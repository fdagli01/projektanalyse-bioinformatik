"""Step 1 (Notebook 01, sections 3-4): look at the tracking, clean it, joint angles, PCA.
Saves figures to figures/working/ so they can be viewed one by one, and the PCA modes to intermediate/."""
import os
import numpy as np
import pandas as pd
import cv2
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from scipy.ndimage import median_filter
from sklearn.decomposition import PCA

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))   # 01_method_fly/
ROOT = os.path.dirname(HERE)                                         # repository root
DATA = os.path.join(ROOT, "unsupervised-behavior-tutorials", "motionmapperpy", "data", "fly")
OUT = os.path.join(HERE, "figures", "working")
CACHE = os.path.join(HERE, "intermediate")   # regenerated .npz/.npy and the Fly_mmpy project (not in git)
os.makedirs(OUT, exist_ok=True)
os.makedirs(CACHE, exist_ok=True)

# ---- 3. look at the data first
datasetnames = ["fly_leap_test", "fly_leap_test_2"]
moviepaths = [os.path.join(DATA, "%s.mp4" % d) for d in datasetnames]
h5s_pandas = [pd.read_hdf(os.path.join(DATA, "%s_positions.h5" % d)) for d in datasetnames]
print("table shape:", h5s_pandas[0].shape)
print("first columns:", list(h5s_pandas[0].columns[:6]))

keep = np.mod(np.arange(1, h5s_pandas[0].shape[1] + 1), 3) != 0     # drop likelihood columns
h5s = [h.values[:, keep].reshape((-1, 32, 2)) for h in h5s_pandas]
for d, h in zip(datasetnames, h5s):
    print("%s: %d frames, %d body parts" % (d, h.shape[0], h.shape[1]))

fps = 100
seg = slice(1400, 1800)
raw = h5s[0][seg, 13, 1].copy()
h5s = [median_filter(h, size=(5, 1, 1)) for h in h5s]
clean = h5s[0][seg, 13, 1]
t = np.arange(seg.stop - seg.start) / fps
fig, ax = plt.subplots(figsize=(13, 3))
ax.plot(t, raw, color="0.7", lw=2, label="raw")
ax.plot(t, clean, color="firebrick", lw=1, label="median filter")
ax.set_xlabel("time (s)"); ax.set_ylabel("y position (px)"); ax.legend()
ax.set_title("Vertical position of one leg tip: tracking errors (jumps) and the cleaned version")
fig.tight_layout(); fig.savefig(os.path.join(OUT, "01_median_filter.png"), dpi=110); plt.close(fig)

# skeleton on three video frames
connections = [np.arange(6, 10), np.arange(10, 14), np.arange(14, 18), np.arange(18, 22),
               np.arange(22, 26), np.arange(26, 30), [2, 0, 1], [0, 3, 4, 5], [31, 3, 30]]
cap = cv2.VideoCapture(moviepaths[0])
fig, axes = plt.subplots(1, 3, figsize=(13, 4.6))
for ax, fr in zip(axes, [7000, 7040, 7080]):
    cap.set(cv2.CAP_PROP_POS_FRAMES, fr); ok, img = cap.read()
    ax.imshow(cv2.cvtColor(img, cv2.COLOR_BGR2RGB), origin="lower")
    for c in connections:
        ax.plot(h5s[0][fr, c, 0], h5s[0][fr, c, 1], "-", color="firebrick", lw=1)
    ax.plot(h5s[0][fr, :, 0], h5s[0][fr, :, 1], ".", color="yellow", ms=3)
    ax.set_title("frame %d (t = %.1f s)" % (fr, fr / fps)); ax.axis("off")
cap.release()
fig.suptitle("32 tracked keypoints (skeleton) drawn on the video")
fig.tight_layout(); fig.savefig(os.path.join(OUT, "02_skeleton.png"), dpi=110); plt.close(fig)

