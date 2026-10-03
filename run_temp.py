import os
from common import list_names

os.makedirs("ground_truth", exist_ok=True)
for name in list_names():
    path = f"ground_truth/{name}.txt"
    if not os.path.exists(path):          # never overwrites your typing
        open(path, "w", encoding="utf-8").close()
print(len(list_names()), "images ->", "ground_truth/*.txt ready")