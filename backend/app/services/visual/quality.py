from pathlib import Path

import cv2


def analyze_image_quality(image_path: str) -> dict:
    path = Path(image_path)

    if not path.exists():
        raise FileNotFoundError(f"Image not found: {image_path}")

    image = cv2.imread(str(path))

    if image is None:
        raise ValueError("Unable to read image.")

    height, width = image.shape[:2]

    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

    # Blur estimation using Laplacian variance.
    blur_score = float(cv2.Laplacian(gray, cv2.CV_64F).var())

    # Brightness estimation.
    brightness = float(gray.mean())

    # Contrast estimation.
    contrast = float(gray.std())

    quality_issues = []

    if blur_score < 100:
        quality_issues.append("possible_blur")

    if brightness < 60:
        quality_issues.append("too_dark")
    elif brightness > 210:
        quality_issues.append("too_bright")

    if contrast < 35:
        quality_issues.append("low_contrast")

    if width < 1000 or height < 1000:
        quality_issues.append("low_resolution")

    return {
        "width": width,
        "height": height,
        "blur_score": round(blur_score, 2),
        "brightness": round(brightness, 2),
        "contrast": round(contrast, 2),
        "quality_issues": quality_issues,
        "enhancement_required": len(quality_issues) > 0,
    }