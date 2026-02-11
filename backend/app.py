from backend.receipt import Receipt
from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import shutil
import os
from backend.receipt_reader import read_itemlist, split_receipt_text
from backend.ocr_api import run_ocr_with_ocr_space, compress_image_to_limit
from io import BytesIO
import tempfile

app = FastAPI(
    title="Receipt OCR API",
    version="1.0.0",
    root_path=""
)

# Allow requests from your mobile app
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # restrict in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

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
    """
    Accepts a receipt image file, runs OCR, and returns structured items and total.
    """
    # Save uploaded file to a temporary location
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(file.filename)[1]) as tmp:
            tmp_path = tmp.name
            tmp.write(await file.read())

        # Compress if needed (to avoid size limits on OCR.Space)
        compress_image_to_limit(tmp_path)

        # Run OCR.Space
        ocr_text = run_ocr_with_ocr_space(tmp_path)

        # Remove temp file
        os.remove(tmp_path)

        # Create Receipt object from OCR text
        receipt = Receipt.from_text(ocr_text)
        receipt.extract_metadata()          # store name + date
        structured = receipt.extract_items()  # structured items + total

        return {
            "store": receipt.store,
            "date": receipt.date,
            "items": structured["items"],
            "total": structured["total"]
        }

    except Exception as e:
        # Clean up temp file if it still exists
        if os.path.exists(tmp_path):
            os.remove(tmp_path)
        raise HTTPException(status_code=500, detail=str(e))