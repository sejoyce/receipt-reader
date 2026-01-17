from receipt import Receipt
from fastapi import FastAPI, File, UploadFile
from fastapi.responses import JSONResponse
import shutil
import os
from receipt_reader import read_itemlist
from io import BytesIO

app = FastAPI()
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
async def parse_receipt(file: UploadFile = File(None)):
    """
    Receives a receipt image.
    Accepts:
      - multipart/form-data (UploadFile)
      - raw bytes (for testing via Postman binary)
    """
    if file is None:
        return {"error": "No file uploaded. Make sure the key is 'file' in form-data."}

    # Save file temporarily
    file_path = os.path.join(UPLOAD_DIR, file.filename)
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    # Parse receipt
    try:
        r = Receipt(file_path, expected_items)
        result = {"lines": r.text, "store": r.store, "date": r.date}
    except Exception as e:
        result = {"error": str(e)}
    finally:
        os.remove(file_path)

    return result