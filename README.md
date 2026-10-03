# Tawkeel — Legal OCR & Document Pipeline Spike (Sprint 0)

> **Document Processing & Arabic OCR Engine Benchmark**  
> **Author:** Manal Anwer | **Project:** Tawkeel Graduation Project  
> **Sprint:** Sprint 0 — Technical Feasibility & Architecture Spike

---

## 1. Executive Summary

Optical Character Recognition (OCR) for Arabic documents—particularly in legal, governmental, and administrative domains—presents severe challenges: cursive script, non-standard typography, context-dependent letter shaping, ligatures, diacritics, mixed Arabic/Latin content, complex tabular layouts, and degraded handwritten text.

The goal of this **Sprint 0 Spike** is to evaluate candidate OCR approaches to identify the most viable, accurate, and robust starting point for the **Tawkeel** document ingestion pipeline. We benchmarked four distinct OCR engines across a curated evaluation dataset representing real-world legal and administrative Arabic documents.

### Key Takeaways

| Engine | Best Suited For | Clean CER | Clean WER | Official Words Recall | Key Advantages | Primary Risk / Bottleneck |
| :--- | :--- | :---: | :---: | :---: | :--- | :--- |
| **Qwen2.5-VL-3B** | **Best Overall Generalist** | **0.44** | **0.62** | 70% | Most dependable overall; lowest CER/WER once loops are collapsed; highest date recall (40%). | Prone to repetition loops on noisy pages; requires a loop guard. |
| **Chandra OCR 2 (~5B)** | **Printed Text & Tables** | 1.02 *(0.29\**)* | 1.36 | **83%** | **Best on printed Arabic (CER 0.11)**; preserves table hierarchy (HTML/Markdown); won 4/9 images. | Catastrophic runaway generation on outlier pages; high compute footprint (2x GPUs). |
| **Tesseract (v5 + ara)** | **CPU Baseline / Simple Forms** | 0.62 | 0.89 | 20% | Free, ultra-lightweight (~0.8s/img on CPU), deterministic (never loops or hallucinates). | Fails on handwriting (CER 0.75); misses large text sections; zero date recall. |
| **Qari-OCR-0.4.0 (4B)** | **Classical Printed Books** | 1.71 | 2.18 | 48% | Near-perfect on clean classical print (CER 0.03); high number recall (49%). | Extreme hallucination on modern/tabled docs (counts numbers, invents pages); not production-ready for legal docs. |

*\* Excluding the catastrophic outlier `tabled_data_02`.*

---

## 2. Benchmark Dataset

The test suite consists of **9 representative Arabic document images** (6,215 characters, 85 numbers, 15 dates, and 46 administrative/legal terms) categorized into three realistic operational regimes:

```
dataset/
├── handwritten/        # Degradation, calligraphic variance, human forms
│   ├── handwritten_01  (297 chars)
│   ├── handwritten_02  (491 chars)
│   └── handwritten_03  (581 chars)
├── printed_arabic/     # Standard legal decrees, court summons, official reports
│   ├── printed_arabic_01 (1,175 chars)
│   ├── printed_arabic_02 (864 chars)
│   └── printed_arabic_03 (500 chars)
└── tabled_data/        # Civil registry extracts, structured forms, tabular grids
    ├── tabled_data_01  (1,015 chars)
    ├── tabled_data_02  (419 chars - low-density, high tabular complexity)
    └── tabled_data_03  (873 chars)
```

Each image is accompanied by an authoritative, human-transcribed ground truth file in `ground_truth/<image_name>.txt` adhering strictly to natural reading order.

---

## 3. Evaluated OCR Engines

| Engine | Architecture / Paradigm | Hardware & Runtime Setup | Output Format |
| :--- | :--- | :--- | :--- |
| **Tesseract OCR** | Traditional open-source pipeline (line finding + LSTM) | Laptop CPU (`ara` pack), ~0.8s per image | Plain text |
| **Qwen2.5-VL-3B** | Multimodal Vision-Language Model (Alibaba, 3B params) | 1x Kaggle GPU, max 1,536 new tokens, prompt: *"extract all the Arabic text"* | Plain text |
| **Qari-OCR-0.4.0 (4B)** | Fine-tuned Qwen2-VL-4B on 45k classical Arabic book pages (NAMAA) | 1x Kaggle GPU, max 1,536 new tokens, prompt: *"Free OCR."* | Plain text |
| **Chandra OCR 2** | Layout-preserving document VLM (Datalab, ~5B params) | 2x Kaggle GPUs, reduced resolution, max ~12,000 tokens | Markdown & HTML tables (`<table>`, `<tr>`, `<td>`, `**`, `#`) |

