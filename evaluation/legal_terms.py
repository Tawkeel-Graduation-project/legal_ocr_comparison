from collections import Counter
from .normalize import normalize_arabic

# Words typical of official / administrative / legal Arabic. Extend this after you see your own ground truth.
TERMS = ["وزارة", "الوزارة", "الجمهورية", "المملكة", "الدولة", "محكمة", "المحكمة",
         "قرار", "مرسوم", "قانون", "المادة", "مادة", "رقم", "تاريخ", "بتاريخ",
         "طلب", "السيد", "السيدة", "توقيع", "ختم", "مديرية", "إدارة", "شهادة", "عقد"]

_TERMS = {normalize_arabic(t) for t in TERMS}

def term_recall(ref, hyp):
    """(found, total): term occurrences in the ground truth that the OCR also produced."""
    r = Counter(w for w in normalize_arabic(ref).split() if w in _TERMS)
    h = Counter(w for w in normalize_arabic(hyp).split() if w in _TERMS)
    return sum((r & h).values()), sum(r.values())