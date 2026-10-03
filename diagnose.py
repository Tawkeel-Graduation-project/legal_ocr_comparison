import os
from common import list_names
from evaluation.normalize import normalize_arabic
from evaluation.metrics import char_errors

rows = []
for eng in sorted(os.listdir("outputs")):
    for n in list_names():
        gt, out = f"ground_truth/{n}.txt", f"outputs/{eng}/{n}.txt"
        if not (os.path.exists(gt) and os.path.exists(out)):
            continue
        ref = open(gt, encoding="utf-8").read()
        hyp = open(out, encoding="utf-8").read()
        if not ref.strip():
            continue
        e, l = char_errors(ref, hyp)
        rows.append((n, eng, l, len(normalize_arabic(hyp)), round(e / max(l, 1), 2)))

print(f"{'image':28}{'engine':11}{'ref_len':>8}{'hyp_len':>8}{'CER':>7}")
for r in sorted(rows):
    print(f"{r[0]:28}{r[1]:11}{r[2]:8}{r[3]:8}{r[4]:7}")