"""First look at raw (uncleaned) SLEAP predictions, before choosing any cleaning thresholds.
Four panels: keypoint confidence, frame-to-frame jumps, body length, distance between the two animals.

Run from the repository root with the SLEAP tool python, $PY (it has sleap_io; see ../README.md):
  $PY 02_pose_sleap/scripts/raw_data_plots.py PRED.slp OUT.png
"""
import sys
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import sleap_io as sio

COLORS = {"male": "tab:blue", "female": "tab:orange"}


def to_arrays(labels):
    """(frames, animals, nodes, 2) positions and (frames, animals, nodes) scores, animals ordered by track."""
    tracks = [t.name for t in labels.tracks]
    nn = len(labels.skeleton.nodes)
    lfs = sorted(labels.labeled_frames, key=lambda f: f.frame_idx)
    pos = np.full((len(lfs), len(tracks), nn, 2), np.nan)
    sc = np.full((len(lfs), len(tracks), nn), np.nan)
    for i, lf in enumerate(lfs):
        for inst in lf.instances:
            k = tracks.index(inst.track.name)
            a = inst.numpy(scores=True)
            pos[i, k], sc[i, k] = a[:, :2], a[:, 2]
    return np.array([f.frame_idx for f in lfs]), tracks, pos, sc


def main():
    labels = sio.load_slp(sys.argv[1])
    names = [n.name for n in labels.skeleton.nodes]
    fr, tracks, pos, sc = to_arrays(labels)
    t = fr / 25.0
    nose, tail = names.index("nose"), names.index("tail_base")

    fig, ax = plt.subplots(2, 2, figsize=(14, 8))

    # 1. confidence per keypoint
    a = ax[0, 0]
    data = [sc[:, :, j].ravel() for j in range(len(names))]
    a.boxplot(data, orientation="horizontal", tick_labels=names, showfliers=True, flierprops=dict(ms=2))
    a.axvline(0.3, color="red", ls="--", lw=1)
    a.set_xlabel("confidence score (0-1)"); a.set_title("1) How sure is the model about each point?")

    # 2. frame-to-frame jump of each keypoint (pixels)
    a = ax[0, 1]
    jump = np.linalg.norm(np.diff(pos, axis=0), axis=-1)          # (frames-1, animals, nodes)
    for k, tr in enumerate(tracks):
        a.plot(t[1:], np.nanmax(jump[:, k], axis=1), color=COLORS.get(tr), lw=1, label=tr)
    a.axhline(50, color="red", ls="--", lw=1)
    a.set_xlabel("time (s)"); a.set_ylabel("largest point jump (px)")
    a.set_title("2) Biggest movement of any point between two frames"); a.legend()

    # 3. body length nose - tail_base
    a = ax[1, 0]
    blen = np.linalg.norm(pos[:, :, nose] - pos[:, :, tail], axis=-1)
    for k, tr in enumerate(tracks):
        a.plot(t, blen[:, k], color=COLORS.get(tr), lw=1, label=tr)
    a.set_xlabel("time (s)"); a.set_ylabel("nose - tail base (px)")
    a.set_title("3) Body length: should stay roughly constant"); a.legend()

    # 4. distance between the two animals (body centres)
    a = ax[1, 1]
    cen = np.nanmean(pos, axis=2)
    dist = np.linalg.norm(cen[:, 0] - cen[:, 1], axis=-1)
    a.plot(t, dist, color="k", lw=1)
    a.set_xlabel("time (s)"); a.set_ylabel("distance (px)")
    a.set_title("4) Distance between male and female")

    fig.suptitle("Raw SLEAP output, frames %d-%d (%d frames, %.0f s)" % (fr[0], fr[-1], len(fr), len(fr) / 25))
    fig.tight_layout(); fig.savefig(sys.argv[2], dpi=100)

    print("score  median %.2f, below 0.3: %.1f%% of points" % (np.nanmedian(sc), 100 * np.nanmean(sc < 0.3)))
    print("jumps  >50 px: %d point-frames, max %.0f px" % (np.sum(jump > 50), np.nanmax(jump)))
    for k, tr in enumerate(tracks):
        print("%-6s body length median %.0f px, range %.0f-%.0f" % (tr, np.nanmedian(blen[:, k]),
                                                                    np.nanmin(blen[:, k]), np.nanmax(blen[:, k])))
    print("distance between animals: min %.0f, median %.0f px" % (np.nanmin(dist), np.nanmedian(dist)))


if __name__ == "__main__":
    main()
