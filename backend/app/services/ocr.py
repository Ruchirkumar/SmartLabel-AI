from pathlib import Path
from typing import Any

from paddleocr import PaddleOCR


# Initialize once when the backend starts.
# PP-OCRv5 server detector is intentionally used because
# SmartLabel prioritizes accuracy over minimum latency.
ocr = PaddleOCR(
    lang="en",
    ocr_version="PP-OCRv5",

    # Document preprocessing
    use_doc_orientation_classify=True,
    use_doc_unwarping=True,

    # Text orientation
    use_textline_orientation=True,

    # Accuracy-first detector
    text_detection_model_name="PP-OCRv5_server_det",

    # English recognition
    text_recognition_model_name="en_PP-OCRv5_mobile_rec",

    # Your Windows environment previously had MKL-DNN/PIR issues.
    enable_mkldnn=False,

    # Keep every recognized text region.
    text_rec_score_thresh=0.0,

    # Return polygon information.
    return_word_box=False,
)


def _normalize_polygon(polygon: Any) -> list[list[int]]:
    """
    Convert PaddleOCR polygon output into:
    [[x1, y1], [x2, y2], ...]
    """
    if polygon is None:
        return []

    try:
        return [
            [int(round(float(point[0]))), int(round(float(point[1])))]
            for point in polygon
        ]
    except (TypeError, ValueError, IndexError):
        return []


def _polygon_to_bbox(polygon: list[list[int]]) -> list[int]:
    """
    Convert polygon to [x1, y1, x2, y2].
    """
    if not polygon:
        return []

    xs = [point[0] for point in polygon]
    ys = [point[1] for point in polygon]

    return [
        min(xs),
        min(ys),
        max(xs),
        max(ys),
    ]


def extract_text(image_path: str) -> list[dict]:
    """
    Run PaddleOCR on a product-label image.

    Returns one dictionary per detected text region:

    {
        "text": "...",
        "confidence": 0.98,
        "bbox": [x1, y1, x2, y2],
        "polygon": [[x1,y1], ...],
        "index": 0
    }

    The complete OCR evidence is preserved for the
    information-extraction layer.
    """

    path = Path(image_path)

    if not path.exists():
        raise FileNotFoundError(
            f"Image not found: {image_path}"
        )

    if not path.is_file():
        raise ValueError(
            f"Path is not a file: {image_path}"
        )

    results = ocr.predict(str(path))

    detections: list[dict] = []

    for page in results:

        # PaddleOCR 3.x Result object exposes JSON through .json
        data = page.json

        if isinstance(data, str):
            import json
            data = json.loads(data)

        if isinstance(data, list):
            if not data:
                continue
            data = data[0]

        res = data.get("res", data)

        texts = res.get("rec_texts", [])
        scores = res.get("rec_scores", [])
        polygons = res.get("rec_polys", [])

        # Keep every OCR detection.
        count = max(
            len(texts),
            len(scores),
            len(polygons),
        )

        for index in range(count):

            text = (
                str(texts[index]).strip()
                if index < len(texts)
                else ""
            )

            confidence = (
                float(scores[index])
                if index < len(scores)
                else 0.0
            )

            polygon = (
                _normalize_polygon(polygons[index])
                if index < len(polygons)
                else []
            )

            bbox = _polygon_to_bbox(polygon)

            # Do not discard low-confidence OCR.
            # The extraction layer may still need it.
            detections.append(
                {
                    "text": text,
                    "confidence": round(confidence, 4),
                    "bbox": bbox,
                    "polygon": polygon,
                    "index": index,
                }
            )

    return detections


def extract_text_with_metadata(image_path: str) -> dict:
    """
    Rich OCR response used when the application needs
    document-level metadata in addition to detections.
    """

    path = Path(image_path)

    if not path.exists():
        raise FileNotFoundError(
            f"Image not found: {image_path}"
        )

    results = ocr.predict(str(path))

    all_detections: list[dict] = []
    pages: list[dict] = []

    for page_index, page in enumerate(results):

        data = page.json

        if isinstance(data, str):
            import json
            data = json.loads(data)

        if isinstance(data, list):
            if not data:
                continue
            data = data[0]

        res = data.get("res", data)

        texts = res.get("rec_texts", [])
        scores = res.get("rec_scores", [])
        polygons = res.get("rec_polys", [])

        page_detections = []

        for index, text in enumerate(texts):

            polygon = (
                _normalize_polygon(polygons[index])
                if index < len(polygons)
                else []
            )

            confidence = (
                float(scores[index])
                if index < len(scores)
                else 0.0
            )

            detection = {
                "text": str(text).strip(),
                "confidence": round(confidence, 4),
                "bbox": _polygon_to_bbox(polygon),
                "polygon": polygon,
                "index": index,
            }

            page_detections.append(detection)
            all_detections.append(detection)

        pages.append(
            {
                "page_index": page_index,
                "angle": (
                    res.get("doc_preprocessor_res", {})
                    .get("angle")
                ),
                "detections": page_detections,
            }
        )

    return {
        "image_path": str(path),
        "text_count": len(all_detections),
        "detections": all_detections,
        "pages": pages,
    }


def get_full_text(image_path: str) -> str:
    """
    Return OCR text in PaddleOCR reading order.

    This is intentionally a convenience function.
    For SmartLabel extraction, prefer extract_text()
    because bounding boxes are important.
    """

    detections = extract_text(image_path)

    return "\n".join(
        item["text"]
        for item in detections
        if item["text"]
    )