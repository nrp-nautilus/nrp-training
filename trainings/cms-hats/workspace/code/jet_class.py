#!/usr/bin/env python3
"""Train a jet classifier as a Kubernetes GPU batch workload.

Source material:
https://jduarte.physics.ucsd.edu/phys139_239/03_Tabular_Data_NN.html
Credit: Javier Duarte, UCSD, 2023.
"""

import json
import os
import random
import time
from contextlib import contextmanager
from pathlib import Path

import numpy as np
import tensorflow as tf
from sklearn.datasets import fetch_openml
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder, StandardScaler
from tensorflow.keras import mixed_precision
from tensorflow.keras.layers import Dense, Input
from tensorflow.keras.models import Sequential
from tensorflow.keras.optimizers import Adam
from tensorflow.keras.utils import to_categorical


DATASET = os.environ.get("DATASET", "hls4ml_lhc_jets_hlf")
OUTPUT_ROOT = Path(os.environ.get("OUTPUT_DIR", "/training/jet-class"))
RUN_ID = os.environ.get("RUN_ID") or os.environ.get("JOB_COMPLETION_INDEX", "single")
RUN_DIR = OUTPUT_ROOT / f"run-{RUN_ID}"
OPENML_CACHE_DIR = Path(os.environ.get("OPENML_CACHE_DIR", "/tmp/openml"))

SEED = int(os.environ.get("SEED", "42")) + (int(RUN_ID) if RUN_ID.isdigit() else 0)
EPOCHS = int(os.environ.get("EPOCHS", "50"))
BATCH_SIZE = int(os.environ.get("BATCH_SIZE", "8192"))
LEARNING_RATE = float(os.environ.get("LEARNING_RATE", "0.001"))
MODEL_WIDTHS = tuple(
    int(part.strip())
    for part in os.environ.get("MODEL_WIDTHS", "4096,4096,2048,1024").split(",")
    if part.strip()
)
MIXED_PRECISION = os.environ.get("MIXED_PRECISION", "1").lower() not in ("0", "false", "no")
TEST_FRACTION = float(os.environ.get("TEST_FRACTION", "0.2"))
VALIDATION_FRACTION = float(os.environ.get("VALIDATION_FRACTION", "0.25"))
SAVE_FEATURE_DATA = os.environ.get("SAVE_FEATURE_DATA", "1").lower() not in ("0", "false", "no")

MLFLOW_TRACKING_URI = os.environ.get("MLFLOW_TRACKING_URI", "")
MLFLOW_EXPERIMENT_NAME = os.environ.get("MLFLOW_EXPERIMENT_NAME", "jet-classifier")


def set_reproducible_seed(seed):
    random.seed(seed)
    np.random.seed(seed)
    tf.random.set_seed(seed)


def configure_tensorflow():
    gpus = tf.config.list_physical_devices("GPU")
    for gpu in gpus:
        try:
            tf.config.experimental.set_memory_growth(gpu, True)
        except RuntimeError:
            pass
    if MIXED_PRECISION:
        mixed_precision.set_global_policy("mixed_float16")
    return [gpu.name for gpu in gpus]


def build_model(input_dim, output_dim):
    model = Sequential(name="jet_classifier_gpu_heavy")
    model.add(Input(shape=(input_dim,), name="features"))
    for idx, width in enumerate(MODEL_WIDTHS, start=1):
        model.add(Dense(width, activation="relu", name=f"dense_{idx}"))
    model.add(Dense(output_dim, activation="softmax", dtype="float32", name="class_probabilities"))
    model.compile(
        optimizer=Adam(learning_rate=LEARNING_RATE),
        loss="categorical_crossentropy",
        metrics=["accuracy"],
    )
    return model


def make_dataset(features, labels, *, shuffle):
    dataset = tf.data.Dataset.from_tensor_slices((features, labels))
    if shuffle:
        dataset = dataset.shuffle(
            buffer_size=min(len(features), 100_000),
            seed=SEED,
            reshuffle_each_iteration=True,
        )
        dataset = dataset.batch(BATCH_SIZE, drop_remainder=True)
    else:
        dataset = dataset.batch(BATCH_SIZE)
    return dataset.prefetch(tf.data.AUTOTUNE)


