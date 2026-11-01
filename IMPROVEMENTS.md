# Improvements

Ideas for the SLEAP → MotionMapper pipeline. Newest first in each section.

## Open
- [ ] (2026-11-01) **Automated QC script** — detect identity swaps between male and female,
      flag frames where the fur grey-level difference is small, read model metrics
      (metrics.val.0.npz), and sample 15–20 frames rendered with skeleton for manual review.
- [ ] (2026-11-01) **Batch script for all videos** — skip the 10 training videos and finished
      ones, read the male's fur colour from the folder name, write a summary table.
- [ ] (2026-11-01) **Review cleaning thresholds** after looking at raw predictions
      (score 0.3, spike 40 px, gap fill 5 frames, body length 0.5–1.5×).
- [ ] (2026-11-01) **Fill in the results table** in SLEAP_PIPELINE.md for the 3 test videos.
- [ ] (2026-11-01) **Ask Maria:** access to a GPU server / HPC for the big batch?
      Should the front camera be used?

## Done
- [ ] (2026-11-01) Run SLEAP predictions on 3 test videos (m1313, m1599, m1600) — in progress.

## Dropped
- (2026-11-01) Decode video on the GPU (NVDEC) — decoding is only ~15% of runtime,
  not worth the setup effort.
