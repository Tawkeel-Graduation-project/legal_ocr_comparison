import re, unicodedata

_DIAC = re.compile(r"[\u0610-\u061A\u064B-\u065F\u0670\u06D6-\u06ED\u0640]")
_DIGITS = str.maketrans("٠١٢٣٤٥٦٧٨٩۰۱۲۳۴۵۶۷۸۹", "01234567890123456789")

def normalize_arabic(text):
    t = unicodedata.normalize("NFKC", text or "")
    t = _DIAC.sub("", t).translate(_DIGITS)
    t = re.sub("[إأآٱ]", "ا", t).replace("ى", "ي")          # alef/hamza forms and ى/ي
    t = re.sub(r"[._]{2,}", " ", t)                           # dotted or underscore fill lines
    t = re.sub(r"(?<=\d)\s*([/.\-])\s*(?=\d)", r"\1", t)      # "5 / 3 / 2021" -> "5/3/2021"
    return re.sub(r"\s+", " ", t).strip()