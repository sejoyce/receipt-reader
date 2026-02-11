import os
import requests
from PIL import Image

OCR_API_KEY = os.environ.get("OCR_API_KEY")

def compress_image_to_limit(file_path: str, max_size_kb=900):
    img = Image.open(file_path)

    if img.mode in ("RGBA", "P"):
        img = img.convert("RGB")

    max_width = 1200
    if img.width > max_width:
        ratio = max_width / img.width
        new_size = (max_width, int(img.height * ratio))
        img = img.resize(new_size, Image.LANCZOS)

    quality = 85
    img.save(file_path, format="JPEG", quality=quality)

    while os.path.getsize(file_path) > max_size_kb * 1024 and quality > 20:
        quality -= 5
        img.save(file_path, format="JPEG", quality=quality)

def run_ocr_with_ocr_space(file_path: str) -> str:
    """
    Uploads an image to OCR.Space and returns the parsed text.
    """
    compress_image_to_limit(file_path)

    with open(file_path, "rb") as f:
        r = requests.post(
            "https://api.ocr.space/parse/image",
            files={"file": f},
            data={
                "apikey": OCR_API_KEY,
                "language": "eng",
                "OCREngine": "2",
                "scale": "true",
                "isTable": "true",
                "detectOrientation": "true"
            }
        )

    try:
        result = r.json()
    except ValueError:
        raise Exception(f"OCR.Space did not return JSON. Response was:\n{r.text}")

    if not isinstance(result, dict):
        raise Exception(f"OCR.Space returned unexpected type: {type(result)}\nContent: {result}")

    if result.get("IsErroredOnProcessing"):
        raise Exception(f"OCR.Space error: {result.get('ErrorMessage')}")

    parsed_text = ""
    if "ParsedResults" in result and result["ParsedResults"]:
        parsed_text = result["ParsedResults"][0].get("ParsedText", "")

    return parsed_text
