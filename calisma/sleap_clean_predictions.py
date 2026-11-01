"""Automatic quality control and cleaning of SLEAP predictions (replaces watching every frame by hand).

Per point the script marks as bad:
  - missing            (no prediction)
  - low confidence     (score < SCORE_MIN)
  - spike              (point is far from its own smoothed trajectory: it jumps away and comes back)
Per animal and frame:
  - broken skeleton    (nose - tail base length far from that animal's usual length)
Then it removes bad points, fills short gaps by interpolation, smooths, and lists what is still doubtful.

Outputs (OUT is a prefix):
  OUT_clean.npz   raw and cleaned positions, scores, frame numbers, node and track names (MotionMapper input)
  OUT_flags.csv   time segments to look at, with the reason
  OUT_report.txt  short summary numbers
  OUT_qc.png      one figure: what was removed and filled

Run with the SLEAP tool python (it has sleap_io):
  ~/.local/share/uv/tools/sleap/bin/python calisma/sleap_clean_predictions.py PRED.slp OUT
"""
import os
import sys
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from scipy.ndimage import median_filter
import sleap_io as sio

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from sleap_raw_data_plots import to_arrays

FPS = 25
SCORE_MIN = 0.3        # below this the model is guessing
SPIKE_PX = 40          # distance from the smoothed trajectory that counts as a spike
SPIKE_WIN = 7          # frames used for the smoothed trajectory (0.28 s)
BODY_RANGE = (0.5, 1.5)  # allowed nose - tail base length relative to the animal's median
MAX_GAP = 5            # longest gap (frames) that is filled by interpolation (0.2 s)
SMOOTH = 5             # median filter after filling (frames)
BAD_NODES = 4          # an animal with more bad points than this in a frame is a doubtful frame
CONTACT_PX = 120       # body centres closer than this: animals touch, identity can be mixed up


def nan_median_filter(x, size):
    """Median filter along time that ignores NaN (x: frames)."""
    pad = size // 2
    xp = np.pad(x, pad, mode="edge")
    win = np.lib.stride_tricks.sliding_window_view(xp, size)
    with np.errstate(all="ignore"):
        return np.nanmedian(win, axis=1)


def fill_short_gaps(x, max_gap):
    """Linear interpolation over NaN runs of at most max_gap frames; longer runs stay NaN."""
    x = x.copy()
    bad = np.isnan(x)
    if bad.all() or not bad.any():
        return x
    idx = np.arange(len(x))
    filled = np.interp(idx, idx[~bad], x[~bad])
    start = None
    for i, b in enumerate(np.append(bad, False)):
        if b and start is None:
            start = i
        elif not b and start is not None:
            inside = start > 0 and i < len(x)          # do not extrapolate at the edges
            if inside and i - start <= max_gap:
                x[start:i] = filled[start:i]
            start = None
    return x


def segments(mask):
    """Start/end index pairs of runs where mask is True (end exclusive)."""
    d = np.diff(np.r_[0, mask.astype(int), 0])
    return list(zip(np.where(d == 1)[0], np.where(d == -1)[0]))


