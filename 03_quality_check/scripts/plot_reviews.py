"""Figures from exported annotation records of one video (same inputs as analyze_reviews.py).

  fig1_accuracy_by_stratum.png  regions correct and skeletons whole per SLEAP stratum, per annotator, 95 % Wilson intervals
  fig2_agreement.png            inter-rater percent agreement and Cohen's kappa per question (first pair of records)
  fig3_scene_vs_stratum.png     the annotator's scene judgement against the SLEAP stratum, per annotator
Needs matplotlib (the SLEAP Python has it):
  & $PY Notebooks/03_quality_check/scripts/plot_reviews.py rec1.json rec2.json --out figures/<experiment>
"""
import argparse
import os
from collections import Counter, defaultdict

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

from analyze_reviews import SCENES, kappa, load, items_of, measures, wilson

STRATA = ["apart", "contact", "random"]          # "single" has at most one skeleton, shown in fig 3
MEASURES = ["head correct", "body correct", "rear correct", "skeletons whole"]
COLORS = ["#2a78d6", "#eb6834", "#1baf7a", "#6250d6"]
FIELDS = ["scene", "missed", "detect_A", "detect_B", "head_A", "head_B", "body_A", "body_B",
          "rear_A", "rear_B", "whole_A", "whole_B", "darker", "darker_conf", "overall"]


def usable_firsts(rec):
    return [e for e in items_of(rec).values() if not e[0]["repeat_of"] and e[1]["scene"] != "unusable"]


def fig_accuracy(recs, path):
    fig, axes = plt.subplots(1, len(MEASURES), figsize=(13, 3.6), sharey=True)
    w = 0.8 / len(recs)
    for ax, name in zip(axes, MEASURES):
        for i, r in enumerate(recs):
            entries = usable_firsts(r)
            for j, s in enumerate(STRATA):
                k, n = measures([e for e in entries if e[0]["stratum"] == s])[name]
                p = wilson(k, n)
                if p is None:
                    continue
                x = j + (i - (len(recs) - 1) / 2) * w
                ax.bar(x, 100 * p[0], w * 0.9, color=COLORS[i], label=r["annotator"] if j == 0 else None)
                ax.errorbar(x, 100 * p[0], yerr=[[100 * (p[0] - p[1])], [100 * (p[2] - p[0])]],
                            color="#444441", capsize=3, lw=1)
        ax.set_title(name)
        ax.set_xticks(range(len(STRATA)), STRATA)
        ax.set_ylim(40, 100)
        ax.grid(axis="y", color="#e1e0d9")
        ax.set_axisbelow(True)
    axes[0].set_ylabel("% of judged regions / skeletons")
    fig.legend(*axes[0].get_legend_handles_labels(), title="annotator", frameon=False, loc="upper right")
    fig.suptitle("%s: SLEAP accuracy by stratum (bars: proportion, whiskers: 95 %% Wilson CI)" % recs[0]["experiment"], fontsize=11)
    fig.tight_layout(rect=(0, 0, 0.93, 1))
    fig.savefig(path, dpi=150)
    plt.close(fig)


def fig_agreement(r1, r2, path):
    i1, i2 = items_of(r1), items_of(r2)
    common = [k for k in i1 if k in i2 and not i1[k][0]["repeat_of"]]
    rows = []
    for f in FIELDS:
        pairs = [(i1[k][1][f], i2[k][1][f]) for k in common if f in i1[k][1] and f in i2[k][1]]
        if pairs:
            po, k = kappa(pairs)
            rows.append((f, len(pairs), po, k))
    fig, ax = plt.subplots(figsize=(8, 0.38 * len(rows) + 1.4))
    y = range(len(rows))[::-1]
    ax.barh(list(y), [100 * r[2] for r in rows], color="#b5d4f4", height=0.6, label="percent agreement")
    ax.scatter([100 * r[3] for r in rows], list(y), color="#0c447c", zorder=3, label="Cohen's kappa x 100")
    ax.set_yticks(list(y), ["%s (n=%d)" % (r[0], r[1]) for r in rows])
    for v in (40, 60, 80):
        ax.axvline(v, color="#b4b2a9", lw=0.8, ls="--")
    ax.set_xlim(-10, 100)
    ax.set_xlabel("%   (dashed lines: kappa 0.4 / 0.6 / 0.8)")
    ax.legend(frameon=False, loc="lower left", bbox_to_anchor=(0, 1.0), ncol=2)
    ax.set_title("%s: %s vs %s, %d items" % (r1["experiment"], r1["annotator"], r2["annotator"], len(common)), fontsize=10, pad=24)
    fig.tight_layout()
    fig.savefig(path, dpi=150)
    plt.close(fig)


def fig_scene(recs, path):
    cols = SCENES + ["unusable"]
    strata = STRATA[:2] + ["single", "random"]
    fig, axes = plt.subplots(1, len(recs), figsize=(4.6 * len(recs), 3.4), squeeze=False)
    for ax, r in zip(axes[0], recs):
        firsts = [e for e in items_of(r).values() if not e[0]["repeat_of"]]
        m = [[Counter(e[1]["scene"] for e in firsts if e[0]["stratum"] == s)[c] for c in cols] for s in strata]
        ax.imshow(m, cmap="Blues", vmin=0, vmax=30)
        for a, row in enumerate(m):
            for b, v in enumerate(row):
                ax.text(b, a, v, ha="center", va="center", color="white" if v > 18 else "#042c53", fontsize=10)
        ax.set_xticks(range(len(cols)), cols, rotation=30, ha="right")
        ax.set_yticks(range(len(strata)), strata)
        ax.set_xlabel("annotator's scene judgement")
        ax.set_title("annotator %s" % r["annotator"], fontsize=10)
    axes[0][0].set_ylabel("SLEAP stratum")
    fig.suptitle("%s: scene judgement vs SLEAP stratum (first showings)" % recs[0]["experiment"], fontsize=11)
    fig.tight_layout()
    fig.savefig(path, dpi=150)
    plt.close(fig)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("records", nargs="+")
    ap.add_argument("--out", required=True, help="folder for the PNG files")
    a = ap.parse_args()
    recs = [load(p) for p in a.records]
    os.makedirs(a.out, exist_ok=True)
    fig_accuracy(recs, os.path.join(a.out, "fig1_accuracy_by_stratum.png"))
    if len(recs) > 1:
        fig_agreement(recs[0], recs[1], os.path.join(a.out, "fig2_agreement.png"))
    fig_scene(recs, os.path.join(a.out, "fig3_scene_vs_stratum.png"))
    print("written", a.out)


if __name__ == "__main__":
    main()
