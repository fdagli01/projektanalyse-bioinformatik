# Results – how good are the SLEAP poses?

**Status:** video m1313 is done by both annotators (MFD, ZT). m1599 and m1600 follow when the second annotator has
finished them (until then their results stay hidden, so that the second person is not influenced).

## What we wanted to know

Before we build a behaviour map from the SLEAP skeletons, we need to know whether we can trust them:
are the body points in the right place, and does our script tell the male and the female apart correctly?

## What we did

Two people looked at the same 80 frames of video m1313, each on their own, and judged every skeleton with the same
written rules ([PROTOCOL.md](../PROTOCOL.md)). The frames were chosen so that both easy moments (mice apart) and hard
moments (mice touching or on top of each other) are included.

## What we found

**1. When the mice are apart, SLEAP is reliable.**
Almost all body points (about 9 out of 10 or more) sit where they should.

**2. When the mice touch, SLEAP makes more mistakes.**
More points end up in the wrong place, and many skeletons are stretched or connect points of both mice.
This is the most important result, because the interaction between male and female happens mostly in contact.

![SLEAP accuracy: apart vs contact](20260320_m1313black_f1603agouti_wt_estrus/fig1_accuracy_by_stratum.png)
*Each bar is the share of correct body regions or whole skeletons; left = mice apart, middle = in contact.*

**3. When one mouse is on top of the other, SLEAP often sees only one mouse.**
The second mouse is there but gets no skeleton at all.

**4. Telling male and female apart by fur colour works.**
Whenever the annotators could see which mouse was darker, they agreed with the script (practically every time).

**5. The two annotators mostly judge the same way.**
They differ mainly on one question: if a mouse is almost completely hidden under the other, does it count as
"visible"? The rules did not say, so they decided differently (compare the two panels below).

![Scene judgement vs SLEAP](20260320_m1313black_f1603agouti_wt_estrus/fig3_scene_vs_stratum.png)
*Rows: what SLEAP found; columns: what the annotator saw. The "single" row is where the two people disagree.*

## What this means for the project

- The skeletons are good enough for behaviour **when the mice are apart**.
- For **contact**, which matters most for interaction, they have to get better first: either by training SLEAP with
  more contact frames, or by repairing these frames afterwards. This decision is still open (ask Maria).
- The male/female labels can be trusted.

## Next steps

1. Second annotator finishes m1599 and m1600, to see if the same picture appears in all three videos.
2. Agree on the rule for an almost fully hidden mouse.
3. Decide with Maria: retrain SLEAP, or repair contact frames in the cleaning step.

## What we aim for, and what each script is for

**Goal:** a behaviour map of male–female interaction (stage 5), built from skeletons we can trust.
For that, every video needs skeletons with the right male/female label, and the bad frames, especially in contact,
must be found and repaired or left out.

**Scripts that exist**

| Script | Stage | What it is meant to find or do | State |
|---|---|---|---|
| `assign_identity.py` | 2 | Which skeleton is the male and which the female (the darker mouse is the black one) | works on m1313; rule confirmed by both annotators |
| `raw_data_plots.py` | 2 | A first look at the raw poses: confidence, jumps, body length, distance between the mice | runs |
| `clean_predictions.py` | 2 | Bad points (missing, unsure, sudden jumps), broken skeletons; fills short gaps and lists doubtful moments | first run on m1313: flags too much, finds only about half of the broken skeletons |
| `draw_skeleton_video.py` | 2 | A video with the skeletons drawn on, to check by eye | runs |
| `sample_frames.py` | 3 | Picks frames to judge by hand, from easy (apart) to hard (contact, one mouse) | done for the 3 test videos |
| `review_page.html` | 3 | The page where a person judges each skeleton | in use |
| `analyze_reviews.py`, `plot_reviews.py` | 3 | Turn the judgements into numbers and figures: how often SLEAP is right, and whether the two people agree | done for m1313 |

The scripts in `01_method_fly/scripts/` were for learning MotionMapper on fly data (cleaning → angles → PCA →
wavelets → UMAP map → watershed regions); stage 5 will reuse these steps for the mice.

**Scripts still needed**

| Script | What it should find or do |
|---|---|
| better cleaning (stage 2) | skeletons that connect points of both mice; keep the one mouse when SLEAP finds only one; keep male/female consistent over time when the fur difference is small |
| automatic check (stage 3) | the same errors as the manual check, but on every frame, and compared with the manual judgements to show how well it works |
| batch (stage 4) | run everything on all videos and write one summary table |
| MotionMapper for mice (stage 5) | the behaviour map, with features of each mouse and between the two (distance, orientation, contact) |

## Details

- All numbers with confidence intervals, agreement between the annotators (Cohen's kappa) and repeat consistency:
  [report.md](20260320_m1313black_f1603agouti_wt_estrus/report.md) and
  [fig2_agreement.png](20260320_m1313black_f1603agouti_wt_estrus/fig2_agreement.png).
- Raw answers: [records/](../records/). Scripts: [analyze_reviews.py](../scripts/analyze_reviews.py),
  [plot_reviews.py](../scripts/plot_reviews.py). To recreate the report and figures:

```powershell
cd $HOME\Desktop\Projektanalyse\Notebooks\03_quality_check
$PY = "$(uv tool dir)\sleap\Scripts\python.exe"
$N  = "20260320_m1313black_f1603agouti_wt_estrus"
$R  = "records\annotation_${N}_MFD_20261106-1333.json", "records\annotation_${N}_ZT_20261102-1218.json"
& $PY scripts\analyze_reviews.py @R --out results\$N\report.md
& $PY scripts\plot_reviews.py    @R --out results\$N
```
