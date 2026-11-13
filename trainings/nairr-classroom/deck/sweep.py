"""Terminal text and the job schedule shared by build_deck.py and build_html.py.

The kubectl output is laid out the way kubectl prints it (columns padded by 3, at least 6 wide).
Pod names are the job name plus a random 5-character suffix, as Kubernetes makes them.
"""

ACCESS_JOBS = [("train-lr-0.1", "7xkqp"), ("train-lr-0.01", "m4q9d"), ("train-lr-0.001", "c8w3n")]


def kubectl_table(rows):
    widths = [max(max(len(r[i]) for r in rows) + 3, 6) for i in range(len(rows[0]) - 1)]
    return ["".join(c.ljust(w) for c, w in zip(r, widths)) + r[-1] for r in rows]


def apply_lines():
    return ["$ kubectl apply -f sweep/"] + [f"job.batch/{j} created" for j, _ in ACCESS_JOBS]


def get_pods(stage):
    """stage 3: two running, one pending; stage 4: the first finished and the pending one took its GPU."""
    state = {3: [("1/1", "Running"), ("1/1", "Running"), ("0/1", "Pending")],
             4: [("0/1", "Completed"), ("1/1", "Running"), ("1/1", "Running")]}[stage]
    age = "40s" if stage == 3 else "3m10s"
    rows = [["NAME", "READY", "STATUS", "RESTARTS", "AGE"]]
    rows += [[f"{j}-{suffix}", ready, st, "0", age] for (j, suffix), (ready, st) in zip(ACCESS_JOBS, state)]
    return ["$ kubectl get pods"] + kubectl_table(rows)


# "Ways to Run Work": the text, then six jobs from one sweep on four GPUs, in time units (0-10).
RUN_WAYS = [
    ("Interactive: JupyterHub", ["Pick a GPU from the start menu; explore, debug, teach",
                                 "Idle servers stop: 1 hour after you close the browser on NRP's hub, "
                                 "6 hours at most on any hub"]),
    ("Interactive: a pod", ["Start a container with kubectl, then open a shell in it",
                            "Deleted after 6 hours; at most 2 GPUs"]),
    ("Long-running: a Deployment", ["Keeps a service up (a web app, a database) and restarts it if it crashes",
                                    "Removed after 2 weeks unless admins grant an exception; no GPU if it sits "
                                    "mostly idle"]),
]
RUN_JOB = ["Runs your script to the end, then gives the GPU back",
           "Submit many at once; the rest wait in Pending for a free GPU"]
RUN_CAPTION = ("Six jobs on four GPUs: two wait in Pending and take the first GPUs that free up. When the last "
               "one ends, all four GPUs are free again.")
RUN_CMD = "$ kubectl apply -f sweep/        # six training jobs"

# Four start at once; two wait in Pending and take the first GPUs that free up.
SWEEP = [  # (job, gpu, start, end)
    ("lr-0.1", 0, 0.0, 4.5), ("lr-0.03", 1, 0.0, 6.0), ("lr-0.01", 2, 0.0, 3.5), ("lr-0.003", 3, 0.0, 5.5),
    ("lr-0.001", 2, 3.5, 8.0), ("lr-0.0003", 0, 4.5, 8.5)]
SWEEP_T = 10.0
