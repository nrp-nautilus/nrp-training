#!/usr/bin/env python3
"""Analyze jet classifier outputs from the GPU training job."""

import json
import os
from pathlib import Path

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
import numpy as np
from sklearn.metrics import accuracy_score, auc, confusion_matrix, roc_curve


OUTPUT_ROOT = Path(os.environ.get("OUTPUT_DIR", "/training/jet-class"))
RUN_ID = os.environ.get("RUN_ID") or os.environ.get("JOB_COMPLETION_INDEX", "single")
RUN_DIR = OUTPUT_ROOT / f"run-{RUN_ID}"


def load_json(path):
    return json.loads(path.read_text(encoding="utf-8"))


def log_to_mlflow(metadata, accuracy, plot_paths):
    """Best-effort: resume the run jet_class.py created (if any) and attach
    the test accuracy plus plots. A down/misconfigured MLflow server should
    never fail the analysis job itself."""
    run_id = metadata.get("mlflow_run_id")
    tracking_uri = metadata.get("mlflow_tracking_uri")
    if not run_id or not tracking_uri:
        return
    try:
        # Bound how long a dead/unreachable server can stall the job before
        # the except block below takes over.
        os.environ.setdefault("MLFLOW_HTTP_REQUEST_TIMEOUT", "10")
        os.environ.setdefault("MLFLOW_HTTP_REQUEST_MAX_RETRIES", "2")

        import mlflow

        mlflow.set_tracking_uri(tracking_uri)
        with mlflow.start_run(run_id=run_id):
            mlflow.log_metric("test_accuracy", accuracy)
            for path in plot_paths:
                mlflow.log_artifact(str(path))
        print(f"Logged analysis results to MLflow run {run_id}")
    except Exception as exc:  # noqa: BLE001 - any MLflow failure must not break analysis
        print(f"MLflow logging unavailable, continuing without it: {exc}")


def plot_feature_distributions(features, labels, classes, feature_names, output):
    fig, axs = plt.subplots(4, 4, figsize=(24, 24))

    for ix, ax in enumerate(axs.reshape(-1)):
        feat = feature_names[ix]
        values = features[:, ix]
        bins = np.linspace(np.nanmin(values), np.nanmax(values), 20)
        for class_idx, label in enumerate(classes):
            ax.hist(
                values[labels == class_idx],
                bins=bins,
                histtype="step",
                label=label,
                lw=1.5,
            )
        ax.set_xlabel(feat)
        ax.set_ylabel("Jets")
        ax.legend(fontsize=8, loc="best")

    fig.tight_layout()
    fig.savefig(output, dpi=150)
    plt.close(fig)


def plot_model_history(history, output):
    fig, axes = plt.subplots(1, 2, figsize=(12, 4))

    axes[0].plot(history["loss"], label="train")
    axes[0].plot(history["val_loss"], label="validation")
    axes[0].set_title("Loss")
    axes[0].set_xlabel("Epoch")
    axes[0].legend()

    axes[1].plot(history["accuracy"], label="train")
    axes[1].plot(history["val_accuracy"], label="validation")
    axes[1].set_title("Accuracy")
    axes[1].set_xlabel("Epoch")
    axes[1].legend()

    fig.tight_layout()
    fig.savefig(output, dpi=150)
    plt.close(fig)


def plot_confusion_matrix(y_true_onehot, y_pred, classes, output):
    y_true = np.argmax(y_true_onehot, axis=1)
    y_hat = np.argmax(y_pred, axis=1)
    matrix = confusion_matrix(y_true, y_hat, normalize="true")

    fig, ax = plt.subplots(figsize=(7, 6))
    image = ax.imshow(matrix, interpolation="nearest", cmap="Blues", vmin=0, vmax=1)
    fig.colorbar(image, ax=ax, fraction=0.046, pad=0.04)
    ax.set(
        xticks=np.arange(len(classes)),
        yticks=np.arange(len(classes)),
        xticklabels=classes,
        yticklabels=classes,
        ylabel="True label",
        xlabel="Predicted label",
        title="Normalized confusion matrix",
    )
    plt.setp(ax.get_xticklabels(), rotation=45, ha="right", rotation_mode="anchor")

    for row in range(matrix.shape[0]):
        for col in range(matrix.shape[1]):
            color = "white" if matrix[row, col] > 0.5 else "black"
            ax.text(col, row, f"{matrix[row, col]:.2f}", ha="center", va="center", color=color)

    fig.tight_layout()
    fig.savefig(output, dpi=150)
    plt.close(fig)


def plot_roc(y_true_onehot, y_pred, classes, output):
    fig, ax = plt.subplots(figsize=(7, 6))

    for idx, label in enumerate(classes):
        fpr, tpr, _ = roc_curve(y_true_onehot[:, idx], y_pred[:, idx])
        roc_auc = auc(fpr, tpr)
        ax.plot(fpr, tpr, lw=1.8, label=f"{label} (AUC = {roc_auc:.3f})")

    ax.plot([0, 1], [0, 1], "k--", lw=1)
    ax.set(xlabel="False positive rate", ylabel="True positive rate", title="ROC curves")
    ax.legend(loc="lower right", fontsize=8)
    fig.tight_layout()
    fig.savefig(output, dpi=150)
    plt.close(fig)


def main():
    if not RUN_DIR.is_dir():
        raise SystemExit(f"Run output directory not found: {RUN_DIR}")

    metadata = load_json(RUN_DIR / "metadata.json")
    history = load_json(RUN_DIR / "history.json")
    predictions = np.load(RUN_DIR / "predictions.npz")
    y_test = predictions["y_test"]
    y_pred = predictions["y_pred"]
    classes = metadata["classes"]

    accuracy = accuracy_score(np.argmax(y_test, axis=1), np.argmax(y_pred, axis=1))
    print(f"Analyzing run: {RUN_ID}")
    print(f"Accuracy: {accuracy:.4f}")

    feature_data = RUN_DIR / "feature_data.npz"
    plot_paths = []
    if feature_data.is_file():
        path = RUN_DIR / "feature_distributions.png"
        features = np.load(feature_data)
        plot_feature_distributions(
            features["X"],
            features["y"],
            classes,
            metadata["feature_names"],
            path,
        )
        plot_paths.append(path)

    history_plot = RUN_DIR / "training_history.png"
    confusion_plot = RUN_DIR / "confusion_matrix.png"
    roc_plot = RUN_DIR / "roc_curve.png"
    plot_model_history(history, history_plot)
    plot_confusion_matrix(y_test, y_pred, classes, confusion_plot)
    plot_roc(y_test, y_pred, classes, roc_plot)
    plot_paths += [history_plot, confusion_plot, roc_plot]

    log_to_mlflow(metadata, accuracy, plot_paths)

    metrics = {
        "dataset": metadata["dataset"],
        "run_id": RUN_ID,
        "accuracy": float(accuracy),
        "classes": classes,
        "epochs": metadata["epochs"],
        "batch_size": metadata["batch_size"],
        "model_widths": metadata["model_widths"],
        "model_parameters": metadata["model_parameters"],
        "training_seconds": metadata.get("training_seconds"),
        "mlflow_run_id": metadata.get("mlflow_run_id"),
        "outputs": sorted(path.name for path in RUN_DIR.iterdir()),
    }
    (RUN_DIR / "metrics.json").write_text(json.dumps(metrics, indent=2) + "\n", encoding="utf-8")

    print("Analysis complete. Wrote artifacts:")
    for path in sorted(RUN_DIR.iterdir()):
        print(f"  - {path}")


if __name__ == "__main__":
    main()
