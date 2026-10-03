import csv, os, sys, time
from common import find_image, list_names
from ocr_engines import get_engine
from dotenv import load_dotenv
load_dotenv()

# usage: python run_all.py tesseract qwen google_vision
engines = sys.argv[1:] or ["tesseract"]
names = list_names()
print(len(names), "images found")

rows = []
for eng in engines:
    print(f"\n=== loading {eng} ===")
    run = get_engine(eng)
    os.makedirs(os.path.join("outputs", eng), exist_ok=True)
    for name in names:
        out_path = os.path.join("outputs", eng, name + ".txt")
        if os.path.exists(out_path):        # skip finished ones so you can resume
            continue
        try:
            t0 = time.time()
            text = run(find_image(name))
            sec = time.time() - t0
            with open(out_path, "w", encoding="utf-8") as f:
                f.write(text)
            rows.append([eng, name, round(sec, 2)])
            print(f"{eng:14s} {name:18s} {sec:5.1f}s")
        except Exception as e:
            print(f"{eng:14s} {name:18s} ERROR: {str(e)[:100]}")

if rows:
    new = not os.path.exists("timing.csv")
    with open("timing.csv", "a", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        if new:
            w.writerow(["engine", "image", "seconds"])
        w.writerows(rows)