# Stage 3 – Automated quality check ⏳

Know with numbers how reliable the skeletons from stage 2 are, without watching every frame
(like a factory inspector who checks random samples, not every product).

**Input:** `predictions_male_female.slp` and `cleaning_*` files of a video (stage 2), the video itself, the model folders.
**Output:** a short report per video and a set of sampled frames for review; a go / no-go decision for stage 4.

## Planned checks

| Check | How | Why |
|---|---|---|
| Identity swaps | male and female positions jump into each other's place from one frame to the next | a swap mixes up the two animals' behaviour |
| Unsure identity | frames where the fur grey-level gap between the mice is small | the colour decision may be wrong there |
| Model accuracy | read `metrics.val.0.npz` and `labels_gt/pr.val.0.slp` in the model folders | how far the model is off on frames a human labelled |
| Sampled review | ~50 frames per video (half with the mice apart, half in contact), drawn with skeleton and label | is the label on the right mouse? are the points on the body? |

## Status

- [ ] Write the script
- [ ] Run it on the 3 test videos and fill in the results table in [02_pose_sleap/README.md](../02_pose_sleap/README.md)
