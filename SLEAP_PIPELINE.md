# SLEAP pipeline: from video to clean mouse skeletons

Stage 1 of Maria's project. Process the interaction videos with SLEAP and our Python scripts
until every video has a clean male/female skeleton file. Those files are the input for the actual
project: the unsupervised behavior map (MotionMapper, see `README.md`).

Last update: 01.11.2026

---

## START HERE (Windows PC, RTX 4070)

Tick the boxes as you go. Every command is typed in **PowerShell**
(press the Windows key, type `PowerShell`, press Enter).

### A. One-time setup

- [ ] **1. Check the graphics card driver**
  ```
  nvidia-smi
  ```
  You should see a table with "RTX 4070", a *Driver Version* and a *CUDA Version*.
  If the command is not found, install the NVIDIA driver first (nvidia.com/drivers).

- [ ] **2. Install uv** (the tool we used to install SLEAP on the Mac)
  ```
  powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
  ```
  Close and reopen PowerShell, then check: `uv --version`

- [ ] **3. Install SLEAP** (finds the GPU by itself)
  ```
  uv tool install --python 3.13 "sleap[nn]" --torch-backend auto
  ```
  Check that the GPU is found:
  ```
  sleap doctor
  ```
  Look for CUDA / your RTX 4070 in the output. If it says CPU only, stop and ask.

- [ ] **4. Get this repository** (needs Git: git-scm.com; GitHub asks you to sign in, the repo is private)
  ```
  cd $HOME\Desktop
  git clone https://github.com/fdagli01/projektanalyse-bioinformatik.git
  ```

- [ ] **5. Make the work folder** (the same layout as on the Mac)
  ```
  mkdir $HOME\Desktop\Projektanalyse\data\videos, $HOME\Desktop\Projektanalyse\models, $HOME\Desktop\Projektanalyse\results, $HOME\Desktop\Projektanalyse\logs
  ```

- [ ] **6. Copy the model** from Sciebo > `SLEAP label` (only download, never change Sciebo)
  into `Projektanalyse\models\`:
  - `without_tail_and_paws\` (stage 1, finds each mouse)
  - `without_tail_and_paws-1\` (stage 2, finds the keypoints)

- [ ] **7. Remember SLEAP's Python** (it has sleap_io, opencv, scipy, matplotlib; our scripts need it)
  ```
  $PY = "$(uv tool dir)\sleap\Scripts\python.exe"
  & $PY --version
  ```
  `$PY` is forgotten when PowerShell is closed. Type the first line again in every new window.

- [ ] **8. Speed test on 300 frames** (with the video we already know)
  Copy `20241007_m706black_f779agouti_wt_estrus_videoTop.avi` from Sciebo into `data\videos\`, then:
  ```
  cd $HOME\Desktop\Projektanalyse
  sleap-track data\videos\20241007_m706black_f779agouti_wt_estrus_videoTop.avi -m models\without_tail_and_paws -m models\without_tail_and_paws-1 --tracking.tracker simple --tracking.max_tracking 1 --tracking.max_tracks 2 --frames 3000-3299 -o results\speed_test.slp
  ```
  Write down the frames per second. The Mac did 13.7 frames/s, so a 30-minute video took hours.

### B. This week's work (see "Plan for this week" below)

- [ ] Choose 3 test videos (not training videos!) and copy them into `data\videos\`
- [ ] Run the full pipeline on each (commands under "How to run")
- [ ] Quality check: look at 50 random frames per video (script still to be written)
- [ ] Write down the numbers in the "Results" table below

---

## The pipeline

```
video (.avi)
  |
  v  sleap-track ..................... keypoints of both mice in every frame  -> predictions_raw.slp
  |
  v  sleap_assign_identity.py ........ which mouse is male, which female       -> predictions_male_female.slp
  |
  v  sleap_clean_predictions.py ...... remove wrong points, fill short gaps    -> NAME_clean.npz  (MotionMapper input)
  |                                                                               NAME_report.txt, NAME_flags.csv, NAME_qc.png
  v  MotionMapper (stage 2) .......... behavior map without labels

For checking by eye:
     sleap_raw_data_plots.py ......... 4 plots of the raw data quality
     sleap_draw_skeleton_video.py .... video with the skeleton drawn on top (male blue, female orange)
