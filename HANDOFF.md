# Handoff: Projektanalyse Bioinformatik (mouse behavior, unsupervised)

Read this first in a new Claude session, then read `handoff/stepwise-teaching.md` and `handoff/mouse-interaction-project.md`.

## Project
- User (Turkish speaker) joins a project led by Maria Royo: automatically categorize mouse behavior from video (especially male-female interaction) **without manual labels**, to speed up future research.
- Method template: Berman Lab MotionMapper tutorials (https://github.com/bermanlabemory/unsupervised-behavior-tutorials). SLEAP for pose estimation. Two cameras (top + side).
- Data from Maria: some videos raw (need SLEAP), some already processed. Dataset/labels not confirmed yet.
- Next meeting: 27.10 (questions are on the last Canva slide).

## How to teach the user (important)
- One small step per message, then stop. The user asks questions and says "devam" to continue. Simple language, everyday analogies, little math, small simulations/figures. Answer in Turkish unless asked for English (slides are English).

## State
- Notebook 01 (fly demo data) fully run locally, steps: data -> 22 joint angles (egocentric) -> PCA (13 modes, 95%) -> Morlet wavelet (13x25=325 features) -> UMAP map -> watershed (12 regions) -> ethogram. Region names were only guesses from still frames, not verified.
- Teaching so far: steps 1-3 explained (PCA explained in depth); next is the wavelet step again, then UMAP, watershed, naming regions by watching clips.
- Later: notebooks 02 (transitions), 04 (rat social, closest to the project), 07 (bring your own data, SLEAP loader).
- Canva deck "Living Presentation": 6 pages restyled (light blue #DDEAF8, Poppins); page 4 is the Notebook 01 overview image; last page has the meeting questions.

## Scripts
`calisma/nb01_*.py` produce figures into `calisma/cikti/` (PNGs are committed, `.npy/.npz` are not). Run order: `nb01_adim1_2.py` -> `nb01_adim3_wavelet.py` -> `nb01_adim4_umap.py` -> `nb01_adim5_watershed.py`. English figures: `nb01_ozet_figurler_en.py`, overview page: `nb01_ozet_sayfa_v2.py`.

## Setup on a new machine (Windows or Mac)
1. Clone this repo.
2. Inside it, clone the tutorials and pin the pinned commits:
   ```
   git clone https://github.com/bermanlabemory/unsupervised-behavior-tutorials
   cd unsupervised-behavior-tutorials
   cd motionmapperpy && git checkout ffd071d362ef8c3a508e8eabd612639aa433184d
   ```
   (`motionmapperpy/` is a git checkout inside the tutorials repo; check that the demo fly data is in `motionmapperpy/data/fly/`.)
3. Python 3.11 environment (the tutorials need an older stack):
   ```
   python -m venv .venv311
   .venv311\Scripts\activate        # Windows (macOS: source .venv311/bin/activate)
   pip install numpy scipy scikit-learn scikit-image matplotlib pandas tables h5py hdf5storage opencv-python tqdm easydict umap-learn ipykernel
   ```
   (`tables` needed a prebuilt wheel; on macOS `uv` with Python 3.11 worked.)
4. Scripts using mmpy wavelets need the `if __name__ == "__main__":` guard (already in place) because of multiprocessing.
5. Paths in the scripts are relative to the repo root; they should work on Windows, but check `os.path` usage if something fails.

## Open questions for Maria
fps, camera synchronization/calibration, identity (male/female) tracking, which videos are raw vs. SLEAP-processed (same skeleton?), experiment groups/conditions, existing manual labels.
