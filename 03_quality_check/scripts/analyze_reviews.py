"""Analyse exported annotation records (PROTOCOL.md, section 7) and write a Markdown report.

For one or more records of the same video and protocol version:
  - per SLEAP stratum and per the annotator's own scene judgement: proportions with 95 % Wilson intervals
    (skeletons on a mouse, no mouse missed, regions correct, skeletons whole, darker mouse = identity script)
  - intra-rater agreement on the repeated items
  - inter-rater agreement (percent agreement and Cohen's kappa) for every pair of records
Only the standard library is used, so any Python 3 can run it:
  python Notebooks/03_quality_check/scripts/analyze_reviews.py annotation_<exp>_MFD_*.json annotation_<exp>_XY_*.json --out report.md
"""
import argparse
import json
import math
import sys
from collections import Counter, defaultdict
from itertools import combinations

SKEL = ["A", "B"]
STRATA = ["apart", "contact", "single", "random"]
SCENES = ["apart", "touching", "overlapping", "one"]


def wilson(k, n, z=1.96):
    if n == 0:
        return None
    p = k / n
    d = 1 + z * z / n
    c = (p + z * z / (2 * n)) / d
    h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return p, max(0.0, c - h), min(1.0, c + h)


def fmt(k, n):
    w = wilson(k, n)
    if w is None:
        return "–"
    return "%d %% [%d–%d] (%d/%d)" % (round(100 * w[0]), round(100 * w[1]), round(100 * w[2]), k, n)


def kappa(pairs):
    """Cohen's kappa for a list of (answer rater 1, answer rater 2)."""
    n = len(pairs)
    if n == 0:
        return None, None
    po = sum(a == b for a, b in pairs) / n
    c1, c2 = Counter(a for a, _ in pairs), Counter(b for _, b in pairs)
    pe = sum(c1[c] * c2[c] for c in set(c1) | set(c2)) / (n * n)
    k = 1.0 if pe == 1 else (po - pe) / (1 - pe)
    return po, k


def required(ans, animals, regions):
    """Answer fields that the protocol asks for, given the answers so far (same rules as the page)."""
    req = ["scene"]
    if ans.get("scene") == "unusable":
        return req + ["overall"]
    skels = SKEL[:animals]
    req += ["detect_" + s for s in skels] + ["missed"]
    on = [s for s in skels if ans.get("detect_" + s) == "mouse"]
    for s in on:
        req += ["%s_%s" % (r, s) for r in regions] + ["whole_" + s]
    if animals == 2 and len(on) == 2:
        req.append("darker")
        if ans.get("darker") not in (None, "cant"):
            req.append("darker_conf")
    return req + ["overall"]


def load(path):
    with open(path, encoding="utf-8") as f:
        r = json.load(f)
    if r.get("kind") != "pose-annotation-record":
        sys.exit("%s is not an annotation record" % path)
    return r


def items_of(rec):
    """item id -> (item info, answers) for complete items only."""
    regions = ["head", "body", "rear"]
    out = {}
    for it in rec["item_list"]:
        st = rec["items"].get(it["item"], {})
        a = st.get("answers", {})
        if all(a.get(k) for k in required(a, it["animals"], regions)):
            out[it["item"]] = (it, a, st)
    return out


def script_darker(it):
    g = it.get("grey") or []
    if len(g) != 2 or None in g:
        return None
    return "A" if g[0] < g[1] else "B"


def measures(entries):
    m = defaultdict(lambda: [0, 0])
    for it, a, _ in entries:
        skels = SKEL[:it["animals"]]
        for s in skels:
            m["skeletons on a mouse"][1] += 1
            m["skeletons on a mouse"][0] += a.get("detect_" + s) == "mouse"
        m["no mouse missed"][1] += 1
        m["no mouse missed"][0] += a.get("missed") == "no"
        for s in [s for s in skels if a.get("detect_" + s) == "mouse"]:
            for r in ["head", "body", "rear"]:
                v = a.get("%s_%s" % (r, s))
                if v in ("c", "w"):
                    m["%s correct" % r][1] += 1
                    m["%s correct" % r][0] += v == "c"
            m["skeletons whole"][1] += 1
            m["skeletons whole"][0] += a.get("whole_" + s) == "whole"
        sd = script_darker(it)
        if a.get("darker"):
            m["darker mouse could be told"][1] += 1
            m["darker mouse could be told"][0] += a["darker"] != "cant"
            if a["darker"] != "cant" and sd:
                m["darker: annotator = script"][1] += 1
                m["darker: annotator = script"][0] += a["darker"] == sd
    return m


COLS = ["skeletons on a mouse", "no mouse missed", "head correct", "body correct", "rear correct",
        "skeletons whole", "darker mouse could be told", "darker: annotator = script"]


def table(groups):
    lines = ["| group | items | " + " | ".join(COLS) + " |", "|---" * (len(COLS) + 2) + "|"]
    for name, entries in groups:
        m = measures(entries)
        lines.append("| %s | %d | " % (name, len(entries)) + " | ".join(fmt(*m[c]) if c in m else "–" for c in COLS) + " |")
    return "\n".join(lines)


