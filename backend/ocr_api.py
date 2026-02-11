import os
import requests

OCR_API_KEY = os.environ.get("OCR_API_KEY")

def run_ocr_with_ocr_space(file_path: str) -> str:
    """
    Uploads an image to OCR.Space and returns the parsed text.
    """
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

    result = r.json()
    print(result)
    if result.get("IsErroredOnProcessing"):
        raise Exception(f"OCR.Space error: {result.get('ErrorMessage')}")

    parsed_text = ""
    if "ParsedResults" in result and result["ParsedResults"]:
        parsed_text = result["ParsedResults"][0].get("ParsedText", "")

    return parsed_text
