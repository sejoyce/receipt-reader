from backend.receipt import Receipt
from fastapi import FastAPI, File, UploadFile
from fastapi.responses import JSONResponse
import shutil
import os
from backend.receipt_reader import read_itemlist
from backend.ocr_api import run_ocr_with_ocr_space
from io import BytesIO

app = FastAPI(
    title="Receipt OCR API",
    version="1.0.0",
    root_path=""
)
UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)
expected_items, _ = read_itemlist()

@app.get("/health")
async def healthcheck():
    """
    Simple health check endpoint.
    Returns status 200 if the API is up.
    """
    return {
        "status": "ok",
        "message": "Receipt parser API is running",
    }

@app.post("/parse_receipt/")
async def parse_receipt(file: UploadFile = File(...)):
    file_path = os.path.join(UPLOAD_DIR, file.filename)

    # Save file
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    # Run OCR through OCR.Space
    text = run_ocr_with_ocr_space(file_path)

    # Pass OCR text to Receipt class
    receipt = Receipt.from_text(text)
    receipt.extract_metadata()

    structured = receipt.extract_items()

    os.remove(file_path)

    return {
        "store": receipt.store,
        "date": receipt.date,
        "items": structured["items"],
        "total": structured["total"]
    }