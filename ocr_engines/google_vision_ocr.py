from google.cloud import vision

def make():
    client = vision.ImageAnnotatorClient()
    def run(path):
        with open(path, "rb") as f:
            image = vision.Image(content=f.read())
        resp = client.document_text_detection(image=image, image_context={"language_hints": ["ar"]})
        if resp.error.message:
            raise RuntimeError(resp.error.message)
        return resp.full_text_annotation.text
    return run