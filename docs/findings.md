# Findings so far

Short notes on what we have learned, newest first. Details and numbers: [03_quality_check/results](../03_quality_check/results/README.md).

## 2026-11-06 – SLEAP is good when the mice are apart, weak in contact

Based on video m1313, 80 frames, judged by two people (MFD, ZT).

**What we found**
1. **Mice apart: SLEAP is reliable.** About 87–97 % of body regions are in the right place.
2. **Mice in contact: SLEAP gets worse.** About 80 % of regions are correct, and 20–37 % of the skeletons are
   broken (stretched, or joining points of both mice).
3. **Overlapping mice: SLEAP loses one mouse.** In the frames where it found only one mouse, the second one was there.
4. **The male/female rule works.** The darker mouse is the black one: both annotators agree with the script in 99–100 %.
5. **The two annotators mostly agree** (scene κ = 0.76, darker mouse κ = 0.84). One rule was unclear: does an
   almost fully hidden mouse count as visible?

**First run of the cleaning script (unchanged thresholds)**
- It marks 37 % of all frames as doubtful: too many to check by hand.
- It finds only 40–47 % of the skeletons the annotators judged broken (it looks at nose–tail length only).
- In frames with one mouse it drops that mouse too (no identity → skipped).

**Why it matters**
Interaction happens mostly in contact, which is exactly where the poses are weakest.
The behaviour map (stage 5) will only be as good as the contact frames.

**Decision needed before more work** (see [open_questions.md](open_questions.md), question 2)
- Retrain SLEAP with more contact frames, or repair the contact frames afterwards with the cleaning script?
- Ask Maria first. Until then: finish m1599 and m1600 (second annotator), do not change the cleaning script.

**Limits:** one video, 80 frames, wide confidence intervals (often ± 10 points).
