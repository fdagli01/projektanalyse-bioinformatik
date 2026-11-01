"""Pick frames from a SLEAP prediction file and draw them for manual review in review_page.html.

Frames are chosen per situation, spread evenly over the video (the first SKIP frames are set-up and left out):
  apart    2 animals, body centres more than APART_PX apart      (easy case)
  contact  2 animals, body centres closer than CONTACT_PX         (hard case)
  single   only 1 animal found                                    (missed animal, or animals on top of each other)
  random   any frame not chosen yet
Each frame is saved twice: the full frame and a zoom on the animals, plus the CONTEXT frames before and after it
(same zoom box) so the movement around it can be played in the page. The two detections are drawn as
A (red) and B (cyan); this is SLEAP's raw output, so A/B are not male/female yet. For every animal the
mean grey level of its back is stored too (the value the identity script uses), lower = darker.
REPEATS frames per stratum are shown a second time, unmarked, to measure consistency.
The questions, blinding and decision rules are in ../PROTOCOL.md.

Run from the work folder with the SLEAP tool python, $PY (it has sleap_io and opencv):
  $PY Notebooks/03_quality_check/scripts/sample_frames.py results/<experiment>/predictions_raw.slp data/videos/videoTop_<experiment>.avi review/<experiment>
The male's fur colour is read from the experiment folder name (m1313black_f1603agouti -> black); --male overrides it.
Then open review/<experiment>/index.html in a browser.
"""
import argparse
import json
import os
import re
import shutil
import sys
from datetime import datetime
import numpy as np
import cv2
import sleap_io as sio

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "02_pose_sleap", "scripts"))
from assign_identity import darkness, BACK_PARTS

FPS = 25
SKIP = 3000                 # first 2 minutes: set-up
CONTACT_PX = 120            # same threshold as clean_predictions.py
APART_PX = 250
CONTEXT = 5                 # frames before and after each sampled frame, to see the movement
REPEATS = 2                 # frames per stratum shown twice, to measure consistency (PROTOCOL.md, section 2)
MIN_GAP = 20                # a repeat comes at least this many items after the first showing
PROTOCOL_VERSION = "1.0"
REGIONS = {"head": ["nose", "ear_left", "ear right", "neck"],
           "body": ["shoulder_left", "shoulder_right", "spine1", "spine2"],
           "rear": ["spine3", "hip_left", "hip_right", "tail_base"]}
COUNTS = {"apart": 30, "contact": 30, "single": 10, "random": 10}
COLORS = [(60, 60, 230), (230, 200, 40)]          # BGR: A red, B cyan
FULL_WIDTH = 960
ZOOM_SIZE = 640
PAGE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "review_page.html")


def spread(candidates, n, rng, taken):
    """n frames spread evenly over the candidates (with a little jitter), skipping frames already taken."""
    c = np.array(sorted(set(candidates) - taken))
    if len(c) <= n:
        return list(c)
    edges = np.linspace(0, len(c), n + 1).astype(int)
    return [int(c[rng.integers(a, b)]) for a, b in zip(edges[:-1], edges[1:])]


def draw(img, instances, edges, nose):
    for k, inst in enumerate(instances):
        col = COLORS[k % len(COLORS)]
        p = inst.numpy()[:, :2]
        for a, b in edges:
            if np.isfinite(p[[a, b]]).all():
                cv2.line(img, tuple(np.round(p[a]).astype(int)), tuple(np.round(p[b]).astype(int)), col, 2, cv2.LINE_AA)
        for j, (x, y) in enumerate(p):
            if np.isfinite(x) and np.isfinite(y):
                cv2.circle(img, (int(round(x)), int(round(y))), 7 if j == nose else 4, col, -1, cv2.LINE_AA)
        c = np.nanmean(p, axis=0)
        if np.isfinite(c).all():
            cv2.putText(img, "AB"[k] if k < 2 else str(k), (int(c[0]) + 12, int(c[1]) - 12),
                        cv2.FONT_HERSHEY_SIMPLEX, 1.1, (0, 0, 0), 5, cv2.LINE_AA)
            cv2.putText(img, "AB"[k] if k < 2 else str(k), (int(c[0]) + 12, int(c[1]) - 12),
                        cv2.FONT_HERSHEY_SIMPLEX, 1.1, col, 2, cv2.LINE_AA)
    return img


