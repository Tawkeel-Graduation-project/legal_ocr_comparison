import pytesseract
from PIL import Image

pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"

def make():
    def run(path):
        return pytesseract.image_to_string(Image.open(path), lang="ara", config="--psm 6")
    return run