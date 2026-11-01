# Stage 2 – Pose estimation with SLEAP 🔄

Turn every interaction video into a clean skeleton file with a correct male/female label.
These files are the input for the behaviour map (stage 5).

Last update: 2026-11-01

## Pipeline

```
videoTop_<experiment>.avi
  │
  ▼  sleap-track ................... keypoints of both mice in every frame   → predictions_raw.slp
  │
  ▼  assign_identity.py ............ which mouse is male, which is female     → predictions_male_female.slp
  │
  ▼  clean_predictions.py .......... remove wrong points, fill short gaps     → cleaning_clean.npz  (stage 5 input)
                                                                                cleaning_report.txt, cleaning_flags.csv, cleaning_qc.png
For checking by eye:
     raw_data_plots.py ............. 4 plots of the raw data quality          → raw_data_plots.png
     draw_skeleton_video.py ........ the video with the skeleton drawn on it  → skeleton.mp4
```

## Scripts (`scripts/`)

All scripts run with SLEAP's own Python, which has `sleap_io`, OpenCV, SciPy and Matplotlib.

### `assign_identity.py` – who is who?
SLEAP finds two mice but does not know which one is the male, and its own track numbers get mixed up.
This script ignores them and uses **fur colour**. For every frame:
1. If SLEAP found 3–4 mice (one counted twice, or a shadow), keep the 2 most reliable:
   the highest score, then the best one whose body centre is at least 40 px away from it.
2. Measure how dark the fur is around the 4 back points (neck, spine1, spine2, spine3).
3. The darker mouse is the black one. `--male black` or `--male agouti` says which one is the male
   (read it from the folder name: `m1313black_f1603agouti` means the male is black).
4. Frames with only 1 mouse get no identity.

It prints how many frames were assigned and the grey-level gap between the mice (a small gap means an unsure decision).

### `clean_predictions.py` – fix wrong keypoints
A keypoint is removed when:
- the model's confidence is below **0.3**,
- it is more than **40 px** away from its own smoothed path (a jump; a mouse cannot move that far in 0.04 s),
- the nose to tail base length is under **0.5×** or over **1.5×** that mouse's normal length (broken skeleton).

Then gaps of up to **5 frames** (0.2 s) are filled by interpolation and the result is lightly smoothed.
Frames that are still bad are listed with the reason; contact (body centres closer than **120 px**) is marked.
The thresholds were chosen from 12 seconds of video only and must be checked on full videos.

### `raw_data_plots.py` – raw data at a glance
4 panels: confidence per keypoint, largest jumps, body length over time, distance between the mice.

### `draw_skeleton_video.py` – skeleton video
Draws the skeleton and the male/female name on every frame (male blue, female orange). `--scale 0.5` gives a smaller file.

## How to run (Windows, PowerShell)

Work in the work folder (`Projektanalyse\`, next to this repository). Set these once per PowerShell window:

```powershell
cd $HOME\Desktop\Projektanalyse
$PY   = "$(uv tool dir)\sleap\Scripts\python.exe"
$REPO = "Notebooks\02_pose_sleap\scripts"
$N    = "20260320_m1313black_f1603agouti_wt_estrus"     # experiment name
```

Then, one command per line:

```powershell
sleap-track data\videos\videoTop_$N.avi -m models\without_tail_and_paws -m models\without_tail_and_paws-1 --tracking.tracker simple --tracking.max_tracking 1 --tracking.max_tracks 2 -o results\$N\predictions_raw.slp

& $PY $REPO\assign_identity.py results\$N\predictions_raw.slp data\videos\videoTop_$N.avi results\$N\predictions_male_female.slp --male black

& $PY $REPO\raw_data_plots.py results\$N\predictions_male_female.slp results\$N\raw_data_plots.png

& $PY $REPO\clean_predictions.py results\$N\predictions_male_female.slp results\$N\cleaning

& $PY $REPO\draw_skeleton_video.py results\$N\predictions_male_female.slp data\videos\videoTop_$N.avi results\$N\skeleton.mp4 --scale 0.5
```

- `--tracking.max_tracking 1` is required; without it the number of tracks is not limited to 2.
- `--frames 3000-3299` processes only a range (for quick tests).
- The `.slp` file is written only at the very end. Never run two predictions at the same time.

## Setup (once)

1. Check the NVIDIA driver: `nvidia-smi`.
2. Install uv: `powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"`.
3. Install SLEAP: `uv tool install --python 3.13 "sleap[nn]" --torch-backend auto`, then `sleap doctor` must show CUDA.
4. Copy the model from Sciebo > `SLEAP label` into `Projektanalyse\models\` (`without_tail_and_paws\` and `without_tail_and_paws-1\`).

Current setup: SLEAP 1.6.6, sleap-nn 0.3.5, Python 3.13, PyTorch 2.11 + CUDA 12.8, RTX 4070 Laptop GPU.
Speed: ~32–40 frames/s, about 22 minutes per 30-minute video. The limit is CPU preprocessing and tracking, not video decoding.

## Data and model

- **Videos:** Sciebo `InteractionVideos_rawData/initialInteractionVideos` (2024) and `secondInteractionVideos`
  (65 experiments, 113.5 GB). We use the top camera (`videoTop_<experiment>.avi`).
  1280 × 1024 greyscale, 25 frames/s, about 45,000 frames = 30 min. The first ~2 minutes are set-up.
- **Experiment name:** `20260320_m1313black_f1603agouti_wt_estrus` = date, male (number + fur colour),
  female (number + fur colour), genotype, female's cycle state. The male is usually black, but not always.
- **Model:** Sciebo `SLEAP label`, trained by Rebekka Esslen, top-down (centroid + centred instance),
  12 keypoints: nose, neck, 2 ears, 2 shoulders, spine1–3, 2 hips, tail base (no tail tip, no paws).
- **Never test on the 10 training videos:** 20241008_m811, 20241111_m778, 20241115_m843, 20241204_m846,
  20250113_m849, 20250114_m941, 20250115_m942, 20250409_m1069, 20250410_m1059, 20250610_m1108.

## Status

- [x] Scripts: identity, cleaning, raw plots, skeleton video
- [x] First tests on the Mac: 300 frames and one full video (20241007_m706); 2 mice found in 94 % of frames
- [x] SLEAP on the Windows PC
- [ ] SLEAP predictions for the 3 test videos (running)
- [ ] Identity and cleaning on full videos, read the reports
- [ ] Solve the contact problem (keypoints break when the mice touch)

Results of the 300-frame test: 2.7 % of keypoints removed, jumps > 50 px went from 25 to 1,
87.7 % clean frames, 37 doubtful frames (mostly during contact).

### Results of the 3 test videos (fill in)

| Video | Male | Prediction time | Identity correct (apart) | Identity correct (contact) | Points on body | Clean frames |
|---|---|---|---|---|---|---|
| 20260320_m1313black_f1603agouti | black | 21 min 41 s (inference) | /25 | /25 | /50 | |
| 20260322_m1599agouti_f1550black | agouti | | /25 | /25 | /50 | |
| 20260322_m1600agouti_f1553black | agouti | | /25 | /25 | /50 | |

What the result tells us:
- everything good → process all videos (stage 4)
- only contact frames bad → label 50–100 contact frames and fine-tune the model, or leave contact out
- agouti-male videos bad → fix the identity script
