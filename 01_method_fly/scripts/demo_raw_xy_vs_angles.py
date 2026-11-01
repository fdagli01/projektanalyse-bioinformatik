"""Demo: why raw x,y is a poor description: take ONE real fly frame, move + rotate the whole fly (same pose),
and compare the raw coordinates with the joint angles."""
import os
import numpy as np, pandas as pd
import matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))   # 01_method_fly/
ROOT = os.path.dirname(HERE)                                         # repository root
OUT = os.path.join(HERE, "figures", "working")
h = pd.read_hdf(os.path.join(ROOT, "unsupervised-behavior-tutorials", "motionmapperpy", "data", "fly", "fly_leap_test_positions.h5"))
keep = np.mod(np.arange(1, h.shape[1] + 1), 3) != 0
P = h.values[:, keep].reshape((-1, 32, 2))[7000]            # one frame: (32 points, 2)

def move(P, shift, deg):
    a = np.deg2rad(deg); R = np.array([[np.cos(a), -np.sin(a)], [np.sin(a), np.cos(a)]])
    c = P.mean(0)
    return (P - c) @ R.T + c + shift

def angle(P, a, b, c):                                       # angle at point b between b->a and b->c
    v1, v2 = P[a] - P[b], P[c] - P[b]
    return np.degrees(np.arctan2(v1[1], v1[0]) - np.arctan2(v2[1], v2[0]))

Q = move(P, shift=np.array([60.0, -40.0]), deg=70)          # same fly, moved and turned
triples = [(6, 7, 8), (10, 11, 12), (22, 23, 24), (1, 0, 2)]  # a few leg / head angles used in the notebook
raw_diff = np.linalg.norm(P - Q, axis=1).mean()
print("mean distance between the same 32 points, raw x,y: %.1f px" % raw_diff)
for t in triples:
    print("angle %s: original %.1f deg, moved+turned %.1f deg" % (t, angle(P, *t) % 360, angle(Q, *t) % 360))

conn = [np.arange(6, 10), np.arange(10, 14), np.arange(14, 18), np.arange(18, 22),
        np.arange(22, 26), np.arange(26, 30), [2, 0, 1], [0, 3, 4, 5], [31, 3, 30]]
fig, ax = plt.subplots(1, 2, figsize=(11, 5))
for X, col, lab in [(P, "firebrick", "original"), (Q, "royalblue", "same fly: shifted + turned by 70°")]:
    for c in conn:
        ax[0].plot(X[c, 0], X[c, 1], "-", color=col, lw=1.5)
    ax[0].plot([], [], color=col, label=lab)
ax[0].set_aspect("equal"); ax[0].legend(fontsize=8, loc="lower center"); ax[0].set_title("Same pose, different place and direction\n(raw x,y numbers: %.0f px different)" % raw_diff)
w = 0.35; x = np.arange(len(triples))
a0 = [angle(P, *t) % 360 for t in triples]; a1 = [angle(Q, *t) % 360 for t in triples]
ax[1].bar(x - w / 2, a0, w, color="firebrick", label="original"); ax[1].bar(x + w / 2, a1, w, color="royalblue", label="shifted + turned")
ax[1].set_xticks(x); ax[1].set_xticklabels(["leg 1\nupper joint", "leg 2\nupper joint", "leg 3\nupper joint", "head\n(eye-head-eye)"], fontsize=8)
ax[1].set_ylabel("angle (degrees)"); ax[1].legend(fontsize=8); ax[1].set_title("Joint angles: unchanged")
fig.tight_layout(); fig.savefig(os.path.join(OUT, "16_raw_vs_angles.png"), dpi=110); plt.close(fig)
