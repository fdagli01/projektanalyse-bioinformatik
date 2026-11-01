"""Step 2 (Notebook 01, sections 5-6): parameters and the wavelet transform (posture -> postural dynamics).
Starts with a toy signal so the idea is visible, then runs it on the fly's PCA modes."""
import os, sys, types
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))   # 01_method_fly/
ROOT = os.path.dirname(HERE)                                         # repository root
OUT = os.path.join(HERE, "figures", "working")
CACHE = os.path.join(HERE, "intermediate")   # regenerated .npz/.npy and the Fly_mmpy project (not in git)

# motionmapperpy imports moviepy on load; none of this uses video, so stub it (as the notebooks do)
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


def main():
    d = np.load(os.path.join(CACHE, "pca.npz"))
    proj0, n_pca, fps = d["proj0"], int(d["n_pca"]), int(d["fps"])

    parameters = mmpy.setRunParameters()
    parameters.samplingFreq = fps
    parameters.minF, parameters.maxF, parameters.numPeriods = 1, 50, 25
    parameters.numProcessors, parameters.useGPU = -1, -1
    print("omega0 =", parameters.omega0)

    def wavelets(x):
        w, f = mmpy.findWavelets(x, x.shape[1], parameters.omega0, parameters.numPeriods,
                                 parameters.samplingFreq, parameters.maxF, parameters.minF,
                                 parameters.numProcessors, parameters.useGPU)
        return np.asarray(w), np.asarray(f)

    # ---- toy signal: 2 s resting, 2 s slow 3 Hz swing, 2 s fast 20 Hz flicking, 2 s both
    t = np.arange(0, 8, 1 / fps)
    toy = np.zeros_like(t)
    toy[(t >= 2) & (t < 4)] = np.sin(2 * np.pi * 3 * t[(t >= 2) & (t < 4)])
    toy[(t >= 4) & (t < 6)] = np.sin(2 * np.pi * 20 * t[(t >= 4) & (t < 6)])
    both = (t >= 6)
    toy[both] = np.sin(2 * np.pi * 3 * t[both]) + 0.7 * np.sin(2 * np.pi * 20 * t[both])
    toy += 0.05 * np.random.default_rng(0).standard_normal(len(t))
    wt, freqs = wavelets(toy[:, None])
    print("frequency channels (Hz):", np.round(freqs, 1))

    fig, ax = plt.subplots(2, 1, figsize=(13, 5.5), sharex=True)
    ax[0].plot(t, toy, "k", lw=0.8)
    for x0, lab in [(0, "rest"), (2, "slow (3 Hz)"), (4, "fast (20 Hz)"), (6, "both")]:
        ax[0].text(x0 + 1, 2.0, lab, ha="center", fontsize=11, color="firebrick")
    ax[0].set_ylim(-2, 2.4); ax[0].set_ylabel("signal"); ax[0].set_title("Toy signal: think of one joint angle changing over time")
    ax[1].imshow(wt.T, aspect="auto", origin="lower", cmap="PuRd", extent=(0, 8, 0, len(freqs)))
    ticks = [0, 6, 12, 18, 24]
    ax[1].set_yticks([i + 0.5 for i in ticks]); ax[1].set_yticklabels(["%.0f" % freqs[i] for i in ticks])
    ax[1].set_ylabel("frequency (Hz)"); ax[1].set_xlabel("time (s)")
    ax[1].set_title("Wavelet: how much movement at each frequency, at every moment?")
    fig.tight_layout(); fig.savefig(os.path.join(OUT, "05_toy_wavelet.png"), dpi=110); plt.close(fig)

    # ---- the fly: wavelets of all PCA modes
    wlets, freqs = wavelets(proj0)
    print("fly wavelets:", wlets.shape, "=", n_pca, "modes x", parameters.numPeriods, "frequencies")

    nshow, show = 600, 4
    fig, axes = plt.subplots(show + 1, 1, figsize=(13, 9), sharex=True)
    tt = np.arange(nshow) / fps
    for i in range(3):
        axes[0].plot(tt, proj0[:nshow, i], lw=0.8, label="PC%d" % (i + 1))
    axes[0].legend(ncol=3, fontsize=8, loc="upper right"); axes[0].set_ylabel("PCA mode")
    axes[0].set_title("First 6 seconds of the fly: raw PCA modes on top, their wavelet spectrograms below")
    for i in range(show):
        axes[i + 1].imshow(wlets[:nshow, 25 * i:25 * (i + 1)].T, cmap="PuRd", aspect="auto", origin="lower",
                           extent=(0, nshow / fps, 0, 25))
        axes[i + 1].set_yticks([0.5, 24.5]); axes[i + 1].set_yticklabels(["1", "50"])
        axes[i + 1].set_ylabel("PC%d\nHz" % (i + 1), fontsize=9)
    axes[-1].set_xlabel("time (s)")
    fig.tight_layout(); fig.savefig(os.path.join(OUT, "06_fly_wavelet.png"), dpi=110); plt.close(fig)

    # ---- what one frame looks like now: a quiet moment vs an active moment
    power = wlets.sum(1)
    quiet, active = int(np.argmin(power[:5000])), int(np.argmax(power[:5000]))
    fig, ax = plt.subplots(2, 1, figsize=(13, 4.5), sharex=True, sharey=True)
    for a, fr, lab in [(ax[0], quiet, "quiet moment"), (ax[1], active, "active moment")]:
        a.bar(np.arange(wlets.shape[1]), wlets[fr], width=1.0, color="firebrick")
        for k in range(1, n_pca):
            a.axvline(25 * k - 0.5, color="0.8", lw=0.6)
        a.set_title("%s (frame %d, t = %.2f s): %d-number 'movement fingerprint'" % (lab, fr, fr / fps, wlets.shape[1]))
    ax[1].set_xticks([25 * k + 12 for k in range(n_pca)]); ax[1].set_xticklabels(["PC%d" % (k + 1) for k in range(n_pca)])
    ax[1].set_xlabel("25 frequencies per PC (left to right: slow → fast)")
    fig.tight_layout(); fig.savefig(os.path.join(OUT, "07_fingerprint.png"), dpi=110); plt.close(fig)

    np.save(os.path.join(CACHE, "wavelets_movie0.npy"), wlets)
    print("saved figures 05-07")


if __name__ == "__main__":   # macOS starts worker processes by re-importing this file
    main()
