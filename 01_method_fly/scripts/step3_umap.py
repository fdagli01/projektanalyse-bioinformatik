"""Step 3 (Notebook 01, section 7): compress the 325-number fingerprints into a 2-D behavioral map (UMAP).
First a toy example with known 'behaviors', then the real fly map: training set, density, re-embedding."""
import os, sys, types, glob, shutil, time
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))   # 01_method_fly/
ROOT = os.path.dirname(HERE)                                         # repository root
OUT = os.path.join(HERE, "figures", "working")
CACHE = os.path.join(HERE, "intermediate")   # regenerated .npz/.npy and the Fly_mmpy project (not in git)

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


def toy_umap():
    # 4 made-up 'behaviors', each a typical 325-number fingerprint; every frame is one of them plus noise
    import umap
    rng = np.random.default_rng(1)
    names = ["rest", "walk", "groom", "turn"]
    protos = rng.gamma(1.0, 1.0, size=(4, 325)) * np.array([0.2, 1, 1, 1])[:, None]
    labels = rng.integers(0, 4, 3000)
    X = protos[labels] + rng.normal(0, 0.6, size=(3000, 325))
    Z = umap.UMAP(n_neighbors=15, random_state=0).fit_transform(X)
    fig, ax = plt.subplots(1, 2, figsize=(12, 5))
    ax[0].imshow(X[np.argsort(labels)][::10], aspect="auto", cmap="PuRd")
    ax[0].set_title("Input: 3000 frames × 325 numbers (sorted by label)\nhard to see the groups by eye")
    ax[0].set_xlabel("325 features"); ax[0].set_ylabel("frames")
    for k, nm in enumerate(names):
        m = labels == k
        ax[1].scatter(Z[m, 0], Z[m, 1], s=3, label=nm)
    ax[1].legend(markerscale=4); ax[1].set_xticks([]); ax[1].set_yticks([])
    ax[1].set_title("UMAP output: 2-D map\n(colours only for checking; UMAP never saw the labels)")
    fig.tight_layout(); fig.savefig(os.path.join(OUT, "08_toy_umap.png"), dpi=110); plt.close(fig)


def main():
    toy_umap()
    print("toy done")

    d = np.load(os.path.join(CACHE, "pca.npz"))
    projs_list, n_pca, fps = [d["proj0"], d["proj1"]], int(d["n_pca"]), int(d["fps"])
    datasetnames = ["fly_leap_test", "fly_leap_test_2"]

    projectPath = os.path.join(CACHE, "Fly_mmpy")
    shutil.rmtree(projectPath, ignore_errors=True)          # build from scratch every run
    mmpy.createProjectDirectory(projectPath)
    for nm, projs in zip(datasetnames, projs_list):
        hdf5storage.savemat("%s/Projections/%s_pcaModes.mat" % (projectPath, nm), {"projections": projs})

    parameters = mmpy.setRunParameters()
    parameters.projectPath = projectPath
    parameters.method = "UMAP"
    parameters.samplingFreq = fps
    parameters.minF, parameters.maxF, parameters.numPeriods = 1, 50, 25
    parameters.pcaModes = n_pca
    parameters.useGPU, parameters.numProcessors = -1, -1
    parameters.training_numPoints, parameters.trainingSetSize = 3000, 5000

    t0 = time.time()
    mmpy.subsampled_tsne_from_projections(parameters, parameters.projectPath)
    print("training map built in %d s" % (time.time() - t0))

    tfolder = "%s/%s/" % (projectPath, parameters.method)
    with h5py.File(tfolder + "training_data.mat", "r") as f: trainingSetData = f["trainingSetData"][:].T
    with h5py.File(tfolder + "training_embedding.mat", "r") as f: trainingEmbedding = f["trainingEmbedding"][:].T
    ty = trainingEmbedding
    m = np.abs(ty).max()

    # training points + density at three smoothings. (The training fingerprints are normalized to sum 1,
    # so they carry no movement amplitude; step3b_map_by_movement.py colours the map by raw amplitude.)
    fig, ax = plt.subplots(1, 4, figsize=(19, 5))
    ax[0].scatter(ty[:, 0], ty[:, 1], s=2, c="k")
    ax[0].set_title("%d training points (each one a moment)" % len(ty))
    for a, sigma in zip(ax[1:], [1.0, 3.0, 6.0]):
        _, xx, dens = mmpy.findPointDensity(ty, sigma, 511, [-m - 15, m + 15])
        a.imshow(dens, extent=(xx[0], xx[-1], xx[0], xx[-1]), cmap=mmpy.gencmap(), origin="lower")
        a.set_title("density, sigma = %.0f" % sigma)
    for a in ax:
        a.set_xlim(-m - 15, m + 15); a.set_ylim(-m - 15, m + 15); a.set_aspect("equal"); a.set_xticks([]); a.set_yticks([])
    fig.suptitle("Fly behaviour map: peaks = frequently performed behaviours")
    fig.tight_layout(); fig.savefig(os.path.join(OUT, "09_map_density.png"), dpi=110); plt.close(fig)

    # re-embed every frame of both movies onto the training map
    t0 = time.time()
    zs = {}
    for nm in datasetnames:
        pf = "%s/Projections/%s_pcaModes.mat" % (projectPath, nm)
        projections = hdf5storage.loadmat(pf)["projections"]
        z, _ = mmpy.findEmbeddings(projections, trainingSetData, trainingEmbedding, parameters)
        z = np.asarray(z)
        hdf5storage.write(data={"zValues": z}, path="/", filename=pf[:-4] + "_uVals.mat",
                          store_python_metadata=False, matlab_compatible=True, truncate_existing=True)
        zs[nm] = z
    print("all %d frames embedded in %d s" % (sum(len(z) for z in zs.values()), time.time() - t0))

    # one movie's journey across the map: 10 s of trajectory on top of the full density
    z = zs[datasetnames[0]]
    allz = np.concatenate(list(zs.values()))
    _, xx, dens = mmpy.findPointDensity(allz, 3.0, 511, [-m - 15, m + 15])
    seg = slice(1000, 2000)
    fig, ax = plt.subplots(1, 2, figsize=(14, 6))
    ax[0].imshow(dens, extent=(xx[0], xx[-1], xx[0], xx[-1]), cmap=mmpy.gencmap(), origin="lower")
    ax[0].plot(z[seg, 0], z[seg, 1], "-", color="w", lw=0.6, alpha=0.8)
    sc = ax[0].scatter(z[seg, 0], z[seg, 1], c=np.arange(seg.stop - seg.start) / fps, s=6, cmap="cool", zorder=3)
    plt.colorbar(sc, ax=ax[0], fraction=0.046, label="time (s)")
    ax[0].set_title("How does the fly move across the map in 10 seconds?\n(on top of the density of all %d frames)" % len(allz))
    ax[0].set_aspect("equal"); ax[0].set_xticks([]); ax[0].set_yticks([])
    speed = np.r_[0, np.linalg.norm(np.diff(z, axis=0), axis=1)]
    tt = np.arange(seg.stop - seg.start) / fps
    ax[1].plot(tt, speed[seg], "k", lw=0.8)
    ax[1].set_xlabel("time (s)"); ax[1].set_ylabel("speed on the map (per frame)")
    ax[1].set_title("Speed on the map: low = staying in one behaviour,\njump = switching to another behaviour")
    fig.tight_layout(); fig.savefig(os.path.join(OUT, "10_map_trajectory.png"), dpi=110); plt.close(fig)
    print("saved figures 08-10")


if __name__ == "__main__":   # macOS starts worker processes by re-importing this file
    main()
