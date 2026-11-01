# Literature for our problems

P1 = keypoints break during contact, P2 = identity mixed up, P3 = unsupervised analysis of two mice.

| Paper | Helps with | Idea for us |
|---|---|---|
| Lauer 2022, multi-animal DeepLabCut (Nat Methods) | P1, P2 | label contact frames on purpose and add them to training |
| Azechi & Takahashi 2025, vmTracking (PLOS Biol) | P1, P2 | heavy backup plan for crowding / contact |
| sleap-nn supervised ID (`multi_class_topdown`) | P2 | the model learns male/female directly; best fit for identity |
| DIPLOMAT | P1, P2 | keeps identity consistent across frames |
| Ritter 2025 (Front Behav Neurosci) | P3 | SLEAP 12 keypoints + Keypoint-MoSeq on mouse pairs; very similar set-up |
| LISBET (arXiv 2311.04069) | P3 | social motifs differ for male vs female partner |
| Klibaite 2025 (Cell) | P3 | template for a social behaviour map (rats) |
| Segalin 2021, MARS (eLife) | P2, P3 | supervised comparison; black vs white mice |

The method itself: Berman lab, MotionMapper and [unsupervised-behavior-tutorials](https://github.com/bermanlabemory/unsupervised-behavior-tutorials).
