"""Notebook 01, sections 8-10: carve the map into behaviors (watershed), read the ethogram, and look at
example bouts of each region so they can be named. Starts with a toy landscape to show the idea."""
import os, sys, types, glob, shutil
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import cv2

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "calisma", "cikti")
DATA = os.path.join(ROOT, "unsupervised-behavior-tutorials", "motionmapperpy", "data", "fly")

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
import hdf5storage


def toy_watershed():
    # a made-up 2-D density with four hills; flood it and see where the pools meet
    from skimage.segmentation import watershed
    from skimage.feature import peak_local_max
    x = np.linspace(-10, 10, 300); X, Y = np.meshgrid(x, x)
    hills = [(-5, -4, 2.0, 1.0), (4, -3, 2.5, 0.8), (0, 5, 1.8, 0.6), (5, 5, 1.2, 0.5)]
    D = sum(h * np.exp(-((X - a) ** 2 + (Y - b) ** 2) / (2 * s ** 2)) for a, b, s, h in hills)
    peaks = peak_local_max(D, min_distance=10)
    markers = np.zeros(D.shape, int)
    for k, (i, j) in enumerate(peaks, 1):
        markers[i, j] = k
    L = watershed(-D, markers)
    fig = plt.figure(figsize=(15, 4.8))
    ax0 = fig.add_subplot(1, 3, 1, projection="3d")
    ax0.plot_surface(X, Y, D, cmap="viridis", linewidth=0, antialiased=False)
    ax0.set_title("Yoğunluk = arazi (tepeler = davranışlar)"); ax0.set_xticks([]); ax0.set_yticks([]); ax0.set_zticks([])
    ax1 = fig.add_subplot(1, 3, 2)
    ax1.imshow(D, origin="lower", cmap=mmpy.gencmap(), extent=(-10, 10, -10, 10))
    ax1.plot(x[peaks[:, 1]], x[peaks[:, 0]], "w*", ms=14)
    ax1.set_title("Her tepenin zirvesi bir başlangıç noktası"); ax1.set_xticks([]); ax1.set_yticks([])
    ax2 = fig.add_subplot(1, 3, 3)
    ax2.imshow(L, origin="lower", cmap="tab10", extent=(-10, 10, -10, 10), alpha=0.6)
    ax2.contour(X, Y, L, levels=np.arange(0.5, L.max()), colors="k", linewidths=1.5)
    ax2.contour(X, Y, D, levels=8, colors="w", linewidths=0.5)
    ax2.set_title("Ters çevirip su doldur: havuzların\nbuluştuğu yerler = sınırlar"); ax2.set_xticks([]); ax2.set_yticks([])
    fig.tight_layout(); fig.savefig(os.path.join(OUT, "11_oyuncak_watershed.png"), dpi=110); plt.close(fig)


