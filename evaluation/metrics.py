from .normalize import normalize_arabic

def edit_distance(a, b):
    prev = list(range(len(b) + 1))
    for i, x in enumerate(a, 1):
        cur = [i]
        for j, y in enumerate(b, 1):
            cur.append(min(prev[j] + 1, cur[j - 1] + 1, prev[j - 1] + (x != y)))
        prev = cur
    return prev[-1]

def char_errors(ref, hyp):
    r, h = normalize_arabic(ref), normalize_arabic(hyp)
    return edit_distance(r, h), len(r)

def word_errors(ref, hyp):
    r, h = normalize_arabic(ref).split(), normalize_arabic(hyp).split()
    return edit_distance(r, h), len(r)