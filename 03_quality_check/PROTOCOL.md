# SLEAP Pose Annotation Protocol

**Version 1.0 · 2026-11-01**

This protocol defines how the sampled frames of a SLEAP prediction are judged by eye. It is the reference
for every answer in the review page. Each record stores the protocol version it was made with; if the rules
change, the version number changes and records of different versions are analysed separately.

## 1. Purpose

Estimate, with confidence intervals, how reliable SLEAP's raw output is for one video:

1. Are the mice detected correctly?
2. Are the keypoints placed correctly, per body region?
3. Are the skeletons whole, each on one mouse?
4. Can the fur colour tell the black mouse from the agouti mouse (the basis of the identity script)?

The answers are also the reference ("ground truth") for the automatic checks of stage 3.

## 2. Material

- **Frames:** 80 frames per video, chosen by `scripts/sample_frames.py` with a fixed seed, in 4 strata
  defined from SLEAP's output: *apart* (body centres > 250 px, 30 frames), *contact* (< 120 px, 30),
  *single* (only 1 animal found, 10), *random* (10). The first 3,000 frames (2 min set-up) are excluded.
- **Repeats:** 8 of the 80 frames (2 per stratum) are shown a second time, at least 20 items later,
  to measure consistency. They are not marked.
- **Context:** for every frame the 5 frames before and after are available (0.2 s each way).
- **Display:** SLEAP skeletons are drawn as **A (red)** and **B (cyan)**. A and B are detections, not male/female.

## 3. Blinding

While an item is being answered the page hides: the frame number, SLEAP's stratum, the distance between
the animals, the scores and the measured grey levels. They are shown after the item is complete.
The two annotators work independently and do not discuss items until both records are exported.

## 4. Body regions

| Region | Keypoints |
|---|---|
| **Head** | nose, ear left, ear right, neck |
| **Body** | shoulder left, shoulder right, spine1, spine2 |
| **Rear** | spine3, hip left, hip right, tail base |

## 5. Questions and decision rules

Answer for the **centre frame**. Use the context frames only to understand what is happening.

### Q1 Scene – what do you see?
| Answer | Rule |
|---|---|
| **Apart** | two mice, clearly separate (fur not touching) |
| **Touching** | two mice whose bodies touch, both bodies mostly visible |
| **Overlapping** | one mouse hides a large part of the other (e.g. mounting, crawling over) |
| **One mouse visible** | only one mouse can be seen at all |
| **Unusable** | the frame cannot be judged (blur, mice out of view). The other questions are then skipped. |

### Q2 Detection – for each skeleton (A, B)
| Answer | Rule |
|---|---|
| **On a mouse** | most of its points lie on one real mouse, and no other skeleton is on that same mouse |
| **Duplicate** | it lies on a mouse that already has another skeleton |
| **Ghost** | it lies on no mouse (bedding, wall, reflection) |

### Q3 Missed mouse
**Yes** if a visible mouse has no skeleton at all, otherwise **No**.

### Q4 Keypoints – for each skeleton that is *on a mouse*, per region
| Answer | Rule |
|---|---|
| **Correct** | every drawn point of the region is on the right body part, within about half an ear width |
| **Wrong** | at least one drawn point of the region is clearly on another body part, off the body, or on the other mouse |
| **Not visible** | the body part is hidden, so it cannot be judged, *or* no point of the region is drawn |

Missing points (not drawn) are **not** errors; a region with all its points missing is *Not visible*.
The button **All correct** sets all three regions to *Correct* and is only a shortcut.

### Q5 Integrity – for each skeleton that is *on a mouse*
**Whole** if the skeleton has the shape of one mouse. **Broken** if it is stretched, folded, or connects points
of both mice. Check the context frames: a skeleton that jumps between mice there is *Broken* in the centre frame
only if it is already wrong in the centre frame.

### Q6 Darker mouse (only when two skeletons are *on a mouse*)
Compare the fur of the **back** (neck to tail base), not the head or tail. Answer **A**, **B** or **Can't tell**,
and how sure you are: **Sure** / **Unsure**. Use *Can't tell* when one back is hidden.

### Q7 Overall confidence
**Sure** or **Unsure** about this item as a whole. *Unsure* items are kept, but analysed separately.

## 6. Procedure

1. Read this protocol completely before the first item.
2. Open `index.html`, enter your initials, confirm the protocol version.
3. Answer all items in the given order. A pause is allowed at any time; answers are saved in the browser.
4. At the end, **Export record (JSON)** and send the file. The JSON file is the official record; the CSV is a convenience copy.
5. Do not change answers after seeing the revealed values unless the answer was a mis-click; every change is logged.

## 7. Analysis

`scripts/analyze_reviews.py` reads one or more exported records and reports, per stratum and per scene:
proportions with 95 % Wilson confidence intervals, intra-rater agreement on the repeated items,
inter-rater agreement (percent agreement and Cohen's kappa) when two records are given,
and the agreement between the annotators' darker mouse and the identity script's grey-level decision.

## 8. Version history

| Version | Date | Change |
|---|---|---|
| 0 (pilot) | 2026-11-01 | 4 questions per frame, no blinding of SLEAP's stratum; used to test the questions |
| 1.0 | 2026-11-01 | regions, per-skeleton questions, scene, blinding, repeats, context frames, audit log |