# ---- 4. representation: joint angles
angleinds = [[1,0,2,0],[0,3,4,0],[3,4,5,0],[31,3,30,1],[6,7,8,0],[7,8,9,0],[10,11,12,0],
             [11,12,13,0],[14,15,16,0],[15,16,17,0],[26,27,28,0],[27,28,29,0],[22,23,24,0],
             [23,24,25,0],[18,19,20,0],[19,20,21,0],[3,4,18,0],[3,4,22,0],[3,4,26,0],[3,4,6,0],
             [3,4,10,0],[3,4,14,0]]

def angle_between(v1, v2, small=1):
    a = np.arctan2(v1[:, 1], v1[:, 0]) - np.arctan2(v2[:, 1], v2[:, 0])
    out = np.rad2deg(a % (2 * np.pi))
    if small:
        out[out > 180] -= 360
    return out

angleh5s = []
for h in h5s:
    A = np.zeros((h.shape[0], len(angleinds)))
    for i, (a, b, c, fl) in enumerate(angleinds):
        A[:, i] = angle_between(h[:, a] - h[:, b], h[:, c] - h[:, b], fl)
    angleh5s.append(A)
print("each frame: %d angles instead of %d x,y numbers" % (angleh5s[0].shape[1], h5s[0].shape[1] * 2))

lo = np.min([A.min(0) for A in angleh5s], 0)
angleh5s = [A - lo for A in angleh5s]
hi = np.max([A.max(0) for A in angleh5s], 0)
angleh5s = [A / hi for A in angleh5s]

t = np.arange(1000) / fps
fig, ax = plt.subplots(figsize=(13, 3.5))
ax.plot(t, angleh5s[0][1000:2000, [3, 9, 13]])
ax.set_xlabel("time (s)"); ax.set_ylabel("normalized angle (0-1)")
ax.legend(["wing tip angle", "hind leg tibia angle", "middle leg femur-tibia angle"], loc="upper right")
ax.set_title("Egocentric pose: 3 joint angles over time")
fig.tight_layout(); fig.savefig(os.path.join(OUT, "03_joint_angles.png"), dpi=110); plt.close(fig)

# ---- PCA
X = np.concatenate(angleh5s, axis=0)
p = PCA().fit(X)
n_pca = int(np.argmax(np.cumsum(p.explained_variance_ratio_) > 0.95)) + 1
print("PCA: keep %d modes for 95%% variance; first 5 modes explain: %s"
      % (n_pca, np.round(p.explained_variance_ratio_[:5], 3)))

fig, ax = plt.subplots(1, 2, figsize=(14, 3.8))
ax[0].plot(np.arange(1, X.shape[1] + 1), np.cumsum(p.explained_variance_ratio_), "firebrick", marker=".")
ax[0].axvline(n_pca, ls="--", color="royalblue"); ax[0].axhline(0.95, ls=":", color="grey")
ax[0].set_xlabel("number of PCA components"); ax[0].set_ylabel("cumulative explained variance")
ax[0].set_title("%d components carry 95%% of the variance" % n_pca)
show, width = 4, 0.2
for i in range(show):
    ax[1].bar(np.arange(X.shape[1]) + i * width, p.components_[i], width=width, label="PC%d" % (i + 1))
ax[1].set_xlabel("22 joint angles"); ax[1].set_ylabel("contribution to PC"); ax[1].legend(ncol=4)
ax[1].set_title("Which angles make up the first 4 components?")
fig.tight_layout(); fig.savefig(os.path.join(OUT, "04_pca.png"), dpi=110); plt.close(fig)

y = p.transform(X)[:, :n_pca]
projs_list = np.split(y, np.cumsum([A.shape[0] for A in angleh5s])[:-1])
np.savez(os.path.join(CACHE, "pca.npz"), proj0=projs_list[0], proj1=projs_list[1], n_pca=n_pca, fps=fps)
print("saved:", sorted(os.listdir(OUT)), sorted(os.listdir(CACHE)))
