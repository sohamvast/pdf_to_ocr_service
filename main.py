from fastapi import FastAPI, File, UploadFile
from fastapi.responses import JSONResponse
import subprocess
import tempfile
import os
import shutil
from PIL import Image
import pytesseract
import glob

app = FastAPI()

@app.post("/ocr-pdf")
async def ocr_pdf(file: UploadFile = File(...)):
    if not file.filename.lower().endswith(".pdf"):
        return JSONResponse(content={"error": "Only PDF files are supported"}, status_code=400)

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
                return JSONResponse(content={"error": f"OCR failed on {img_path}"}, status_code=500)

        return {"text": ocr_text.strip()}
