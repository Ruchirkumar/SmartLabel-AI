from pathlib import Path

from fastapi import APIRouter, HTTPException

from app.services.ocr import extract_text
from app.services.information_extraction import extract_product_information

router = APIRouter(
    prefix="/api",
    tags=["OCR"],
)

UPLOAD_DIR = Path("uploads")


@router.post("/ocr/{filename}")
def run_ocr(filename: str):
    image_path = UPLOAD_DIR / filename

    if not image_path.exists():
        raise HTTPException(
            status_code=404,
            detail=f"Image not found: {image_path}",
        )

    try:
        # Step 1: Run PaddleOCR
        detections = extract_text(str(image_path))

        # Step 2: Convert OCR detections into structured information
        product_information = extract_product_information(detections)

        return {
            "filename": filename,
            "text_count": len(detections),
            "product_information": product_information,
            "detections": detections,
        }

    except Exception as exc:
        print("\n========== OCR ERROR ==========")
        print(type(exc).__name__)
        print(str(exc))
        print("================================\n")

        raise HTTPException(
            status_code=500,
            detail=f"OCR failed: {type(exc).__name__}: {exc}",
        )