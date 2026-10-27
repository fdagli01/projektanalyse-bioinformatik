---
name: mouse-interaction-project
description: "User's upcoming project with Maria — unsupervised detection of male–female mouse interaction behavior from video (SLEAP + MotionMapper)"
metadata:
  node_type: memory
  type: project
  originSessionId: 651053a8-11f7-42fa-aa8e-c2e0123f2c80
  modified: 2026-10-26T14:17:24.210Z
---

The user (Turkish speaker) is joining a project led by Maria: automatically detect mouse behavior, especially male–female interactions, from video. Approach is **unsupervised**, using SLEAP for pose and the Berman lab notebooks (github.com/bermanlabemory/unsupervised-behavior-tutorials) as the method template. Setup: **2 cameras, side and top**. Open questions for Maria: fps, camera sync/calibration, identity tracking of the two mice, whether videos are already tracked.

Local setup (2026-10-26): repo cloned at `unsupervised-behavior-tutorials/` with motionmapperpy pinned; Python 3.11 env at `.venv311`; step-by-step scripts and figures in `calisma/` (notebook 01 done). Scripts using mmpy wavelets need an `if __name__ == "__main__"` guard on macOS.

See [[stepwise-teaching]].
