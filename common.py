import os

DATASET = "dataset"
IMG_EXT = (".jpg", ".jpeg", ".png")

def _index():
    """Map image name (without extension) -> full path, searching all class folders."""
    idx = {}
    for dirpath, _, files in os.walk(DATASET):
        for f in files:
            if f.lower().endswith(IMG_EXT):
                idx[os.path.splitext(f)[0]] = os.path.join(dirpath, f)
    return idx

def find_image(name):
    return _index()[name]

def list_names():
    return sorted(_index())