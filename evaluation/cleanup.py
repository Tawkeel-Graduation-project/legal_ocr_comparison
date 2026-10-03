def collapse_repeats(text, max_block=4, keep=2):
    """Collapse runs where the same block of 1..max_block lines repeats more than keep+1 times.
    Keeps the first `keep` repetitions and drops the rest. Applied identically to every engine."""
    lines = [l.strip() for l in (text or "").splitlines()]
    out, i = [], 0
    while i < len(lines):
        collapsed = False
        for k in range(1, max_block + 1):
            block = lines[i:i + k]
            if len(block) < k:
                break
            reps = 1
            while lines[i + reps * k: i + (reps + 1) * k] == block:
                reps += 1
            if reps >= keep + 2:
                out.extend(block * keep)
                i += reps * k
                collapsed = True
                break
        if not collapsed:
            out.append(lines[i])
            i += 1
    return "\n".join(out)