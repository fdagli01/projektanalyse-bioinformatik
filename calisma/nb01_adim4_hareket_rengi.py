"""Redraw the map coloured by raw (un-normalized) movement amplitude. mmpy normalizes each 325-number
fingerprint to sum 1 before embedding, so the training data itself carries no amplitude; use the
movie-0 wavelets saved by the wavelet step and its re-embedded map positions instead."""
import os
import numpy as np, hdf5storage
import matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "calisma", "cikti")
z = hdf5storage.loadmat(os.path.join(ROOT, "calisma", "Fly_mmpy", "Projections", "fly_leap_test_pcaModes_uVals.mat"))["zValues"]
amp = np.load(os.path.join(OUT, "nb01_wlets0.npy")).sum(1)
order = np.argsort(amp)                                      # draw the most active frames on top
fig, ax = plt.subplots(figsize=(7, 6))
sc = ax.scatter(z[order, 0], z[order, 1], c=np.log10(amp[order]), s=1, cmap="viridis")
plt.colorbar(sc, ax=ax, fraction=0.046, label="log10 toplam hareket genliği")
ax.set_aspect("equal"); ax.set_xticks([]); ax.set_yticks([])
ax.set_title("Video 1'in 20.000 karesi haritada\nrenk: o andaki toplam hareket (normalize edilmemiş)")
fig.tight_layout(); fig.savefig(os.path.join(OUT, "09b_harita_hareket.png"), dpi=110); plt.close(fig)
lo, hi = np.percentile(amp, [10, 90])
for nm, m in [("sakin %10", amp <= lo), ("hareketli %10", amp >= hi)]:
    print(nm, "frames: map centre x=%.1f y=%.1f" % tuple(np.median(z[m], 0)))

# Redraw figure 09 with plain training points (the coloured version had no information, see above)
import sys, types, h5py
for name in ["moviepy", "moviepy.editor", "moviepy.video", "moviepy.video.io", "moviepy.video.io.bindings"]:
    sys.modules.setdefault(name, types.ModuleType(name))
sys.modules["moviepy.editor"].VideoClip = sys.modules["moviepy.editor"].VideoFileClip = object
sys.modules["moviepy.video.io.bindings"].mplfig_to_npimage = lambda *a, **k: None
sys.path.insert(0, os.path.join(ROOT, "unsupervised-behavior-tutorials", "motionmapperpy"))
import motionmapperpy as mmpy
with h5py.File(os.path.join(ROOT, "calisma", "Fly_mmpy", "UMAP", "training_embedding.mat"), "r") as f:
    ty = f["trainingEmbedding"][:].T
m = np.abs(ty).max()
fig, ax = plt.subplots(1, 4, figsize=(19, 5))
ax[0].scatter(ty[:, 0], ty[:, 1], s=2, c="k")
ax[0].set_title("%d eğitim noktası (her biri bir an)" % len(ty))
for a, sigma in zip(ax[1:], [1.0, 3.0, 6.0]):
    _, xx, dens = mmpy.findPointDensity(ty, sigma, 511, [-m - 15, m + 15])
    a.imshow(dens, extent=(xx[0], xx[-1], xx[0], xx[-1]), cmap=mmpy.gencmap(), origin="lower")
    a.set_title("yoğunluk, sigma = %.0f" % sigma)
for a in ax:
    a.set_xlim(-m - 15, m + 15); a.set_ylim(-m - 15, m + 15); a.set_aspect("equal"); a.set_xticks([]); a.set_yticks([])
fig.suptitle("Sineğin davranış haritası: tepeler = sık yapılan davranışlar")
fig.tight_layout(); fig.savefig(os.path.join(OUT, "09_harita_yogunluk.png"), dpi=110); plt.close(fig)
