# Stage 5 – MotionMapper on two mice ⏳

Apply the method from stage 1 to the clean mouse skeletons from stage 2, to get a behaviour map of male–female interaction.

**Input:** `cleaning_clean.npz` per video (positions of 12 keypoints for the male and the female, per frame).
**Output:** a UMAP behaviour map, watershed regions and an ethogram per video.

## What changes compared with the fly

| | Fly (stage 1) | Mice (this stage) |
|---|---|---|
| Animals | 1 | 2 (male and female) |
| Keypoints | 32 | 12 per animal |
| Frame rate | 100 fps | 25 fps (wavelet frequencies must stay below 12.5 Hz) |
| Features | joint angles of one animal | angles of each animal **plus** features between them: distance, relative orientation, nose-to-body contact |

## Status

- [ ] Decide the features (per animal and between the animals)
- [ ] Run PCA, wavelets, UMAP and watershed on the 3 test videos
- [ ] Run on all videos (after stage 4)
