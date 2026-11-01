# Projektanalyse Bioinformatik: Unsupervised Behaviour Mapping

**A university data-science project (Uni Bonn) on discovering mouse behaviour from video without manual labels.**

The goal is to categorise male–female mouse interaction behaviour directly from pose-tracking data, so future studies do not depend on hand-labelled behaviour. The method follows the MotionMapper approach of the Berman lab ([unsupervised-behavior-tutorials](https://github.com/bermanlabemory/unsupervised-behavior-tutorials)).

![Stage 1 overview: from video to behaviour map](01_method_fly/figures/working/21_overview_deck_blue.png)

## Research question

Can recurring, interpretable behaviours be found directly in the movement of tracked body parts, without predefined categories, and can this be transferred to two-animal mouse recordings?

## Stages

The project is split into six stages. Each stage has its own folder with a `README.md` (goal, input, output, how to run, status). The full plan with next steps is in [ROADMAP.md](ROADMAP.md).

| # | Stage | Folder | Status |
|---|---|---|---|
| 1 | Learn the MotionMapper method on fly demo data | [01_method_fly](01_method_fly/) | ✅ done |
| 2 | Pose estimation: mouse video → male/female skeletons (SLEAP) | [02_pose_sleap](02_pose_sleap/) | 🔄 in progress |
| 3 | Automated quality check of the skeletons | [03_quality_check](03_quality_check/) | ⏳ planned |
| 4 | Batch processing of all videos | [04_batch](04_batch/) | ⏳ planned |
| 5 | MotionMapper on two interacting mice | [05_motionmapper_mouse](05_motionmapper_mouse/) | ⏳ planned |
| 6 | Validation: name the behaviours, check with the research group | [06_validation](06_validation/) | ⏳ planned |

```
video ──► SLEAP keypoints ──► male / female identity ──► cleaning ──► quality check ──► MotionMapper ──► named behaviours
          └──────────────── stage 2 ────────────────┘                 stage 3          stage 5         stage 6
                                         (stage 4 runs stages 2–3 on every video)
```

## Repository structure

```
README.md                  this page
ROADMAP.md                 all stages: goal, status, next steps
IMPROVEMENTS.md            ideas and decisions (open / done / dropped)
docs/
  literature.md            papers that help with our problems
  open_questions.md        questions for the research group
01_method_fly/             stage 1: scripts/ and figures/
02_pose_sleap/             stage 2: scripts/ and the full SLEAP guide (README.md)
03_quality_check/          stage 3 (README only so far)
04_batch/                  stage 4 (README only so far)
05_motionmapper_mouse/     stage 5 (README only so far)
06_validation/             stage 6 (README only so far)
```

## Data (not in git)

Videos, the SLEAP model and all SLEAP results are large and stay outside the repository, in the work folder next to it:

```
Projektanalyse/
  Notebooks/          this repository
  data/videos/        top-camera videos used by the pipeline (videoTop_<experiment>.avi)
  data/raw/           original downloads from Sciebo (front camera)
  data/labels/        the training labels of the SLEAP model (.slp)
  models/             the trained SLEAP model (two stages)
  results/<experiment>/  SLEAP output per video
  logs/               run logs
```

Source: the research group's Sciebo share (download only, never change anything there). The 10 videos used to train the SLEAP model must never be used for testing; the list is in [02_pose_sleap/README.md](02_pose_sleap/README.md#data-and-model).

## Acknowledgements

The pipeline and demo data are based on the Berman lab's MotionMapper and [unsupervised-behavior-tutorials](https://github.com/bermanlabemory/unsupervised-behavior-tutorials). The SLEAP model was trained by Rebekka Esslen.