def serializable_history(history):
    return {
        name: [float(value) for value in values]
        for name, values in history.history.items()
    }


@contextmanager
def optional_mlflow_run():
    """Best-effort MLflow run: yields the active run, or None if tracking is
    unset or unreachable. A down/misconfigured MLflow server should never
    fail the training job itself."""
    if not MLFLOW_TRACKING_URI:
        yield None
        return
    try:
        # Bound how long a dead/unreachable server can stall the job before
        # the except block below takes over.
        os.environ.setdefault("MLFLOW_HTTP_REQUEST_TIMEOUT", "10")
        os.environ.setdefault("MLFLOW_HTTP_REQUEST_MAX_RETRIES", "2")

        import mlflow

        mlflow.set_tracking_uri(MLFLOW_TRACKING_URI)
        mlflow.set_experiment(MLFLOW_EXPERIMENT_NAME)
        # Deliberately not using mlflow.tensorflow.autolog(): MLflow flags
        # this image's TensorFlow (2.16.1) as below its tested-compatible
        # range (2.17.1+), and in practice autolog silently captures zero
        # metrics on it. Logging metrics manually below has no such
        # dependency on TF/MLflow internals lining up.
        with mlflow.start_run(run_name=f"run-{RUN_ID}") as run:
            mlflow.log_params(
                {
                    "run_id": RUN_ID,
                    "seed": SEED,
                    "epochs": EPOCHS,
                    "batch_size": BATCH_SIZE,
                    "learning_rate": LEARNING_RATE,
                    "model_widths": ",".join(str(w) for w in MODEL_WIDTHS),
                    "mixed_precision": MIXED_PRECISION,
                }
            )
            yield run
    except Exception as exc:  # noqa: BLE001 - any MLflow failure must not break training
        print(f"MLflow logging unavailable, continuing without it: {exc}")
        yield None