def zoom_box(instances, w, h, margin=90):
    """Square crop around the animals; the context frames use the same box, so the view does not move."""
    pts = np.concatenate([i.numpy()[:, :2] for i in instances])
    pts = pts[np.isfinite(pts).all(1)]
    if not len(pts):
        return 0, 0, w, h
    (x0, y0), (x1, y1) = pts.min(0) - margin, pts.max(0) + margin
    side = max(x1 - x0, y1 - y0, 260)
    cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
    x0, y0 = int(max(cx - side / 2, 0)), int(max(cy - side / 2, 0))
    return x0, y0, int(min(x0 + side, w)), int(min(y0 + side, h))


def crop(img, box, size=ZOOM_SIZE):
    x0, y0, x1, y1 = box
    return cv2.resize(img[y0:y1, x0:x1], (size, int(size * (y1 - y0) / max(x1 - x0, 1))))


def with_repeats(order, kind, rng):
    """Review items: every frame once, plus REPEATS frames per stratum shown again at least MIN_GAP items later."""
    items = [{"item": None, "frame": f, "repeat_of": None} for f in order]
    for k in COUNTS:
        firsts = [n for n, f in enumerate(order) if kind[f] == k and n < len(order) - MIN_GAP]
        for n in sorted(rng.choice(firsts, size=min(REPEATS, len(firsts)), replace=False)):
            cur = next(j for j, it in enumerate(items) if it["frame"] == order[n] and it["repeat_of"] is None)
            at = int(rng.integers(cur + MIN_GAP, len(items) + 1))
            items.insert(at, {"item": None, "frame": order[n], "repeat_of": n})
    for n, it in enumerate(items):
        it["item"] = "I%02d" % (n + 1)
    first = {it["frame"]: it["item"] for it in items if it["repeat_of"] is None}
    for it in items:
        if it["repeat_of"] is not None:
            it["repeat_of"] = first[it["frame"]]
    return items


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("pred"); ap.add_argument("video"); ap.add_argument("out")
    ap.add_argument("--male", choices=["black", "agouti"], help="fur colour of the male; default: read from the folder name")
    ap.add_argument("--seed", type=int, default=0)
    a = ap.parse_args()
    experiment = os.path.basename(os.path.dirname(os.path.abspath(a.pred)))
    if a.male is None:
        m = re.search(r"_m\d+(black|agouti)_f\d+(black|agouti)", experiment)
        if not m:
            sys.exit("cannot read the male's fur colour from '%s'; pass --male" % experiment)
        a.male = m.group(1)
    print("experiment %s, male %s" % (experiment, a.male))

    labels = sio.load_slp(a.pred, open_videos=False)
    names = [n.name for n in labels.skeleton.nodes]
    edges, nose = labels.skeleton.edge_inds, names.index("nose")
    back_idx = [names.index(p) for p in BACK_PARTS]
    frames = {lf.frame_idx: lf for lf in labels.labeled_frames if lf.frame_idx >= SKIP}

    def dist(lf):
        c = [np.nanmean(i.numpy()[:, :2], axis=0) for i in lf.instances[:2]]
        return float(np.linalg.norm(c[0] - c[1]))

    two = {f: dist(lf) for f, lf in frames.items() if len(lf.instances) == 2}
    pools = {"apart": [f for f, d in two.items() if d > APART_PX],
             "contact": [f for f, d in two.items() if d < CONTACT_PX],
             "single": [f for f, lf in frames.items() if len(lf.instances) == 1],
             "random": list(frames)}
    rng, taken, kind = np.random.default_rng(a.seed), set(), {}
    for k, n in COUNTS.items():
        for f in spread(pools[k], n, rng, taken):
            taken.add(f); kind[f] = k
    print("frames in the pools:", {k: len(v) for k, v in pools.items()})
    print("frames chosen:", {k: sum(v == k for v in kind.values()) for k in COUNTS})

    os.makedirs(os.path.join(a.out, "img", "context"), exist_ok=True)
    cap = cv2.VideoCapture(a.video)
    w, h = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH)), int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    every = {lf.frame_idx: lf for lf in labels.labeled_frames}       # context frames may have no prediction
    box = {t: zoom_box(frames[t].instances, w, h) for t in kind}
    needed = {}                                                      # video frame -> [(sampled frame, offset)]
    for t in kind:
        for o in range(-CONTEXT, CONTEXT + 1):
            needed.setdefault(t + o, []).append((t, o))

    rows, pos, last = {}, 0, max(needed)
    while pos <= last:                       # read in order: seeking in this codec can land on the wrong frame
        if pos not in needed:
            cap.grab(); pos += 1; continue
        ok, img = cap.read()
        if not ok:
            print("\ncould not read frame", pos); pos += 1; continue
        lf = every.get(pos)
        insts = lf.instances if lf else []
        grey = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        draw(img, insts, edges, nose)
        for t, o in needed[pos]:
            if o == 0:
                full, zm = "img/%06d_full.jpg" % t, "img/%06d_zoom.jpg" % t
                cv2.imwrite(os.path.join(a.out, full), cv2.resize(img, (FULL_WIDTH, int(FULL_WIDTH * h / w))), [cv2.IMWRITE_JPEG_QUALITY, 88])
                cv2.imwrite(os.path.join(a.out, zm), crop(img, box[t]), [cv2.IMWRITE_JPEG_QUALITY, 90])
                g = [darkness(grey, i, back_idx) for i in insts]
                rows[t] = {"frame": int(t), "time": round(t / FPS, 1), "kind": kind[t],
                           "animals": len(insts), "distance": round(two[t]) if t in two else None,
                           "grey": [None if np.isnan(v) else round(float(v), 1) for v in g],
                           "score": [round(float(i.score), 2) for i in insts], "full": full, "zoom": zm,
                           "context": ["img/context/%06d_%+d.jpg" % (t, k) if k else zm for k in range(-CONTEXT, CONTEXT + 1)]}
            else:
                cv2.imwrite(os.path.join(a.out, "img", "context", "%06d_%+d.jpg" % (t, o)), crop(img, box[t]),
                            [cv2.IMWRITE_JPEG_QUALITY, 85])
        pos += 1
        print("\rvideo frame %d / %d" % (pos, last + 1), end="", flush=True)
    print()
    rows = [rows[t] for t in sorted(rows)]
    rng.shuffle(rows)                               # review in mixed order, so the kinds are not judged in blocks
    items = with_repeats([r["frame"] for r in rows], kind, np.random.default_rng(a.seed + 1))

    meta = {"protocol": PROTOCOL_VERSION,
            "experiment": experiment, "male": a.male,
            "prediction": os.path.abspath(a.pred), "video": os.path.abspath(a.video),
            "created": datetime.now().isoformat(timespec="seconds"), "seed": a.seed,
            "sampling": {"skip": SKIP, "apart_px": APART_PX, "contact_px": CONTACT_PX, "counts": COUNTS,
                         "repeats_per_stratum": REPEATS, "context": CONTEXT},
            "pools": {k: len(v) for k, v in pools.items()},
            "software": {"sleap_io": sio.__version__, "opencv": cv2.__version__, "numpy": np.__version__},
            "regions": REGIONS, "frames": {str(r["frame"]): r for r in rows}, "items": items}
    with open(os.path.join(a.out, "frames.js"), "w", encoding="utf-8") as f:
        f.write("window.REVIEW = " + json.dumps(meta, indent=1) + ";\n")
    shutil.copy(PAGE, os.path.join(a.out, "index.html"))
    shutil.copy(os.path.join(os.path.dirname(PAGE), "PROTOCOL.md"), os.path.join(a.out, "PROTOCOL.md"))
    print("items: %d (%d frames + %d repeats)" % (len(items), len(rows), len(items) - len(rows)))
    print("open", os.path.join(os.path.abspath(a.out), "index.html"))


if __name__ == "__main__":
    main()
