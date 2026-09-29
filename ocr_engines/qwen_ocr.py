import torch
from PIL import Image
from transformers import Qwen2_5_VLForConditionalGeneration, AutoProcessor

MODEL_ID = "Qwen/Qwen2.5-VL-3B-Instruct"
PROMPT = "Extract all the Arabic text in this image exactly as written. Output only the text, nothing else."

def make():
    processor = AutoProcessor.from_pretrained(
        MODEL_ID, min_pixels=256 * 28 * 28, max_pixels=1280 * 28 * 28)
    model = Qwen2_5_VLForConditionalGeneration.from_pretrained(
        MODEL_ID, torch_dtype="auto", device_map="auto")

    def run(path):
        img = Image.open(path).convert("RGB")
        msgs = [{"role": "user", "content": [{"type": "image"}, {"type": "text", "text": PROMPT}]}]
        text = processor.apply_chat_template(msgs, tokenize=False, add_generation_prompt=True)
        inputs = processor(text=[text], images=[img], return_tensors="pt").to(model.device)
        with torch.no_grad():
            out = model.generate(**inputs, max_new_tokens=1024, do_sample=False)
        out = out[:, inputs.input_ids.shape[1]:]
        return processor.batch_decode(out, skip_special_tokens=True)[0]
    return run