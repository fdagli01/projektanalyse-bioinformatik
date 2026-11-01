# Stage 4 – Batch processing ⏳

Run stages 2 and 3 on every video, once the 3 test videos show that the pipeline is reliable.

**Input:** all experiment folders from Sciebo (65 in `secondInteractionVideos`, plus `initialInteractionVideos`).
**Output:** clean skeletons for every video and one summary table (one row per video).

## Planned behaviour of the batch script

- Skip the 10 training videos (list in [02_pose_sleap/README.md](../02_pose_sleap/README.md#data-and-model)) and videos that are already finished.
- Read the male's fur colour from the folder name (`m1313black_f1603agouti` → `--male black`).
- Run one prediction at a time, then identity, cleaning and the quality check.
- Write a summary table: video, frames, prediction time, % frames with 2 mice, % clean frames, identity warnings.

## Where to run it

On this PC one video takes about 22 minutes, so 65 videos take about a day of computing.
A university GPU server or HPC cluster would be faster and keeps the laptop free (open question for the research group).

## Status

- [ ] Write the script
- [ ] Decide where to run it
- [ ] Run and check the summary table
