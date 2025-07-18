from fastapi import FastAPI, File, UploadFile, Depends, HTTPException, status
from fastapi.responses import JSONResponse
from fastapi.security.api_key import APIKeyHeader
import subprocess
import tempfile
from typing import Optional
import os
import shutil
from PIL import Image
import pytesseract
import glob
from dotenv import load_dotenv

# Define the API Key name and dependency
API_KEY_NAME = "X-API-Key"
api_key_header = APIKeyHeader(name=API_KEY_NAME, auto_error=False)

load_dotenv()  # Load environment variables from .env file
API_KEY = os.getenv("API_KEY")

app = FastAPI()

# Dependency to validate API Key
def get_api_key(api_key_header: Optional[str] = Depends(api_key_header)):
    expected_api_key = os.environ.get("API_KEY")
    print('########################## Executing API Key Validation ########################## ')
    if api_key_header == expected_api_key:
        return api_key_header
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid or missing API Key",
    )


@app.post("/ocr-pdf", dependencies=[Depends(get_api_key)])
async def ocr_pdf(file: UploadFile = File(...)):
    if not file.filename.lower().endswith(".pdf"):
        return JSONResponse(content={"error": "Only PDF files are supported"}, status_code=400)

    print('########################## Executing OCR Action ########################## ')

    # Create a temporary working directory
    with tempfile.TemporaryDirectory() as tmpdir:
        pdf_path = os.path.join(tmpdir, "input.pdf")
        
        # Save uploaded file to temporary directory
        with open(pdf_path, "wb") as f:
            f.write(await file.read())

        # Convert PDF to images using pdftoppm
        try:
            subprocess.run(["pdftoppm", "-png", pdf_path, os.path.join(tmpdir, "page")], check=True)
        except subprocess.CalledProcessError as e:
            return JSONResponse(content={"error": "Failed to convert PDF to images"}, status_code=500)

        # OCR each image and collect text
        ocr_text = ""
        image_files = sorted(glob.glob(os.path.join(tmpdir, "page-*.png")))
        for img_path in image_files:
            try:
                img = Image.open(img_path)
                text = pytesseract.image_to_string(img)
                ocr_text += text + "\n\n"
            except Exception as e:
                print(f"Error processing {img_path}: {e}")
                return JSONResponse(content={"error": f"OCR failed on {img_path}"}, status_code=500)

        return {"text": ocr_text.strip()}
