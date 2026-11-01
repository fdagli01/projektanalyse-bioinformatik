"""Draw the SLEAP skeleton of every labelled frame onto the video and save it as an .mp4.
Animals are coloured and named by track (male = blue, female = orange).

Run from the repository root with the SLEAP tool python, $PY (it has sleap_io and opencv; see ../README.md):
  $PY 02_pose_sleap/scripts/draw_skeleton_video.py PRED.slp VIDEO.avi OUT.mp4 [--scale 0.5]
"""
import argparse
import numpy as np
import cv2
import sleap_io as sio

COLORS = {"male": (255, 140, 30), "female": (40, 140, 255)}   # BGR
OTHER = [(0, 200, 0), (0, 0, 230)]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("pred"); ap.add_argument("video"); ap.add_argument("out")
    ap.add_argument("--scale", type=float, default=0.5, help="output size relative to the video")
    a = ap.parse_args()

    labels = sio.load_slp(a.pred)
    edges = labels.skeleton.edge_inds
    frames = {lf.frame_idx: lf for lf in labels.labeled_frames}
    idxs = sorted(frames)

    cap = cv2.VideoCapture(a.video)
    fps = cap.get(cv2.CAP_PROP_FPS)
    w, h = int(cap.get(3) * a.scale), int(cap.get(4) * a.scale)
    out = cv2.VideoWriter(a.out, cv2.VideoWriter_fourcc(*"mp4v"), fps, (w, h))
    cap.set(cv2.CAP_PROP_POS_FRAMES, idxs[0])

    for n in range(idxs[0], idxs[-1] + 1):
        ok, img = cap.read()
        if not ok:
            break
        img = cv2.resize(img, (w, h))
        if img.ndim == 2:
            img = cv2.cvtColor(img, cv2.COLOR_GRAY2BGR)
        if n in frames:
            for k, inst in enumerate(frames[n].instances):
                name = inst.track.name if inst.track else "?"
                col = COLORS.get(name, OTHER[k % 2])
                p = inst.numpy()[:, :2] * a.scale
                for i, j in edges:
                    if not (np.isnan(p[i]).any() or np.isnan(p[j]).any()):
                        cv2.line(img, tuple(p[i].astype(int)), tuple(p[j].astype(int)), col, 2)
                for x, y in p:
                    if not np.isnan(x):
                        cv2.circle(img, (int(x), int(y)), 3, col, -1)
                ok_pts = p[~np.isnan(p[:, 0])]
                if len(ok_pts):
                    x, y = ok_pts.mean(0).astype(int)
                    cv2.putText(img, name, (x - 30, y - 25), cv2.FONT_HERSHEY_SIMPLEX, 0.7, col, 2)
        cv2.putText(img, "frame %d  (%.1f s)" % (n, n / fps), (10, 25), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
        out.write(img)
    out.release()
    print("saved", a.out, "frames", idxs[0], "-", n)


if __name__ == "__main__":
    main()