*(Note: Google Cloud Vision was provisioned in the pipeline design at \$1.50/1,000 pages, but excluded from this sprint due to setup deadlines).*

---

## 4. Evaluation Methodology

### 4.1. Domain-Specific Text Normalization
To prevent false penalties arising from typography, font encoding, or formatting quirks, both ground truth ($R$) and OCR hypothesis ($H$) pass through `evaluation/normalize.py`:
- **NFKC Unicode Normalization**: Standardizes character compositions.
- **Diacritics & Kashida Removal**: Strips Tashkeel (`[\u0610-\u061A\u064B-\u065F\u0670\u06D6-\u06ED]`) and Tatweel/stretching (`\u0640`).
- **Digit Harmonization**: Maps Arabic-Indic numerals (`٠١٢٣٤٥٦٧٨٩`) to standard ASCII digits (`0-9`).
- **Orthographic Unification**: Maps Alef variants (`إ`, `أ`, `آ`, `ٱ` $\to$ `ا`) and Yeh variants (`ى` $\to$ `ي`).
- **Layout & Leader Clean-up**: Collapses fill lines (`...`, `___`), normalizes date separators (`5 / 3 / 2021` $\to$ `5/3/2021`), and collapses contiguous whitespace.

### 4.2. Quantitative Metrics
1. **Character Error Rate (CER)**:  
   $$\text{CER} = \frac{S + D + I}{N_{\text{ref}}} = \frac{\text{Levenshtein}(R, H)}{\text{len}(R)}$$  
   *(Note: CER can exceed 1.0 when models hallucinate extra text).*
2. **Word Error Rate (WER)**: Levenshtein distance measured over tokenized whitespace words.
3. **Legal Entity & Field Recall**:
   - **Dates**: Regex-matched extraction (`\b\d{1,4}[/\-.]\d{1,2}[/\-.]\d{1,4}\b`).
   - **Numbers**: Integer and digit sequence recall (`\d+`).
   - **Official Legal Terms**: Occurrences of key legal terminology (`وزارة`, `مرسوم`, `قانون`, `محكمة`, `قرار`, `المادة`, `توقيع`, `ختم`, `إدارة`, etc.).

### 4.3. Raw Run vs. Clean Run (Loop Suppression)
Vision-Language Models occasionally fall into repetitive token loops on ambiguous inputs. To measure real-world performance with basic system-level safeguards, we evaluated:
- **Raw Run**: Pure outputs directly emitted by the engines.
- **Clean Run (`--clean`)**: Passes outputs through `evaluation/cleanup.py` (`collapse_repeats`), which detects recurring blocks of 1–4 lines repeated $>3$ times, collapsing them down to 2 repetitions.

---

## 5. Benchmark Results

### 5.1. Overall Performance (All 9 Images)

| Engine | CER (Raw) | CER (Clean) | WER (Clean) | Numbers Found | Dates Found | Official Terms | Median CER | Images Won (Lowest CER) |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **Qwen2.5-VL-3B** | 0.74 | **0.44** | **0.62** | 38% | **40% (6/15)** | 70% | 0.47 | 3 |
| **Chandra OCR 2** | 1.55 | 1.02 | 1.36 | 27% | 7% (1/15) | **83%** | **0.31** | **4** |
| **Tesseract** | **0.62** | 0.62 | 0.89 | 11% | 0% (0/15) | 20% | 0.76 | 1 |
| **Qari-OCR-0.4.0** | 1.71 | 1.71 | 2.18 | **49%** | 0% (0/15) | 48% | 2.20 | 1 |

*Lower is better for CER, WER, and Median CER. Higher is better for recall columns.*

---

### 5.2. Breakdown by Document Category (Clean CER)

| Document Category | Tesseract | Qwen2.5-VL-3B | Qari-OCR | Chandra OCR 2 | Category Winner |
| :--- | :---: | :---: | :---: | :---: | :--- |
| **Handwritten** | 0.75 | **0.42** | 0.44 | 0.50 | **Qwen2.5-VL-3B** |
| **Printed Arabic** | 0.39 | 0.27 | 1.84 | **0.11** | **Chandra OCR 2** |
| **Tabled / Forms (Clean)** | 0.79 | **0.64** | 2.33 | 2.34 | **Qwen2.5-VL-3B** |
| *Tabled / Forms (Raw)* | *0.79* | *1.43* | *2.33* | *3.77* | *Tesseract (Deterministic)* |

---

### 5.3. Granular Per-Image CER Matrix (Clean Run)