def report(recs):
    r0 = recs[0]
    out = ["# Annotation report: %s" % r0["experiment"], "",
           "Protocol version %s · male: %s · sampling seed %s · %d record(s): %s" % (
               r0["protocol"], r0["male"], r0["sampling"]["seed"], len(recs), ", ".join(r["annotator"] for r in recs)), "",
           "Proportions with 95 % Wilson confidence intervals, first showings only, unusable frames left out. "
           "Regions: *correct* among regions judged correct or wrong (*not visible* excluded).", ""]
    for r in recs:
        its = items_of(r)
        firsts = [e for e in its.values() if not e[0]["repeat_of"]]
        usable = [e for e in firsts if e[1]["scene"] != "unusable"]
        times = sorted(e[2].get("time_ms", 0) / 1000 for e in its.values() if e[2].get("time_ms"))
        out += ["## Annotator %s" % r["annotator"], "",
                "Complete items: %d of %d · unusable: %d · unsure overall: %d · median time per item: %s · answers changed after reveal: %d" % (
                    len(its), len(r["item_list"]), len(firsts) - len(usable),
                    sum(e[1]["overall"] == "unsure" for e in firsts),
                    "%.0f s" % times[len(times) // 2] if times else "–",
                    sum(1 for l in r["log"] if l.get("after_reveal") and l["from"] is not None)), "",
                "### By SLEAP stratum", "",
                table([(s, [e for e in usable if e[0]["stratum"] == s]) for s in STRATA] + [("all", usable)]), "",
                "### By the annotator's scene judgement", "",
                table([(s, [e for e in usable if e[1]["scene"] == s]) for s in SCENES]), "",
                "### Scene judgement vs SLEAP stratum", "",
                "| SLEAP stratum | " + " | ".join(SCENES + ["unusable"]) + " |", "|---" * (len(SCENES) + 2) + "|"]
        for s in STRATA:
            c = Counter(e[1]["scene"] for e in firsts if e[0]["stratum"] == s)
            out.append("| %s | " % s + " | ".join(str(c[x]) for x in SCENES + ["unusable"]) + " |")
        reps = [e for e in its.values() if e[0]["repeat_of"]]
        out += ["", "### Intra-rater agreement (repeated items)", ""]
        if not reps:
            out.append("No repeated item is complete yet.")
        else:
            same_item, fields = 0, defaultdict(list)
            for it, a, _ in reps:
                if it["repeat_of"] not in its:
                    continue
                _, a1, _ = its[it["repeat_of"]]
                keys = sorted(set(required(a1, it["animals"], ["head", "body", "rear"])) | set(required(a, it["animals"], ["head", "body", "rear"])))
                same_item += all(a1.get(k) == a.get(k) for k in keys)
                for k in keys:
                    fields[k].append((a1.get(k), a.get(k)))
            n = sum(1 for it, _, _ in reps if it["repeat_of"] in its)
            out += ["Items answered identically: %s" % fmt(same_item, n), "",
                    "| field | pairs | agreement |", "|---|---|---|"]
            for k in sorted(fields):
                p = fields[k]
                out.append("| %s | %d | %d %% |" % (k, len(p), round(100 * sum(x == y for x, y in p) / len(p))))
        out.append("")

    if len(recs) > 1:
        out += ["## Inter-rater agreement", "",
                "Items complete in both records, first showings. Kappa: < 0.4 poor, 0.4–0.6 moderate, 0.6–0.8 substantial, > 0.8 almost perfect.", ""]
        for r1, r2 in combinations(recs, 2):
            i1, i2 = items_of(r1), items_of(r2)
            common = [k for k in i1 if k in i2 and not i1[k][0]["repeat_of"]]
            fields = defaultdict(list)
            for k in common:
                a1, a2 = i1[k][1], i2[k][1]
                for f in sorted(set(a1) & set(a2)):
                    fields[f].append((a1[f], a2[f]))
            out += ["### %s vs %s (%d items)" % (r1["annotator"], r2["annotator"], len(common)), "",
                    "| field | pairs | agreement | Cohen's kappa |", "|---|---|---|---|"]
            for f in sorted(fields):
                po, k = kappa(fields[f])
                out.append("| %s | %d | %d %% | %s |" % (f, len(fields[f]), round(100 * po), "%.2f" % k))
            dis = [k for k in common if i1[k][1].get("scene") != i2[k][1].get("scene")]
            out += ["", "Items with a different scene judgement (discuss these first): %s" % (", ".join(
                "%s (frame %d)" % (k, i1[k][0]["frame"]) for k in dis) or "none"), ""]
    return "\n".join(out) + "\n"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("records", nargs="+")
    ap.add_argument("--out", help="Markdown file to write; default: print")
    a = ap.parse_args()
    recs = [load(p) for p in a.records]
    if len({(r["experiment"], r["protocol"]) for r in recs}) > 1:
        sys.exit("all records must be for the same video and protocol version")
    text = report(recs)
    if a.out:
        with open(a.out, "w", encoding="utf-8") as f:
            f.write(text)
        print("written", a.out)
    else:
        print(text)


if __name__ == "__main__":
    main()
