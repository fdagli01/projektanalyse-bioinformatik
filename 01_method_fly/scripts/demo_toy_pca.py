"""Demo (Notebook 01, PCA): a tiny made-up example with 2 joint angles, so the idea is visible."""
import os
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from sklearn.decomposition import PCA

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))   # 01_method_fly/
ROOT = os.path.dirname(HERE)                                         # repository root
OUT = os.path.join(HERE, "figures", "working")

# 2 joint angles that mostly move together (leg opening/closing) plus a little independent jitter
rng = np.random.default_rng(3)
t = np.arange(300) / 100
leg = np.sin(2 * np.pi * 1.2 * t) + 0.5 * np.sin(2 * np.pi * 0.4 * t)
A = 0.9 * leg + 0.10 * rng.standard_normal(len(t))          # angle of joint A
B = 0.6 * leg + 0.10 * rng.standard_normal(len(t))          # angle of joint B
X = np.c_[A, B]

p = PCA().fit(X)
Y = p.transform(X)
ratio = p.explained_variance_ratio_
mean = X.mean(0)

fig, ax = plt.subplots(1, 4, figsize=(19, 4.4))

ax[0].plot(t, A, color="royalblue", label="joint A angle")
ax[0].plot(t, B, color="darkorange", label="joint B angle")
ax[0].set_xlabel("time (s)"); ax[0].legend(loc="upper right", fontsize=8)
ax[0].set_title("1) Two angles over time\nthey rise and fall together")

ax[1].scatter(A, B, s=8, c=t, cmap="cool")
ax[1].set_xlabel("joint A"); ax[1].set_ylabel("joint B"); ax[1].set_aspect("equal")
ax[1].set_title("2) Each frame = one point\nthe points form a tilted 'sausage'")

ax[2].scatter(A, B, s=8, c="0.75")
for k, col, nm in [(0, "firebrick", "PC1"), (1, "seagreen", "PC2")]:
    v = p.components_[k] * 1.3 * np.sqrt(p.explained_variance_[k])
    ax[2].plot(*np.c_[mean - v, mean + v], color=col, lw=3)
    ax[2].text(*(mean + v * 1.1), nm, color=col, fontsize=12, weight="bold")
ax[2].set_xlim(-1.8, 1.8); ax[2].set_ylim(-1.3, 1.3)
ax[2].set_xlabel("joint A"); ax[2].set_ylabel("joint B"); ax[2].set_aspect("equal")
ax[2].set_title("3) PCA finds two lines:\nPC1 = long axis of the sausage, PC2 = the axis across it")

ax[3].scatter(Y[:, 0], Y[:, 1], s=8, c=t, cmap="cool")
ax[3].set_xlim(-2.5, 2.5); ax[3].set_ylim(-2.5, 2.5); ax[3].set_aspect("equal")
ax[3].set_xlabel("PC1 value"); ax[3].set_ylabel("PC2 value")
ax[3].set_title("4) On the new axes: spread on PC1 %.0f%%,\non PC2 %.0f%% -> PC2 can be dropped"
                % (100 * ratio[0], 100 * ratio[1]))

fig.tight_layout(); fig.savefig(os.path.join(OUT, "17_toy_pca.png"), dpi=105); plt.close(fig)

# what is lost when we keep only PC1?
Xrec = mean + np.outer(Y[:, 0], p.components_[0])
err = np.abs(Xrec - X).mean()
fig, ax = plt.subplots(1, 2, figsize=(13, 3.6))
ax[0].plot(t, A, color="royalblue", lw=2, label="real A")
ax[0].plot(t, Xrec[:, 0], "k--", lw=1.2, label="A rebuilt from PC1 only")
ax[0].legend(fontsize=8, loc="upper right"); ax[0].set_xlabel("time (s)")
ax[0].set_title("We kept 1 number (PC1) instead of 2: A is almost the same")
ax[1].plot(t, Y[:, 0], color="firebrick")
ax[1].set_xlabel("time (s)"); ax[1].set_ylabel("PC1")
ax[1].set_title("One number per frame: 'how open is the leg'")
fig.tight_layout(); fig.savefig(os.path.join(OUT, "18_toy_pca_loss.png"), dpi=105); plt.close(fig)
print("explained variance:", np.round(ratio, 3), "mean abs error with PC1 only: %.3f" % err)