| Image | Ref Chars | Tesseract | Qwen2.5-VL-3B | Qari-OCR | Chandra OCR 2 | Winner |
| :--- | :---: | :---: | :---: | :---: | :--- |
| `handwritten_01` | 297 | 0.69 | **0.06** | 0.12 | 0.07 | **Qwen2.5-VL** |
| `handwritten_02` | 491 | 0.77 | **0.26** | 0.33 | 0.31 | **Qwen2.5-VL** |
| `handwritten_03` | 581 | 0.76 | 0.74 | **0.71** | 0.87 | **Qari-OCR** |
| `printed_arabic_01` | 1,175 | 0.17 | **0.02** | 0.03 | 0.03 | **Qwen / Qari / Chandra** |
| `printed_arabic_02` | 864 | 0.39 | 0.51 | 2.99 | **0.22** | **Chandra OCR 2** |
| `printed_arabic_03` | 500 | 0.90 | 0.45 | 4.11 | **0.13** | **Chandra OCR 2** |
| `tabled_data_01` | 1,015 | 0.85 | 0.66 | 2.24 | **0.38** | **Chandra OCR 2** |
| `tabled_data_02` | 419 | **0.92** | 0.93 | 2.80 | 11.13 | **Tesseract (No loop)** |
| `tabled_data_03` | 873 | 0.67 | 0.47 | 2.20 | **0.39** | **Chandra OCR 2** |

---

## 6. Deep Dive & Failure Analysis

### 6.1. The `tabled_data_02` Catastrophe
`tabled_data_02` is a short administrative form containing only 419 ground-truth characters. It triggered pathological failure modes across all modern neural models:
- **Chandra OCR 2**: Repeated a block of names and titles indefinitely, generating **~8,300 characters** and spending **24 minutes** on a single image. Its raw CER reached **19.01** (reduced to 11.13 in clean run).
- **Qwen2.5-VL-3B**: Fell into a single-word loop (raw CER: 5.32), successfully rescued to 0.93 by `collapse_repeats`.
- **Qari-OCR**: Began counting numbers sequentially from 1 up to 328. Because its output was not a line-level repeat, loop suppression had zero effect.
- **Tesseract**: Extracted only 46 characters (severe omission), but because it cannot hallucinate, achieved the "best" CER (0.92) simply by failing conservatively.

> **Impact:** If `tabled_data_02` is excluded as an anomaly, Chandra’s overall CER drops from **1.02 to ~0.29**, making it the most accurate engine overall. This proves that a single unconstrained runaway output can destroy pipeline reliability.

### 6.2. Chandra's Structural Superpower vs. Evaluation Bias
Chandra OCR 2 does not emit flat plain text; it parses document geometry into **HTML tables and Markdown tags**:
```html
<table border="1">
  <tr><th>اسم الموكل</th><th>الرقم القومي</th></tr>
  <tr><td>أحمد مصطفى كامل</td><td>29501011600123</td></tr>
</table>
```
- **Strengths:** Crucial for downstream Tawkeel entity extraction (associating table headers with cell values).
- **Evaluation Bias:** Ground truth text is serialized in reading order. Flattening Chandra's HTML tables into raw text for CER computation introduces cell-order discrepancies and strips structural bonuses, meaning Chandra's numeric CER actually **understates its true utility**.

### 6.3. Domain-Mismatch in Specialized Models
Qari-OCR was trained specifically on classical printed Islamic literature. When tested on modern official decrees, bureaucratic headers, and tables, its language model prior broke down, generating 3x to 5x more text than existed on the page.

---

## 7. Related Research: Domain-Specific Adaptation

A recent study by **Elkousy et al. (2026)** (*"Domain-Specific Adaptation of Vision-Language Models for Arabic OCR"*, Procedia Computer Science, ACLing 2025) provides vital empirical direction:
1. **LoRA Fine-Tuning Gains:** Fine-tuning `Qwen2.5-VL-3B` with 4-bit quantization (QLoRA) yielded a **29.17% CER reduction on modern Arabic text** and **17.38% on historical documents**.
2. **Specialization vs. Generalization Trade-off:** The study observed that fine-tuning on real calligraphic noise reduced accuracy on synthetic benchmarks. Training must prioritize authentic legal artifacts over synthetic fonts.
3. **Orthographic Sensitivity:** Even when VLM structural accuracy was high, small orthographic features (diacritics, subtle hamzas) remained error-prone, reinforcing the need for our normalization rules.

---

## 8. Architectural Recommendations for Tawkeel

Based on experimental findings and external research, we propose a **hybrid, guarded architecture**:

```
                       ┌─────────────────────────┐
                       │  Uploaded Document/PDF  │
                       └────────────┬────────────┘
                                    │
                                    ▼
                       ┌─────────────────────────┐
                       │ Page Layout & Routing   │
                       └──────┬───────────┬──────┘
                              │           │
       [High Tabular/Printed] │           │ [Handwritten/Mixed]
                              ▼           ▼
                      ┌──────────────┐   ┌──────────────┐
                      │ Chandra OCR2 │   │ Qwen2.5-VL-3B│
                      └──────┬───────┘   └──────┬───────┘
                             │                  │
                             └──────────┬───────┘
                                        │
                                        ▼
                     ┌──────────────────────────────────────┐
                     │     INFERENCE SAFEGUARD LAYER        │
                     │  - Strict max_new_tokens cap         │
                     │  - Regex / repetition watchdog       │
                     │  - Heuristic loop collapsing         │
                     └──────────────────┬───────────────────┘
                                        │
                                        ▼
                     ┌──────────────────────────────────────┐
                     │ Structured Legal Entities & Metadata │
                     └──────────────────────────────────────┘
```

1. **Routing Strategy**:
   - Use **Chandra OCR 2** for printed official gazettes, contracts, and tabular forms where layout reconstruction is mandatory.
   - Use **Qwen2.5-VL-3B** for freeform text, handwritten appeals, or low-resource deployments.
2. **Mandatory Production Safeguards**:
   - **Generation Token Cap**: Strictly bound generation length based on image dimensions/DPI (e.g., maximum 1,500 tokens).
   - **Repetition Loop Detector**: Terminate streaming generation if identical n-grams or lines repeat $\ge 3$ times.
   - **Length Discrepancy Flag**: Flag any output whose character length deviates by $>2.5\times$ from estimated heuristic visual density.
3. **Future Fine-Tuning**: Once a corpus of authentic Tawkeel legal instruments is collected, execute domain adaptation on Qwen2.5-VL using LoRA + 4-bit quantization as validated by Elkousy et al.

---

## 9. Repository Structure

```
├── dataset/                    # Sample evaluation documents (handwritten, printed, tabled)
├── ground_truth/               # Verified gold-standard Arabic text files
├── ocr_engines/                # Modular engine abstraction wrappers
│   ├── tesseract_ocr.py        # Tesseract wrapper
│   ├── qwen_ocr.py             # Qwen2.5-VL inference driver
│   └── google_vision_ocr.py    # Google Cloud Vision driver
├── evaluation/                 # Metrics & scoring suite
│   ├── metrics.py              # Levenshtein distance, CER, WER calculations
│   ├── normalize.py            # Arabic orthographic normalizer & regex rules
│   ├── cleanup.py              # Loop detection and repeat collapsing
│   ├── legal_fields.py         # Date & number extraction recall
│   └── legal_terms.py          # Administrative/legal vocabulary recall
├── outputs/                    # Output logs per engine (tesseract, qwen, qari, chandra)
├── common.py                   # Dataset discovery & image indexer
├── run_all.py                  # Batch inference orchestrator with runtime tracking
├── evaluate.py                 # Core evaluation CLI (generates CSV reports)
└── diagnose.py                 # Per-image length discrepancy & error inspection
```

---

## 10. Reproduction & Usage Guide

### Prerequisites
- Python 3.10+
- Tesseract OCR binary installed with Arabic language support (`tessdata/ara.traineddata`)
- CUDA-compatible GPU (for local VLM inference) or Kaggle/Colab GPU environments

### Installation
```bash
pip install -r requirements.txt
```
*(Dependencies: `pandas`, `python-dotenv`, `pillow`, `editdistance`, `transformers`, `torch`, `accelerate`)*

### Running Inference
Run all available or specific engines across the benchmark dataset:
```bash
# Run specific engine(s)
python run_all.py tesseract qwen

# Resumes automatically by checking outputs/<engine>/<image>.txt
```

### Running Evaluation
Compute CER, WER, and Legal Entity Recall metrics:
```bash
# 1. Raw Run (outputs as generated)
python evaluate.py

# 2. Clean Run (with repetition loop collapse enabled)
python evaluate.py --clean
```
Outputs will be logged directly to the console and exported to:
- `results_per_image.csv` (Raw run)
- `results_per_image_clean.csv` (Clean run)

### Running Diagnostics
Inspect character counts, hypothesis expansions, and individual image CERs:
```bash
python diagnose.py
```

---

## 11. Citations & References

- **[1]** A. Elkousy, Y. Elasrigy, A. Ammara, M. Ibrahim, M. M. N. Aboelwafaa, *"Domain-Specific Adaptation of Vision-Language Models for Arabic OCR,"* Procedia Computer Science, vol. 275, pp. 351–358, 2026. (Proceedings of ACLing 2025).
- **Tawkeel Document Pipeline Spike (Sprint 0)**: Internal technical report, Manal Anwer.
