# Stage 1 – Learn the MotionMapper method on fly data ✅

A step-by-step re-implementation of the MotionMapper pipeline on the public fruit-fly demo data
(`fly_leap_test`, `fly_leap_test_2`: 32 tracked keypoints per frame, 100 fps), with a figure for every step.
The goal was to understand each step before applying it to the mouse data (stage 5).

## Pipeline

```
keypoints (x, y) ──► median filter ──► joint angles ──► PCA ──► Morlet wavelets ──► UMAP ──► watershed ──► ethogram
   32 points          tracking jumps     22 angles      13 modes   13 × 25 = 325      2-D map    12 regions    behaviour
                                         (egocentric)   (95 % var.) features/frame                            over time
```

1. **Cleaning.** A temporal median filter removes tracking jumps.
2. **Egocentric representation.** Pairs of body-part vectors become 22 joint angles, so the description does not depend on where the animal is or which way it faces. Angles are min–max normalised.
3. **PCA.** Correlated angles are compressed into the fewest modes that explain 95 % of the variance (13 here).
4. **Wavelet transform.** A Morlet wavelet transform (25 frequencies, 1–50 Hz) turns posture into postural dynamics: how much slow and fast movement each mode shows at every moment.
5. **UMAP embedding.** The 325 features per frame are embedded into a 2-D behaviour map; a smoothed density shows frequent behaviours as peaks.
6. **Watershed.** The density map is cut into 12 regions (candidate behaviours). Every frame gets a region label, giving an ethogram and the time spent per behaviour.

Steps 4–6 use the pinned `motionmapperpy` package from the tutorial repository; steps 1–3 use NumPy, SciPy and scikit-learn.

## Scripts

Run them in this order; each step reads the output of the previous one from `intermediate/`.

| Script | What it does | Figures |
|---|---|---|
| `scripts/step1_clean_angles_pca.py` | cleaning, joint angles, PCA | 01–04 |
| `scripts/step2_wavelet.py` | wavelet features (toy signal first, then the fly) | 05–07 |
| `scripts/step3_umap.py` | UMAP map, density, re-embedding of all frames | 08–10 |
| `scripts/step3b_map_by_movement.py` | the map coloured by movement amplitude | 09, 09b |
| `scripts/step4_watershed.py` | watershed regions, ethogram, example bouts per region | 11–15 |
| `scripts/demo_raw_xy_vs_angles.py` | why joint angles: raw x/y vs angles when the fly moves and turns | 16 |
| `scripts/demo_toy_pca.py` | a tiny PCA example with 2 angles | 17–18 |
| `scripts/summary_figures.py` | the six summary figures | `figures/summary/` |
| `scripts/summary_page.py`, `scripts/summary_page_deck.py` | one-page overview (plain and slide style) | 19, 21 |

## Figures

- `figures/summary/` – the six summary figures (one per pipeline step), English.
- `figures/working/` – all working figures, numbered like the scripts above.
  **Note:** the text inside these images is still Turkish. The scripts are already translated;
  the images change once the scripts are run again (see *Reproducing*).

| Step | Figure |
|---|---|
| Skeleton on video frames | [1_skeleton.png](figures/summary/1_skeleton.png) |
| Joint angles over time | [2_angles.png](figures/summary/2_angles.png) |
| PCA variance and loadings | [3_pca.png](figures/summary/3_pca.png) |
| Wavelet transform | [4_wavelet.png](figures/summary/4_wavelet.png) |
| UMAP map and density | [5_umap.png](figures/summary/5_umap.png) |
| Watershed regions and time per region | [6_regions.png](figures/summary/6_regions.png) |

## Results

- The complete pipeline runs locally from raw keypoints to an ethogram.
- 32 keypoints → 22 angles → 13 PCA modes → 325 wavelet features → 2-D map → 12 watershed regions.
- **Region names are not validated.** First interpretations came from still frames only.

## Reproducing

Needs Python 3.11 (the tutorial code needs an older scientific stack). Run from the repository root.

```sh
# 1. Tutorial repository with the demo data and motionmapperpy (ignored by git)
git clone https://github.com/bermanlabemory/unsupervised-behavior-tutorials
cd unsupervised-behavior-tutorials/motionmapperpy
git checkout ffd071d362ef8c3a508e8eabd612639aa433184d
cd ../..

# 2. Environment
python3.11 -m venv .venv311
source .venv311/bin/activate          # Windows: .venv311\Scripts\activate
pip install numpy scipy scikit-learn scikit-image matplotlib pandas tables h5py \
    hdf5storage opencv-python tqdm easydict umap-learn ipykernel

# 3. Pipeline
python 01_method_fly/scripts/step1_clean_angles_pca.py
python 01_method_fly/scripts/step2_wavelet.py
python 01_method_fly/scripts/step3_umap.py
python 01_method_fly/scripts/step3b_map_by_movement.py
python 01_method_fly/scripts/step4_watershed.py
python 01_method_fly/scripts/demo_raw_xy_vs_angles.py
python 01_method_fly/scripts/demo_toy_pca.py

# 4. Summary figures and overview page
python 01_method_fly/scripts/summary_figures.py
python 01_method_fly/scripts/summary_page_deck.py
```

Notes: the demo data must be in `unsupervised-behavior-tutorials/motionmapperpy/data/fly/`. Installing `tables` may need a prebuilt wheel. The wavelet, UMAP and watershed scripts use multiprocessing and are wrapped in `if __name__ == "__main__":`. `intermediate/` is regenerated and not committed. There is no automated test suite.