def main():
    toy_watershed()
    datasetnames = ["fly_leap_test", "fly_leap_test_2"]
    moviepaths = [os.path.join(DATA, "%s.mp4" % d) for d in datasetnames]
    fps = 100
    projectPath = os.path.join(ROOT, "calisma", "Fly_mmpy")

    parameters = mmpy.setRunParameters()
    parameters.projectPath, parameters.method = projectPath, "UMAP"
    parameters.samplingFreq, parameters.minF, parameters.maxF, parameters.numPeriods = fps, 1, 50, 25
    parameters.useGPU, parameters.numProcessors = -1, -1
    for f in glob.glob("%s/UMAP/zWshed*.png" % projectPath) + glob.glob("%s/UMAP/zVals_wShed_groups.mat" % projectPath):
        os.remove(f)
    mmpy.findWatershedRegions(parameters, num_regions=12, startsigma=0.5,
                              pThreshold=[0.33, 0.67], saveplot=True, endident="*_pcaModes.mat")
    shutil.copy(glob.glob("%s/UMAP/zWshed*.png" % projectPath)[0], os.path.join(OUT, "12_mmpy_watershed.png"))

    wfile = hdf5storage.loadmat("%s/UMAP/zVals_wShed_groups.mat" % projectPath)
    print("file keys:", [k for k in wfile.keys() if not k.startswith("__")])
    wregs = wfile["watershedRegions"].flatten().astype(int)
    zValues = wfile["zValues"]
    LL = wfile["LL"]; xx = wfile["xx"].flatten() if "xx" in wfile else None
    nreg = int(wregs.max())
    print("regions: %d; frames with label 0 (on a border): %.1f%%" % (nreg, 100 * np.mean(wregs == 0)))

    names = [str(nm[0][0]).replace("_pcaModes", "") for nm in wfile["zValNames"][0]]
    bounds = np.r_[0, np.cumsum(wfile["zValLens"][0].flatten())].astype(int)
    rows = [slice(bounds[names.index(d)], bounds[names.index(d) + 1]) for d in datasetnames]
    z_by_rec = [zValues[r] for r in rows]
    regs_by_rec = [wregs[r] for r in rows]

    # map with region borders + numbers, and how much time is spent in each region
    m = np.abs(zValues).max()
    _, gx, dens = mmpy.findPointDensity(zValues, 3.0, 511, [-m - 10, m + 10])
    fig, ax = plt.subplots(1, 2, figsize=(14, 6))
    ax[0].imshow(dens, extent=(gx[0], gx[-1], gx[0], gx[-1]), cmap=mmpy.gencmap(), origin="lower")
    ext = (xx[0], xx[-1], xx[0], xx[-1]) if xx is not None else (gx[0], gx[-1], gx[0], gx[-1])
    ax[0].contour(LL, levels=np.arange(0.5, LL.max() + 1), colors="w", linewidths=0.8, extent=ext, origin="lower")
    for r in range(1, nreg + 1):
        c = np.median(zValues[wregs == r], 0)
        if np.all(np.isfinite(c)):
            ax[0].text(c[0], c[1], str(r), color="k", fontsize=11, ha="center", va="center", weight="bold",
                       bbox=dict(boxstyle="circle,pad=0.15", fc="w", alpha=0.8))
    ax[0].set_aspect("equal"); ax[0].set_xticks([]); ax[0].set_yticks([])
    ax[0].set_title("Watershed: harita %d davranış bölgesine bölündü" % nreg)
    occ = np.array([np.mean(wregs == r) for r in range(1, nreg + 1)])
    ax[1].bar(range(1, nreg + 1), 100 * occ, color="firebrick")
    ax[1].set_xticks(range(1, nreg + 1)); ax[1].set_xlabel("bölge"); ax[1].set_ylabel("zamanın yüzdesi")
    ax[1].set_title("Sinek zamanını hangi davranışta geçiriyor?")
    fig.tight_layout(); fig.savefig(os.path.join(OUT, "13_bolgeler.png"), dpi=110); plt.close(fig)

    # ethogram: one label per frame, for both movies, plus a 20 s zoom
    fig, axes = plt.subplots(3, 1, figsize=(15, 8))
    for ax, regs, nm in zip(axes[:2], regs_by_rec, datasetnames):
        E = np.zeros((nreg + 1, len(regs)))
        E[regs, np.arange(len(regs))] = 1
        ax.imshow(E[1:], aspect="auto", cmap="Greys", interpolation="nearest",
                  extent=(0, len(regs) / fps, nreg + 0.5, 0.5))
        ax.set_ylabel("bölge"); ax.set_title("Etogram: %s (200 s)" % nm)
    seg = slice(2000, 4000)
    regs = regs_by_rec[0][seg]
    tt = np.arange(len(regs)) / fps + seg.start / fps
    axes[2].step(tt, regs, where="post", color="firebrick", lw=1)
    axes[2].set_ylim(0.5, nreg + 0.5); axes[2].set_yticks(range(1, nreg + 1))
    axes[2].set_xlabel("zaman (s)"); axes[2].set_ylabel("bölge"); axes[2].set_title("Yakın plan: 20 saniye")
    fig.tight_layout(); fig.savefig(os.path.join(OUT, "14_etogram.png"), dpi=110); plt.close(fig)

    # bouts: how long does the fly stay in one behavior?
    lens = []
    for regs in regs_by_rec:
        change = np.flatnonzero(np.diff(regs)) + 1
        segs = np.split(regs, change)
        lens += [len(s) / fps for s in segs if s[0] > 0]
    lens = np.array(lens)
    print("bouts: %d; median %.2f s; 90th percentile %.2f s; longest %.1f s"
          % (len(lens), np.median(lens), np.percentile(lens, 90), lens.max()))

    # what is each region? 5 frames from the longest bout of each region, cropped around the fly
    h5s = []
    for d in datasetnames:
        import pandas as pd
        from scipy.ndimage import median_filter
        h = pd.read_hdf(os.path.join(DATA, "%s_positions.h5" % d))
        keep = np.mod(np.arange(1, h.shape[1] + 1), 3) != 0
        h5s.append(median_filter(h.values[:, keep].reshape((-1, 32, 2)), size=(5, 1, 1)))
    connections = [np.arange(6, 10), np.arange(10, 14), np.arange(14, 18), np.arange(18, 22),
                   np.arange(22, 26), np.arange(26, 30), [2, 0, 1], [0, 3, 4, 5], [31, 3, 30]]
    ncol = 6
    fig, axes = plt.subplots(nreg, ncol, figsize=(ncol * 1.9, nreg * 1.9))
    for r in range(1, nreg + 1):
        best = None
        for di, regs in enumerate(regs_by_rec):
            on = np.r_[0, (regs == r).astype(int), 0]
            st, en = np.flatnonzero(np.diff(on) == 1), np.flatnonzero(np.diff(on) == -1)
            for s, e in zip(st, en):
                if best is None or e - s > best[0]:
                    best = (e - s, di, s)
        row = axes[r - 1]
        for a in row:
            a.set_xticks([]); a.set_yticks([])
        if best is None:
            row[0].set_ylabel("bölge %d\n(yok)" % r); continue
        L, di, s = best
        cap = cv2.VideoCapture(moviepaths[di])
        for k, fr in enumerate(np.linspace(s, s + L - 1, ncol).astype(int)):
            cap.set(cv2.CAP_PROP_POS_FRAMES, fr); ok, img = cap.read()
            if not ok:
                continue
            row[k].imshow(cv2.cvtColor(img, cv2.COLOR_BGR2RGB), origin="lower")
            for c in connections:
                row[k].plot(h5s[di][fr, c, 0], h5s[di][fr, c, 1], "-", color="firebrick", lw=0.7)
            row[k].set_title("%.2f s" % ((fr - s) / fps), fontsize=7)
        cap.release()
        row[0].set_ylabel("bölge %d\n%.2f s" % (r, L / fps), fontsize=9)
    fig.suptitle("Her bölgenin en uzun epizodundan 6 kare (soldaki: bölge no. ve epizod süresi)", y=1.0)
    fig.tight_layout(); fig.savefig(os.path.join(OUT, "15_bolge_ornekleri.png"), dpi=90); plt.close(fig)

    np.savez(os.path.join(OUT, "nb01_etogram.npz"), regs0=regs_by_rec[0], regs1=regs_by_rec[1],
             z0=z_by_rec[0], z1=z_by_rec[1], nreg=nreg, fps=fps)
    print("saved figures 11-15")


if __name__ == "__main__":   # macOS starts worker processes by re-importing this file
    main()
