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
| Manual annotation | 80 sampled frames per video, judged by two annotators with a written protocol | the reference the automatic checks are measured against |

## Manual annotation (protocol v1.0)

The rules are in [PROTOCOL.md](PROTOCOL.md): questions, decision rules, body regions, blinding, procedure.

| File | Role |
|---|---|
| `PROTOCOL.md` | the written, versioned protocol |
| `scripts/sample_frames.py` | picks the frames (fixed seed), draws them with ±5 context frames, adds 8 hidden repeats, writes the page |
| `review_page.html` | the annotation page (copied into every review folder as `index.html`) |
| `scripts/analyze_reviews.py` | report from the exported records: 95 % Wilson intervals, intra- and inter-rater agreement (Cohen's kappa) |
| `answer_guide.png` | picture guide to the answer options of Q1–Q6 (simplified drawings; the protocol text decides) |
| `scripts/plot_reviews.py` | figures from the same records: accuracy by stratum, inter-rater agreement, scene vs stratum |
| `records/` | exported annotation records (JSON) |
| [`results/`](results/README.md) | findings per video: report, figures, methods and limitations |

**1. Prepare a video** (the male's fur colour is read from the folder name):

```powershell
cd $HOME\Desktop\Projektanalyse
$PY = "$(uv tool dir)\sleap\Scripts\python.exe"
$N  = "20260320_m1313black_f1603agouti_wt_estrus"
& $PY Notebooks\03_quality_check\scripts\sample_frames.py results\$N\predictions_raw.slp data\videos\videoTop_$N.avi review\$N
```

**2. Annotate.** Each annotator opens `review\<experiment>\index.html` (Chrome or Edge), enters their initials and works
through the 88 items independently. To share the task, zip the whole `review\<experiment>\` folder (~75 MB).
At the end: **Export record (JSON)**; that file is the official record.

**3. Analyse** (any Python 3, no packages needed):

```powershell
python Notebooks\03_quality_check\scripts\analyze_reviews.py review\$N\annotation_*_XX_*.json review\$N\annotation_*_YY_*.json --out review\$N\report.md
```

## Status

- [x] Protocol v1.0, annotation page, analysis script (tested with simulated records)
- [x] Review folders prepared for the 3 test videos (m1313, m1599, m1600)
- [x] Annotator ZT: all 3 videos done; records in [records/](records/)
- [x] m1313: both annotators done (MFD, ZT); results in [results/](results/README.md)
- [ ] m1599, m1600: second annotator (MFD), then analyse
- [ ] Agree on the rule for an almost fully hidden mouse (protocol v1.1 for new videos)
- [ ] Write the automatic checks
- [ ] Run it on the 3 test videos and fill in the results table in [02_pose_sleap/README.md](../02_pose_sleap/README.md)
