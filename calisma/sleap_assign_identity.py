"""Give SLEAP predictions meaningful identities: 'male' / 'female' instead of track_0 / track_1.

Identity comes from fur colour, as stated in the sciebo Readme: the darker animal in the video is the
black one. In the folder names used so far the black animal is the male (e.g. m706black_f779agouti), but
a few folders are the other way round (e.g. m1600agouti_f1553black), so the colour of the male is a parameter.

Per frame:
  1. If SLEAP found more than 2 animals (an animal counted twice, or a shadow), keep the 2 most reliable:
     the one with the highest score, then the best one that is not a copy of it (body centres at least
     MIN_SEPARATION px apart). The others are removed from the frame.
  2. Mean grey level around each animal's back keypoints; the darker one gets the 'black' identity.
  3. Frames with only 1 animal get no identity (track left empty), because there is nothing to compare.
This ignores SLEAP's own track numbers, so it also repairs track swaps made by the tracker.

Run with the SLEAP tool python (it has sleap_io and opencv):
  ~/.local/share/uv/tools/sleap/bin/python calisma/sleap_assign_identity.py IN.slp VIDEO.avi OUT.slp --male black
"""
import argparse
import numpy as np
import cv2
import sleap_io as sio

BACK_PARTS = ["neck", "spine1", "spine2", "spine3"]
RADIUS = 10
MIN_SEPARATION = 40    # px; two detections whose body centres are closer than this are the same animal


def darkness(img, inst, back_idx):
    pts = inst.numpy()[back_idx, :2]
    vals = []
    for x, y in pts:
        if np.isnan(x) or np.isnan(y):
            continue
        x, y = int(round(x)), int(round(y))
        patch = img[max(y - RADIUS, 0):y + RADIUS + 1, max(x - RADIUS, 0):x + RADIUS + 1]
        if patch.size:
            vals.append(patch.mean())
    return np.mean(vals) if vals else np.nan


def reliability(inst):
    """Instance score from SLEAP; if missing, the mean of its keypoint scores."""
    s = getattr(inst, "score", None)
    if s is not None and np.isfinite(s):
        return float(s)
    return float(np.nanmean(inst.numpy(scores=True)[:, 2]))


def centre(inst):
    return np.nanmean(inst.numpy()[:, :2], axis=0)


def best_two(instances):
    """Highest-scoring animal, then the best one that is not a duplicate of it. May return 1 if all are copies."""
    ranked = sorted(instances, key=reliability, reverse=True)
    first = ranked[0]
    for other in ranked[1:]:
        if np.linalg.norm(centre(other) - centre(first)) >= MIN_SEPARATION:
            return [first, other]
    return [first]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("pred"); ap.add_argument("video"); ap.add_argument("out")
    ap.add_argument("--male", choices=["black", "agouti"], default="black")
    a = ap.parse_args()

    labels = sio.load_slp(a.pred)
    names = [n.name for n in labels.skeleton.nodes]
    back_idx = [names.index(p) for p in BACK_PARTS]
    male, female = sio.Track("male"), sio.Track("female")
    black_track, agouti_track = (male, female) if a.male == "black" else (female, male)
    cap = cv2.VideoCapture(a.video)

    margins = []
    counts = {"reduced to 2": 0, "only 1 animal": 0, "unreadable": 0}
    next_frame = None                                  # read the video in order instead of seeking every frame
    for lf in sorted(labels.labeled_frames, key=lambda f: f.frame_idx):
        for inst in lf.instances:
            inst.track = None                          # drop SLEAP's track numbers (e.g. track_0 ... track_261)

        if len(lf.instances) > 2:
            lf.instances = best_two(lf.instances)
            counts["reduced to 2"] += 1
        if len(lf.instances) < 2:
            counts["only 1 animal"] += 1
            continue

        if lf.frame_idx != next_frame:
            cap.set(cv2.CAP_PROP_POS_FRAMES, lf.frame_idx)
        ok, img = cap.read()
        next_frame = lf.frame_idx + 1
        if not ok:
            counts["unreadable"] += 1
            continue
        g = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY) if img.ndim == 3 else img
        d = [darkness(g, i, back_idx) for i in lf.instances]
        if np.isnan(d).any():
            counts["unreadable"] += 1
            continue
        dark, light = (0, 1) if d[0] < d[1] else (1, 0)
        lf.instances[dark].track = black_track
        lf.instances[light].track = agouti_track
        margins.append(abs(d[0] - d[1]))

    labels.tracks = [male, female]
    labels.save(a.out)
    m = np.array(margins)
    print("frames with male/female assigned: %d" % len(m))
    print("frames with 3-4 animals reduced to 2: %d" % counts["reduced to 2"])
    print("frames left without identity: only 1 animal %d, unreadable %d"
          % (counts["only 1 animal"], counts["unreadable"]))
    print("grey-level gap between animals: median %.1f, 10th percentile %.1f (small gap = unreliable)"
          % (np.median(m), np.percentile(m, 10)))


if __name__ == "__main__":
    main()