```

## What each script does

All scripts are in `calisma/`. Run them with SLEAP's Python (`PY`, see step 7 above; on the Mac it is
`~/.local/share/uv/tools/sleap/bin/python`).

### `sleap_assign_identity.py`: who is who?
SLEAP finds two mice but does not know which is the male. Its own track numbers get mixed up
(the full test video got 262 of them). This script ignores them and uses **fur colour**. For every frame:
1. If SLEAP found 3-4 mice (one counted twice, or a shadow), keep the 2 most reliable:
   the highest score, then the best one whose body centre is at least 40 px away from it.
2. Measure how dark the fur is around the 4 back points (neck, spine1, spine2, spine3).
3. The darker mouse is the black one. `--male black` or `--male agouti` says which one is the male
   (read it from the folder name: `m706black_f779agouti` means the male is black).
4. Frames with only 1 mouse get no identity.

It prints how many frames were assigned and the grey-level gap between the mice (a small gap means
an unsure decision). **The new version has not been run yet.**

### `sleap_clean_predictions.py`: fix wrong keypoints
A keypoint is removed when:
- the model's confidence is below 0.3,
- it is more than 40 px away from its own smoothed path (a jump; a mouse cannot move that far in 0.04 s),
- the nose to tail base length is under 0.5x or over 1.5x that mouse's normal length (broken skeleton).

Then gaps of up to 5 frames (0.2 s) are filled by interpolation and the result is lightly smoothed.
Frames that are still bad are listed with the reason; contact (body centres closer than 120 px) is marked.
Thresholds were chosen from 12 seconds only and must be checked on full videos.

### `sleap_raw_data_plots.py`: raw data at a glance
4 panels: confidence per keypoint, largest jumps, body length over time, distance between the mice.

### `sleap_draw_skeleton_video.py`: skeleton video
Draws the skeleton and the male/female name on every frame. Use `--scale 0.5` for a smaller file.

## How to run (one video)

Replace `NAME` with the video name. Mac: `PY` = `~/.local/share/uv/tools/sleap/bin/python`.
Windows: `& $PY`. Type each command as one line.

```
sleap-track data/videos/NAME_videoTop.avi -m models/without_tail_and_paws -m models/without_tail_and_paws-1 --tracking.tracker simple --tracking.max_tracking 1 --tracking.max_tracks 2 -o results/NAME/predictions_raw.slp

PY calisma/sleap_assign_identity.py results/NAME/predictions_raw.slp data/videos/NAME_videoTop.avi results/NAME/predictions_male_female.slp --male black

PY calisma/sleap_raw_data_plots.py results/NAME/predictions_male_female.slp results/NAME/raw_data_plots.png

PY calisma/sleap_clean_predictions.py results/NAME/predictions_male_female.slp results/NAME/cleaning