def main():
    set_reproducible_seed(SEED)
    RUN_DIR.mkdir(parents=True, exist_ok=True)
    OPENML_CACHE_DIR.mkdir(parents=True, exist_ok=True)

    gpus = configure_tensorflow()
    print(f"TensorFlow version: {tf.__version__}")
    print(f"TensorFlow mixed precision: {mixed_precision.global_policy().name}")
    print(f"GPUs visible to TensorFlow: {gpus or 'none'}")
    print(f"Run ID: {RUN_ID}")
    print(f"Output directory: {RUN_DIR}")
    print(f"Loading OpenML dataset: {DATASET}")

    data = fetch_openml(DATASET, parser="auto", cache=True, data_home=str(OPENML_CACHE_DIR))
    X_df = data["data"]
    y = data["target"]
    feature_names = list(data["feature_names"])
    classes = list(y.dtype.categories) if hasattr(y.dtype, "categories") else sorted(set(y))

    print(f"Feature names: {feature_names}")
    print(f"Target classes: {classes}")
    print(f"Shapes: X={X_df.shape}, y={y.shape}")
    print("Input preview:")
    print(X_df.head())
    print("Target preview:")
    print(y.head())

    X_np = X_df.to_numpy(dtype=np.float32, copy=True)
    encoder = LabelEncoder()
    y_encoded = encoder.fit_transform(y).astype(np.int16)
    y_onehot = to_categorical(y_encoded, num_classes=len(encoder.classes_)).astype(np.float32)

    if SAVE_FEATURE_DATA:
        np.savez(
            RUN_DIR / "feature_data.npz",
            X=X_np,
            y=y_encoded,
        )

    X_train_val, X_test, y_train_val, y_test, labels_train_val, labels_test = train_test_split(
        X_np,
        y_onehot,
        y_encoded,
        test_size=TEST_FRACTION,
        random_state=SEED,
        stratify=y_encoded,
    )
    X_train, X_val, y_train, y_val = train_test_split(
        X_train_val,
        y_train_val,
        test_size=VALIDATION_FRACTION,
        random_state=SEED,
        stratify=labels_train_val,
    )

    scaler = StandardScaler()
    X_train = scaler.fit_transform(X_train).astype(np.float32)
    X_val = scaler.transform(X_val).astype(np.float32)
    X_test = scaler.transform(X_test).astype(np.float32)

    train_ds = make_dataset(X_train, y_train, shuffle=True)
    val_ds = make_dataset(X_val, y_val, shuffle=False)
    test_ds = make_dataset(X_test, y_test, shuffle=False)

    print("Prepared arrays:")
    print(f"  X_train={X_train.shape}, y_train={y_train.shape}")
    print(f"  X_val={X_val.shape}, y_val={y_val.shape}")
    print(f"  X_test={X_test.shape}, y_test={y_test.shape}")
    print(f"Batch size: {BATCH_SIZE}")
    print(f"Model widths: {MODEL_WIDTHS}")

    model = build_model(X_train.shape[1], y_onehot.shape[1])
    model.summary()

    mlflow_run_id = None
    with optional_mlflow_run() as run:
        if run is not None:
            mlflow_run_id = run.info.run_id
            print(f"MLflow run: {MLFLOW_EXPERIMENT_NAME}/{mlflow_run_id} ({MLFLOW_TRACKING_URI})")

        train_start = time.time()
        history = model.fit(
            train_ds,
            epochs=EPOCHS,
            validation_data=val_ds,
            verbose=2,
        )
        training_seconds = time.time() - train_start

        if run is not None:
            try:
                import mlflow

                num_epochs_recorded = len(next(iter(history.history.values())))
                for epoch_idx in range(num_epochs_recorded):
                    mlflow.log_metrics(
                        {name: float(values[epoch_idx]) for name, values in history.history.items()},
                        step=epoch_idx,
                    )
            except Exception as exc:  # noqa: BLE001 - must not break training
                print(f"MLflow metric logging failed, continuing: {exc}")

    y_pred = model.predict(test_ds, verbose=0)
    model_path = RUN_DIR / "jet_classifier.keras"
    model.save(model_path)

    np.savez(
        RUN_DIR / "predictions.npz",
        y_test=y_test.astype(np.float32),
        y_pred=y_pred.astype(np.float32),
    )
    (RUN_DIR / "history.json").write_text(
        json.dumps(serializable_history(history), indent=2) + "\n",
        encoding="utf-8",
    )

    metadata = {
        "dataset": DATASET,
        "run_id": RUN_ID,
        "seed": SEED,
        "feature_names": feature_names,
        "classes": encoder.classes_.tolist(),
        "input_shape": list(X_np.shape),
        "train_shape": list(X_train.shape),
        "validation_shape": list(X_val.shape),
        "test_shape": list(X_test.shape),
        "epochs": EPOCHS,
        "batch_size": BATCH_SIZE,
        "learning_rate": LEARNING_RATE,
        "model_widths": list(MODEL_WIDTHS),
        "model_parameters": int(model.count_params()),
        "training_seconds": round(training_seconds, 1),
        "mixed_precision": mixed_precision.global_policy().name,
        "tensorflow_version": tf.__version__,
        "gpus": gpus,
        "mlflow_tracking_uri": MLFLOW_TRACKING_URI or None,
        "mlflow_experiment": MLFLOW_EXPERIMENT_NAME if mlflow_run_id else None,
        "mlflow_run_id": mlflow_run_id,
        "outputs": sorted(path.name for path in RUN_DIR.iterdir()),
    }
    (RUN_DIR / "metadata.json").write_text(json.dumps(metadata, indent=2) + "\n", encoding="utf-8")

    print("Training complete. Wrote artifacts:")
    for path in sorted(RUN_DIR.iterdir()):
        print(f"  - {path}")


if __name__ == "__main__":
    main()
