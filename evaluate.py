"""Score OCR outputs against your hand-typed ground truth.

    python evaluate.py            -> raw outputs
    python evaluate.py --clean    -> same, but repeated-line loops are collapsed (applied to ALL engines)

Only images that EVERY engine finished (and that have a non-empty ground-truth file) are scored,
so engines are always compared on the same images.
"""
import os, sys
import pandas as pd
from common import list_names
from evaluation.metrics import char_errors, word_errors
from evaluation.legal_fields import field_recall
from evaluation.legal_terms import term_recall
from evaluation.cleanup import collapse_repeats

CLEAN = "--clean" in sys.argv

# Properties of the engines (verify prices before reporting them)
COST_PER_1000_USD = {"tesseract": 0.0, "qwen": 0.0, "qari": 0.0, "chandra": 0.0, "google_vision": 1.50}
PRIVACY = {"tesseract": "local", "qwen": "local", "qari": "local", "chandra": "local", "google_vision": "cloud"}

def read(p):
    return open(p, encoding="utf-8").read() if os.path.exists(p) else None

names = list_names()
engines = sorted(d for d in os.listdir("outputs") if os.path.isdir(os.path.join("outputs", d)))

rows = []
for eng in engines:
    for name in names:
        ref, hyp = read(f"ground_truth/{name}.txt"), read(f"outputs/{eng}/{name}.txt")
        if not ref or not ref.strip() or hyp is None:
            continue
        if CLEAN:
            hyp = collapse_repeats(hyp)
        ce, cn = char_errors(ref, hyp)
        we, wn = word_errors(ref, hyp)
        tf, tt = term_recall(ref, hyp)
        rec = dict(engine=eng, image=name, cls=name.rsplit("_", 1)[0],
                   char_edits=ce, ref_chars=cn, word_edits=we, ref_words=wn,
                   term_found=tf, term_total=tt, hyp_chars=len(hyp))
        for k, (f, t) in field_recall(ref, hyp).items():
            rec[f"{k}_found"], rec[f"{k}_total"] = f, t
        rows.append(rec)

if not rows:
    sys.exit("Nothing to score: fill in ground_truth/*.txt and make sure outputs/<engine>/ has matching files.")

df = pd.DataFrame(rows)

# keep only images that every engine completed
per_engine = [set(g.image) for _, g in df.groupby("engine")]
common = set.intersection(*per_engine)
dropped = set.union(*per_engine) - common
df = df[df.image.isin(common)]
print(f"Mode: {'CLEAN (loops collapsed)' if CLEAN else 'RAW'}")
print(f"Engines: {sorted(df.engine.unique())} | images scored: {len(common)}")
if dropped:
    print("Not scored (missing for at least one engine):", sorted(dropped))
print()

df.to_csv("results_per_image_clean.csv" if CLEAN else "results_per_image.csv", index=False)

def ratio(g, num, den):
    return g[num] / g[den].replace(0, float("nan"))   # NaN (not 0) when nothing to measure

def summarize(keys):
    g = df.groupby(keys).sum(numeric_only=True)
    return pd.DataFrame({
        "CER": ratio(g, "char_edits", "ref_chars"),
        "WER": ratio(g, "word_edits", "ref_words"),
        "numbers": ratio(g, "number_found", "number_total"),
        "dates": ratio(g, "date_found", "date_total"),
        "terms": ratio(g, "term_found", "term_total"),
        "n_num": g["number_total"], "n_date": g["date_total"], "n_term": g["term_total"],
    }).round(3)

print("BY DOCUMENT TYPE  (CER/WER lower = better; numbers/dates/terms recall higher = better;")
print("                   n_* = how many items existed in the ground truth)\n")
print(summarize(["cls", "engine"]).to_string(), "\n")

final = summarize(["engine"])
if os.path.exists("timing.csv"):
    t = pd.read_csv("timing.csv")
    t = t[t.image.isin(common)]                         # ignore times of images no longer scored
    if len(t):
        final["sec_per_image"] = t.groupby("engine").seconds.mean().round(2)
n_pages = df.groupby("engine").image.nunique()
final["cost_usd"] = [
    None if COST_PER_1000_USD.get(e) is None else round(COST_PER_1000_USD[e] * n_pages[e] / 1000, 4)
    for e in final.index]
final["privacy"] = [PRIVACY.get(e, "local/other") for e in final.index]
print("OVERALL\n", final.to_string(), "\n")

# CER of every single image, one column per engine (shows which image caused a bad average)
per_img = (df.assign(CER=df.char_edits / df.ref_chars.replace(0, float("nan")))
             .pivot(index="image", columns="engine", values="CER").round(2))
print("CER PER IMAGE\n", per_img.to_string())