PY calisma/sleap_draw_skeleton_video.py results/NAME/predictions_male_female.slp data/videos/NAME_videoTop.avi results/NAME/skeleton.mp4 --scale 0.5
```

- `--tracking.max_tracking 1` is required; without it the number of tracks is not limited to 2.
- `--frames 3000-3299` processes only a range (for quick tests).
- The `.slp` file is written only at the end; do not run two predictions at the same time.
- Paths are relative to the repo for the scripts (`calisma/...`); keep data and results in the work folder.

## Data and model (not in git)

- Videos: Sciebo `InteractionVideos_rawData/initialInteractionVideos` (2024) and
  `secondInteractionVideos` (65 experiments, 113.5 GB). Use the `_videoTop.avi` file.
  1280 x 1024 greyscale, 25 frames/s, about 45,000 frames = 30 min. The first ~2 minutes are set-up.
- Folder name: `20241007_m706black_f779agouti_wt_estrus` = date, male, female, genotype, female's state.
  The male is usually black, but not always (e.g. `m1600agouti_f1553black`).
- Model: Sciebo `SLEAP label`, trained by Rebekka Esslen, SLEAP 1.5+, top-down,
  12 keypoints (nose, neck, 2 ears, 2 shoulders, spine1-3, 2 hips, tail base; no tail tip, no paws).
- **Never test on the 10 training videos:** 20241008_m811, 20241111_m778, 20241115_m843, 20241204_m846,
  20250113_m849, 20250114_m941, 20250115_m942, 20250409_m1069, 20250410_m1059, 20250610_m1108.

## Status

- [x] Data inspected on Sciebo, model found, SLEAP running on the Mac
- [x] 300-frame test (frames 3000-3299 of the 20241007_m706 video)
- [x] Scripts: identity, cleaning, raw plots, skeleton video
- [x] Full video prediction (45,002 frames): 2 mice in 94% of frames, 1 mouse in 1,202, 3-4 mice in 1,288
- [x] Identity script fixed for 3-4 mice and 1-mouse frames (not run yet)
- [ ] Identity + cleaning on the full video, read the report
- [ ] Measure how well the scripts work (quality check)
- [ ] SLEAP on the Windows PC (RTX 4070)
- [ ] Batch script for many videos
- [ ] Solve the contact problem
- [ ] MotionMapper on the clean data

Results of the 300-frame test: 2.7% of keypoints removed, jumps > 50 px went from 25 to 1,
87.7% clean frames, 37 doubtful frames (mostly during contact).

## Plan for this week

Goal: process a few new videos **and measure how well the scripts work**, so we can tell Maria
with numbers how reliable the data is. Not all 65 videos yet.

1. **Read and run the identity script** on the full 20241007_m706 video, then cleaning; read the report together.
2. **Quality check** (like a factory inspector who checks random samples, not every product):
   - Choose 3 different videos: one with a black male, one with an agouti male, one from 2025.
   - Run the pipeline on each.
   - A new script picks 50 random frames per video (half with the mice apart, half in contact)
     and draws them with skeleton and male/female label. **To be written.**
   - For each frame, answer: is the label on the right mouse? Are the points on the body?
   - Also read the model's own accuracy files (`metrics.*.npz`, `labels_gt/pr.val.0.slp` in the model folders).
3. **Windows PC**: setup (section A above), speed test.
4. **Batch script** (to be written): runs the 3 steps for every video folder, reads the male's colour
   from the folder name, skips training videos and finished videos, writes one summary table.
5. **Summary for Maria**: how many videos, identity % correct, % clean frames, where the problems are.

What the result tells us:
- everything good -> process all videos
- only contact frames bad -> label 50-100 contact frames and fine-tune the model, or leave contact out
- agouti-male video bad -> fix the identity script

### Results (fill in)

| Video | Male | Prediction time | Identity correct (apart) | Identity correct (contact) | Points on body | Clean frames |
|---|---|---|---|---|---|---|
| 20241007_m706black_f779agouti | black | | /25 | /25 | /50 | |
| | agouti | | /25 | /25 | /50 | |
| | | | /25 | /25 | /50 | |

## Open questions for Maria

1. Which videos should be analysed: all 65, or a subset? Top camera only, or front as well?
2. Are behaviors during contact (mounting, sniffing) important? This decides whether we fine-tune.
3. When does the actual experiment start in each video (female put in)? Is it written down somewhere?
4. Are there hand-annotated behaviors for any video, to check the MotionMapper clusters later?
5. Is the male's colour in the folder name always reliable?
6. Is there a GPU server at the university, or do we use the RTX 4070?

## Literature for our problems

P1 = keypoints break during contact, P2 = identity mixed up, P3 = unsupervised analysis of two mice.

| Paper | Helps with | Idea for us |
|---|---|---|
| Lauer 2022, multi-animal DeepLabCut (Nat Methods) | P1, P2 | label contact frames on purpose and add them to training |
| Azechi & Takahashi 2025, vmTracking (PLOS Biol) | P1, P2 | heavy backup plan for crowding / contact |
| sleap-nn supervised ID (`multi_class_topdown`) | P2 | model learns male/female directly; best fit for identity |
| DIPLOMAT | P1, P2 | keeps identity consistent across frames |
| Ritter 2025 (Front Behav Neurosci) | P3 | SLEAP 12 keypoints + Keypoint-MoSeq on mouse pairs; very similar set-up |
| LISBET (arXiv 2311.04069) | P3 | social motifs differ for male vs female partner |
| Klibaite 2025 (Cell) | P3 | template for a social behavior map (rats) |
| Segalin 2021, MARS (eLife) | P2, P3 | supervised comparison; black vs white mice |

Links and longer notes are in `PROJECT_NOTES_EN.txt` / `PROJECT_NOTES_TR.txt` in the work folder
(`~/Desktop/Projektanalyse` on the Mac).
