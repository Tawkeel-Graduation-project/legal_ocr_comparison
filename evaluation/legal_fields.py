import re
from collections import Counter
from .normalize import normalize_arabic

PATTERNS = {
    "date": re.compile(r"\b\d{1,4}[/\-.]\d{1,2}[/\-.]\d{1,4}\b"),
    "number": re.compile(r"\d+"),
}

def field_recall(ref, hyp):
    """For each field type: (found, total) = items in ground truth that also appear in OCR output."""
    r = {k: Counter(p.findall(normalize_arabic(ref))) for k, p in PATTERNS.items()}
    h = {k: Counter(p.findall(normalize_arabic(hyp))) for k, p in PATTERNS.items()}
    return {k: (sum((r[k] & h[k]).values()), sum(r[k].values())) for k in PATTERNS}