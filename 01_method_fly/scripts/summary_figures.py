"""The six summary figures used on the one-page overview (figures/summary/).
Recomputes the cheap steps and reloads the saved UMAP map / watershed result, so nothing is retrained."""
import os, sys, types
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
OUT = os.path.join(HERE, "figures", "summary")
CACHE = os.path.join(HERE, "intermediate")   # regenerated .npz/.npy and the Fly_mmpy project (not in git)
os.makedirs(OUT, exist_ok=True)

def _stub(name, **attrs):
    m = sys.modules.get(name) or types.ModuleType(name)
    for k, v in attrs.items():
        setattr(m, k, v)
    sys.modules[name] = m
_stub("moviepy"); _stub("moviepy.editor", VideoClip=object, VideoFileClip=object)
_stub("moviepy.video"); _stub("moviepy.video.io")
_stub("moviepy.video.io.bindings", mplfig_to_npimage=lambda *a, **k: None)
sys.path.insert(0, os.path.join(ROOT, "unsupervised-behavior-tutorials", "motionmapperpy"))
import motionmapperpy as mmpy
import hdf5storage, h5py


def main():
    fps = 100
    names = ["fly_leap_test", "fly_leap_test_2"]
    h5s = []
    for d in names:
        h = pd.read_hdf(os.path.join(DATA, "%s_positions.h5" % d))
        keep = np.mod(np.arange(1, h.shape[1] + 1), 3) != 0
        h5s.append(median_filter(h.values[:, keep].reshape((-1, 32, 2)), size=(5, 1, 1)))

    # 1. skeleton on video frames
    connections = [np.arange(6, 10), np.arange(10, 14), np.arange(14, 18), np.arange(18, 22),
                   np.arange(22, 26), np.arange(26, 30), [2, 0, 1], [0, 3, 4, 5], [31, 3, 30]]
    cap = cv2.VideoCapture(os.path.join(DATA, names[0] + ".mp4"))
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
    fig.tight_layout(); fig.savefig(os.path.join(OUT, "1_skeleton.png"), dpi=110); plt.close(fig)

    # 2. joint angles
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

    angles = []
    for h in h5s:
        A = np.zeros((h.shape[0], len(angleinds)))
        for i, (a, b, c, fl) in enumerate(angleinds):
            A[:, i] = angle_between(h[:, a] - h[:, b], h[:, c] - h[:, b], fl)
        angles.append(A)
    lo = np.min([A.min(0) for A in angles], 0); angles = [A - lo for A in angles]
    hi = np.max([A.max(0) for A in angles], 0); angles = [A / hi for A in angles]
    t = np.arange(1000) / fps
    fig, ax = plt.subplots(figsize=(13, 3.5))
    ax.plot(t, angles[0][1000:2000, [3, 9, 13]])
    ax.set_xlabel("time (s)"); ax.set_ylabel("normalized angle (0-1)")
    ax.legend(["wing tip angle", "hind leg tibia angle", "middle leg femur-tibia angle"], loc="upper right")
    ax.set_title("Egocentric pose: 3 of the 22 joint angles over 10 seconds")
    fig.tight_layout(); fig.savefig(os.path.join(OUT, "2_angles.png"), dpi=110); plt.close(fig)

    # 3. PCA
    X = np.concatenate(angles, axis=0)
    p = PCA().fit(X)
    n_pca = int(np.argmax(np.cumsum(p.explained_variance_ratio_) > 0.95)) + 1
    fig, ax = plt.subplots(1, 2, figsize=(14, 3.8))
    ax[0].plot(np.arange(1, X.shape[1] + 1), np.cumsum(p.explained_variance_ratio_), "firebrick", marker=".")
    ax[0].axvline(n_pca, ls="--", color="royalblue"); ax[0].axhline(0.95, ls=":", color="grey")
    ax[0].set_xlabel("number of PCA components"); ax[0].set_ylabel("cumulative explained variance")
    ax[0].set_title("%d components carry 95%% of the variance" % n_pca)
    for i in range(4):
        ax[1].bar(np.arange(X.shape[1]) + i * 0.2, p.components_[i], width=0.2, label="PC%d" % (i + 1))
    ax[1].set_xlabel("22 joint angles"); ax[1].set_ylabel("contribution to PC"); ax[1].legend(ncol=4)
    ax[1].set_title("Which angles make up the first 4 components?")
    fig.tight_layout(); fig.savefig(os.path.join(OUT, "3_pca.png"), dpi=110); plt.close(fig)

    # 4. toy wavelet
    class P: pass
    prm = mmpy.setRunParameters()
    prm.samplingFreq, prm.minF, prm.maxF, prm.numPeriods = fps, 1, 50, 25
    prm.numProcessors, prm.useGPU = -1, -1
    tt = np.arange(0, 8, 1 / fps)
    toy = np.zeros_like(tt)
    toy[(tt >= 2) & (tt < 4)] = np.sin(2 * np.pi * 3 * tt[(tt >= 2) & (tt < 4)])
    toy[(tt >= 4) & (tt < 6)] = np.sin(2 * np.pi * 20 * tt[(tt >= 4) & (tt < 6)])
    both = tt >= 6
    toy[both] = np.sin(2 * np.pi * 3 * tt[both]) + 0.7 * np.sin(2 * np.pi * 20 * tt[both])
    toy += 0.05 * np.random.default_rng(0).standard_normal(len(tt))
    wt, freqs = mmpy.findWavelets(toy[:, None], 1, prm.omega0, prm.numPeriods, prm.samplingFreq,
                                  prm.maxF, prm.minF, prm.numProcessors, prm.useGPU)
    wt, freqs = np.asarray(wt), np.asarray(freqs)
    fig, ax = plt.subplots(2, 1, figsize=(13, 5.5), sharex=True)
    ax[0].plot(tt, toy, "k", lw=0.8)
    for x0, lab in [(0, "rest"), (2, "slow (3 Hz)"), (4, "fast (20 Hz)"), (6, "both")]:
        ax[0].text(x0 + 1, 2.0, lab, ha="center", fontsize=12, color="firebrick")
    ax[0].set_ylim(-2, 2.4); ax[0].set_ylabel("signal")
    ax[0].set_title("Toy signal: think of one joint angle changing over time")
    ax[1].imshow(wt.T, aspect="auto", origin="lower", cmap="PuRd", extent=(0, 8, 0, len(freqs)))
    ticks = [0, 6, 12, 18, 24]
    ax[1].set_yticks([i + 0.5 for i in ticks]); ax[1].set_yticklabels(["%.0f" % freqs[i] for i in ticks])
    ax[1].set_ylabel("frequency (Hz)"); ax[1].set_xlabel("time (s)")
    ax[1].set_title("Wavelet: how much movement at each speed, at every moment")
    fig.tight_layout(); fig.savefig(os.path.join(OUT, "4_wavelet.png"), dpi=110); plt.close(fig)

    # 5. UMAP map: training points and density at three smoothings
    tfolder = os.path.join(CACHE, "Fly_mmpy", "UMAP")
    with h5py.File(os.path.join(tfolder, "training_embedding.mat"), "r") as f:
        ty = f["trainingEmbedding"][:].T
    m = np.abs(ty).max()
    fig, ax = plt.subplots(1, 4, figsize=(19, 5))
    ax[0].scatter(ty[:, 0], ty[:, 1], s=2, c="k")
    ax[0].set_title("%d training points\n(each one a moment in time)" % len(ty))
    for a, sigma in zip(ax[1:], [1.0, 3.0, 6.0]):
        _, xx, dens = mmpy.findPointDensity(ty, sigma, 511, [-m - 15, m + 15])
        a.imshow(dens, extent=(xx[0], xx[-1], xx[0], xx[-1]), cmap=mmpy.gencmap(), origin="lower")
        a.set_title("density, smoothing sigma = %.0f" % sigma)
    for a in ax:
        a.set_xlim(-m - 15, m + 15); a.set_ylim(-m - 15, m + 15); a.set_aspect("equal"); a.set_xticks([]); a.set_yticks([])
    fig.suptitle("Behavior map: peaks = frequently performed behaviors")
    fig.tight_layout(); fig.savefig(os.path.join(OUT, "5_umap.png"), dpi=110); plt.close(fig)

    # 6. watershed regions + time spent per region
    wfile = hdf5storage.loadmat(os.path.join(tfolder, "zVals_wShed_groups.mat"))
    wregs = wfile["watershedRegions"].flatten().astype(int)
    zValues, LL, xx = wfile["zValues"], wfile["LL"], wfile["xx"].flatten()
    nreg = int(wregs.max())
    mm = np.abs(zValues).max()
    _, gx, dens = mmpy.findPointDensity(zValues, 3.0, 511, [-mm - 10, mm + 10])
    fig, ax = plt.subplots(1, 2, figsize=(14, 6))
    ax[0].imshow(dens, extent=(gx[0], gx[-1], gx[0], gx[-1]), cmap=mmpy.gencmap(), origin="lower")
    ax[0].contour(LL, levels=np.arange(0.5, LL.max() + 1), colors="w", linewidths=0.8,
                  extent=(xx[0], xx[-1], xx[0], xx[-1]), origin="lower")
    for r in range(1, nreg + 1):
        c = np.median(zValues[wregs == r], 0)
        if np.all(np.isfinite(c)):
            ax[0].text(c[0], c[1], str(r), color="k", fontsize=11, ha="center", va="center", weight="bold",
                       bbox=dict(boxstyle="circle,pad=0.15", fc="w", alpha=0.8))
    ax[0].set_aspect("equal"); ax[0].set_xticks([]); ax[0].set_yticks([])
    ax[0].set_title("Watershed: the map is cut into %d behavior regions" % nreg)
    occ = np.array([np.mean(wregs == r) for r in range(1, nreg + 1)])
    ax[1].bar(range(1, nreg + 1), 100 * occ, color="firebrick")
    ax[1].set_xticks(range(1, nreg + 1)); ax[1].set_xlabel("region"); ax[1].set_ylabel("% of time")
    ax[1].set_title("How does the fly spend its time?")
    fig.tight_layout(); fig.savefig(os.path.join(OUT, "6_regions.png"), dpi=110); plt.close(fig)
    print("saved:", sorted(os.listdir(OUT)))


if __name__ == "__main__":   # macOS starts worker processes by re-importing this file
    main()