def main():
    pred, out = sys.argv[1], sys.argv[2]
    labels = sio.load_slp(pred)
    names = [n.name for n in labels.skeleton.nodes]
    fr, tracks, pos, sc = to_arrays(labels)
    nf, na, nn, _ = pos.shape
    nose, tail = names.index("nose"), names.index("tail_base")

    # --- 1. mark bad points ------------------------------------------------------------------
    missing = np.isnan(pos[..., 0])
    lowconf = sc < SCORE_MIN
    spike = np.zeros_like(missing)
    for a in range(na):
        for j in range(nn):
            sm = np.stack([nan_median_filter(pos[:, a, j, c], SPIKE_WIN) for c in range(2)], -1)
            with np.errstate(invalid="ignore"):
                spike[:, a, j] = np.linalg.norm(pos[:, a, j] - sm, axis=-1) > SPIKE_PX

    blen = np.linalg.norm(pos[:, :, nose] - pos[:, :, tail], axis=-1)
    rel = blen / np.nanmedian(blen, axis=0)
    with np.errstate(invalid="ignore"):
        broken = (rel < BODY_RANGE[0]) | (rel > BODY_RANGE[1])           # (frames, animals)

    bad = missing | lowconf | spike
    bad[broken] = True                                                   # whole skeleton unusable

    # --- 2. remove, fill short gaps, smooth ----------------------------------------------------
    clean = pos.copy()
    clean[bad] = np.nan
    for a in range(na):
        for j in range(nn):
            for c in range(2):
                v = fill_short_gaps(clean[:, a, j, c], MAX_GAP)
                ok = ~np.isnan(v)
                if ok.sum() > SMOOTH:
                    v[ok] = median_filter(v[ok], size=SMOOTH, mode="nearest")
                clean[:, a, j, c] = v
    still_missing = np.isnan(clean[..., 0])

    # --- 3. doubtful frames and contact ---------------------------------------------------------
    nbad = bad.sum(axis=2)                                               # (frames, animals)
    doubtful = (nbad > BAD_NODES).any(1) | broken.any(1) | still_missing.any(axis=(1, 2))
    cen = np.nanmean(clean, axis=2)
    with np.errstate(invalid="ignore"):
        contact = np.linalg.norm(cen[:, 0] - cen[:, 1], axis=-1) < CONTACT_PX

    rows = []
    for s, e in segments(doubtful):
        why = []
        if broken[s:e].any(): why.append("broken skeleton")
        if (nbad[s:e] > BAD_NODES).any(): why.append("many bad points")
        if still_missing[s:e].any(): why.append("gap too long to fill")
        if contact[s:e].any(): why.append("during contact")
        rows.append((fr[s], fr[e - 1], fr[s] / FPS, fr[e - 1] / FPS, "; ".join(why)))
    with open(out + "_flags.csv", "w") as f:
        f.write("start_frame,end_frame,start_s,end_s,reason\n")
        for r in rows:
            f.write("%d,%d,%.2f,%.2f,%s\n" % r)

    np.savez_compressed(out + "_clean.npz", frames=fr, raw=pos, clean=clean, scores=sc,
                        bad=bad, doubtful=doubtful, contact=contact,
                        nodes=np.array(names), tracks=np.array(tracks))

    # --- 4. report -------------------------------------------------------------------------------
    lines = [
        "file: %s" % pred,
        "frames: %d (%.1f s)" % (nf, nf / FPS),
        "points marked bad: %.1f%%  (missing %.1f%%, low confidence %.1f%%, spikes %.1f%%)"
        % (100 * bad.mean(), 100 * missing.mean(), 100 * lowconf.mean(), 100 * spike.mean()),
        "broken skeletons: " + ", ".join("%s %d frames" % (t, broken[:, k].sum()) for k, t in enumerate(tracks)),
        "points still missing after filling: %.1f%%" % (100 * still_missing.mean()),
        "clean frames: %.1f%%   doubtful frames: %d in %d segments" % (100 * (1 - doubtful.mean()), doubtful.sum(), len(rows)),
        "frames with contact (< %d px): %.1f%%" % (CONTACT_PX, 100 * np.nanmean(contact)),
    ]
    open(out + "_report.txt", "w").write("\n".join(lines) + "\n")
    print("\n".join(lines))

    # --- 5. figure: one point of each animal, raw vs clean --------------------------------------
    t = fr / FPS
    fig, ax = plt.subplots(na, 1, figsize=(13, 3.2 * na), sharex=True)
    for k, a in enumerate(np.atleast_1d(ax)):
        for s, e in segments(contact):
            a.axvspan(t[s], t[e - 1], color="0.9", lw=0)
        for s, e in segments(doubtful):
            a.axvspan(t[s], t[e - 1], color="mistyrose", lw=0)
        a.plot(t, pos[:, k, nose, 0], color="0.6", lw=1, label="raw nose x")
        b = bad[:, k, nose]
        a.plot(t[b], pos[b, k, nose, 0], "x", color="red", ms=5, label="removed")
        a.plot(t, clean[:, k, nose, 0], color="tab:blue" if tracks[k] == "male" else "tab:orange",
               lw=1.6, label="clean nose x")
        a.set_ylabel("%s nose x (px)" % tracks[k]); a.legend(loc="upper right", fontsize=8)
    np.atleast_1d(ax)[-1].set_xlabel("time (s)   grey = contact, pink = doubtful")
    fig.suptitle("Automatic cleaning: removed points (x) and the cleaned trajectory")
    fig.tight_layout(); fig.savefig(out + "_qc.png", dpi=100)


if __name__ == "__main__":
    main()
