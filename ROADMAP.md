# Roadmap

All stages of the project, in order. Each stage ends with a clear result that the next stage needs.
Ideas that are not yet part of a stage go to [IMPROVEMENTS.md](IMPROVEMENTS.md).

Last update: 2026-11-01

---

## Stage 1 – Learn the method on fly data ✅

**Goal:** understand every step of MotionMapper by re-implementing it on the public fruit-fly demo data.
**Result:** the full pipeline runs from raw keypoints to an ethogram; figures for every step.
**Folder:** [01_method_fly](01_method_fly/)

- [x] Cleaning, joint angles, PCA
- [x] Wavelet features
- [x] UMAP behaviour map
- [x] Watershed regions and ethogram
- [x] Summary figures and overview page
- [ ] Name the fly regions by watching example clips (optional; the method is understood)
- [ ] Regenerate the working figures with English labels (needs the tutorial repository)

## Stage 2 – Pose estimation with SLEAP 🔄

**Goal:** every mouse video becomes a clean skeleton file with a correct male/female label.
**Result:** `<experiment>_clean.npz` per video, the input for stage 5.
**Folder:** [02_pose_sleap](02_pose_sleap/)

- [x] SLEAP and the model running on the Windows PC (RTX 4070, ~35 frames/s, ~22 min per video)
- [x] Scripts: identity, raw data plots, cleaning, skeleton video
- [ ] SLEAP predictions for 3 test videos (m1313 black male, m1599 and m1600 agouti male)
- [ ] Look at the raw predictions together, then decide the next steps
- [ ] Identity on the 3 test videos
- [ ] Choose the cleaning thresholds from full videos (so far from 12 s only), then clean
- [ ] Fill in the results table in the stage 2 README

## Stage 3 – Automated quality check ⏳

**Goal:** know with numbers how reliable the skeletons are, without watching every frame.
**Result:** a script and a short report per video; a go / no-go decision for the batch.
**Folder:** [03_quality_check](03_quality_check/)

- [ ] Detect identity swaps between male and female
- [ ] Flag frames where the fur grey-level difference is small (unsure identity)
- [ ] Read the model's own accuracy (`metrics.val.0.npz`, `labels_gt/pr.val.0.slp`)
- [ ] Sample frames (half apart, half in contact), draw them with skeleton and label for review
- [ ] Review the samples of the 3 test videos and report to the research group

## Stage 4 – Batch processing ⏳

**Goal:** run stages 2–3 on all videos.
**Result:** clean skeletons for every video and one summary table.
**Folder:** [04_batch](04_batch/)

- [ ] Batch script: skip training and finished videos, read the male's fur colour from the folder name
- [ ] Decide where to run it (this PC: ~24 h for 65 videos; university GPU server / HPC?)
- [ ] Run and check the summary table

## Stage 5 – MotionMapper on two mice ⏳

**Goal:** a behaviour map of male–female interaction.
**Result:** UMAP map, watershed regions and ethograms for the mouse data.
**Folder:** [05_motionmapper_mouse](05_motionmapper_mouse/)

- [ ] Adapt the features to mice: 12 keypoints per animal, egocentric angles
- [ ] Add features between the animals (distance, relative orientation, nose-to-body contact)
- [ ] Run wavelets, UMAP and watershed on all clean videos

## Stage 6 – Validation ⏳

**Goal:** turn map regions into named, trustworthy behaviours.
**Result:** a list of behaviours with example clips, compared with any existing manual labels.
**Folder:** [06_validation](06_validation/)

- [ ] Watch example clips per region and name them
- [ ] Compare with hand-annotated behaviour, if the research group has any
- [ ] Compare groups (e.g. female cycle state: estrus vs diestrus)

---

Open questions for the research group: [docs/open_questions.md](docs/open_questions.md).
