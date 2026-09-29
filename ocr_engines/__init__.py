import importlib


_MODULES = {
    "tesseract": "ocr_engines.tesseract_ocr",
    "qwen": "ocr_engines.qwen_ocr",
    "google_vision": "ocr_engines.google_vision_ocr",
    "fastocr": "ocr_engines.fastocr",
}

def get_engine(name):
    return importlib.import_module(_MODULES[name]).make()

ENGINE_NAMES = list(_MODULES)