import re
from typing import Any, Callable


# ============================================================
# SMARTLABEL AI - INFORMATION EXTRACTION ENGINE
# ============================================================
#
# Design principles:
# 1. Never modify the original PaddleOCR detection structure.
# 2. Prefer explicit field labels over global regex matching.
# 3. Use spatial proximity when labels and values are separate.
# 4. Never hardcode specific product names.
# 5. Preserve company <-> licence relationships where possible.
# 6. Extraction is NOT compliance. Compliance engine decides that.
#
# ============================================================


# ============================================================
# BASIC HELPERS
# ============================================================

def _clean_text(text: str) -> str:
    text = str(text or "")
    text = text.replace("\n", " ")
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def _normalize_ocr_text(text: str) -> str:
    """
    Normalize common OCR/label variations.

    Important:
    This creates normalized_text only.
    Original `text` is preserved.
    """

    text = _clean_text(text)

    replacements = {
        # Price
        "M.R.P.": "MRP",
        "M.R.P": "MRP",
        "M R P": "MRP",
        "M.R.P": "MRP",

        # FSSAI
        "LIC. NO.": "LIC NO",
        "LIC. NO": "LIC NO",
        "LIC.NO": "LIC NO",
        "LIC NO.": "LIC NO",
        "LICENSE NO.": "LICENSE NO",

        # Batch
        "BATCH NO.": "BATCH NO",
        "BATCH NO": "BATCH NO",
        "LOT NO.": "LOT NO",
        "LOT NO": "LOT NO",

        # Dates
        "DATE OF EXPIRY:": "DATE OF EXPIRY",
        "DATE OF EXPIRY": "DATE OF EXPIRY",
        "DATE OF EXP:": "DATE OF EXP",
        "DATE OF MFG:": "DATE OF MFG",
        "DATE OF MANUFACTURE:": "DATE OF MANUFACTURE",
        "DATE OF MFG": "DATE OF MFG",

        # Business roles
        "MANUFACTURED BY": "MANUFACTURED BY",
        "MANUFACTURER:": "MANUFACTURER",
        "PACKED BY": "PACKED BY",
        "PACKED AT": "PACKED AT",
        "MARKETED BY": "MARKETED BY",
        "IMPORTED BY": "IMPORTED BY",

        # Quantity
        "NET QTY": "NET QUANTITY",
        "NET QTY.": "NET QUANTITY",
        "N.QTY": "NET QUANTITY",
        "N.QTY:": "NET QUANTITY",
        "NET WT": "NET WEIGHT",
        "NET WT.": "NET WEIGHT",

        # Consumer care
        "CUST CARE": "CUSTOMER CARE",
        "CUSTOMER CARE NO": "CUSTOMER CARE",
        "CONSUMER CARE": "CUSTOMER CARE",
        "CONSUMER CARE DETAILS": "CUSTOMER CARE",

        # Generic name
        "NAME OF COMMODITY": "NAME OF COMMODITY",
        "COMMON NAME": "COMMON NAME",
        "GENERIC NAME": "GENERIC NAME",
    }

    for old, new in replacements.items():
        text = text.replace(old, new)

    return text


def _safe_float(value: Any, default: float = 0.0) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


# ============================================================
# BOUNDING BOX
# ============================================================

def _bbox_info(bbox: Any) -> dict[str, float] | None:
    """
    Supports both:

        [x1, y1, x2, y2]

    and PaddleOCR polygon:

        [[x1,y1], [x2,y2], [x3,y3], [x4,y4]]
    """

    if not bbox:
        return None

    try:
        # Flat bbox: [x1, y1, x2, y2]
        if (
            isinstance(bbox, (list, tuple))
            and len(bbox) == 4
            and all(
                isinstance(v, (int, float))
                for v in bbox
            )
        ):
            x1, y1, x2, y2 = map(float, bbox)

            return {
                "x1": min(x1, x2),
                "x2": max(x1, x2),
                "y1": min(y1, y2),
                "y2": max(y1, y2),
                "cx": (x1 + x2) / 2,
                "cy": (y1 + y2) / 2,
                "width": abs(x2 - x1),
                "height": abs(y2 - y1),
            }

        # Polygon bbox
        if (
            isinstance(bbox, (list, tuple))
            and len(bbox) >= 4
        ):
            xs = []
            ys = []

            for point in bbox:
                if (
                    isinstance(point, (list, tuple))
                    and len(point) >= 2
                ):
                    xs.append(float(point[0]))
                    ys.append(float(point[1]))

            if len(xs) >= 2:
                x1 = min(xs)
                x2 = max(xs)
                y1 = min(ys)
                y2 = max(ys)

                return {
                    "x1": x1,
                    "x2": x2,
                    "y1": y1,
                    "y2": y2,
                    "cx": (x1 + x2) / 2,
                    "cy": (y1 + y2) / 2,
                    "width": x2 - x1,
                    "height": y2 - y1,
                }

    except (TypeError, ValueError, IndexError):
        return None

    return None


# ============================================================
# OCR PREPARATION
# ============================================================

def _prepare_detections(
    ocr_results: list[dict[str, Any]]
) -> list[dict[str, Any]]:

    detections = []

    for item in ocr_results:

        text = _clean_text(
            item.get("text", "")
        )

        if not text:
            continue

        bbox = item.get("bbox")

        info = _bbox_info(bbox)

        confidence = _safe_float(
            item.get("confidence", 0)
        )

        # IMPORTANT:
        # Preserve exact structure expected by existing system.
        detections.append(
            {
                "text": text,
                "normalized_text": _normalize_ocr_text(text),
                "confidence": confidence,
                "bbox": bbox,
                "_bbox": info,
            }
        )

    return detections


# ============================================================
# REGEX PATTERNS
# ============================================================

DATE_PATTERN = (
    r"\b"
    r"(?:0?[1-9]|[12]\d|3[01])"
    r"[/-]"
    r"(?:0?[1-9]|1[0-2])"
    r"[/-]"
    r"(?:\d{2}|\d{4})"
    r"\b"
)

MONTH_YEAR_PATTERN = (
    r"\b"
    r"(?:0?[1-9]|1[0-2])"
    r"[/-]"
    r"\d{2,4}"
    r"\b"
)

MONTH_NAME_YEAR_PATTERN = (
    r"\b"
    r"(?:JAN(?:UARY)?|FEB(?:RUARY)?|MAR(?:CH)?|"
    r"APR(?:IL)?|MAY|JUN(?:E)?|JUL(?:Y)?|"
    r"AUG(?:UST)?|SEP(?:T(?:EMBER)?)?|"
    r"OCT(?:OBER)?|NOV(?:EMBER)?|DEC(?:EMBER)?)"
    r"\s+\d{4}\b"
)

WEIGHT_PATTERN = (
    r"\b\d+(?:\.\d+)?\s*"
    r"(?:mg|g|kg|ml|l|"
    r"milligram(?:s)?|"
    r"gram(?:s)?|"
    r"kilogram(?:s)?|"
    r"millilitre(?:s)?|"
    r"milliliter(?:s)?|"
    r"litre(?:s)?|"
    r"liter(?:s)?)"
    r"\b"
)

COMPOUND_QUANTITY_PATTERN = (
    r"\b\d+(?:\.\d+)?\s*(?:g|kg|ml|l)"
    r"(?:\s*\([^)]{1,100}\))?"
)

DIMENSION_PATTERN = (
    r"\b"
    r"\d+(?:\.\d+)?\s*(?:mm|cm|m)"
    r"(?:\s*[xX×]\s*"
    r"\d+(?:\.\d+)?\s*(?:mm|cm|m))+"
    r"\b"
)

BATCH_PATTERN = (
    r"\b[A-Z0-9][A-Z0-9./\-_]{2,40}\b"
)

LICENSE_PATTERN = (
    r"\b\d{14}\b"
)

PIN_PATTERN = (
    r"\b[1-9][0-9]{5}\b"
)

PHONE_PATTERN = (
    r"(?:\+91[\s\-]?)?"
    r"[6-9]\d{9}"
)

EMAIL_PATTERN = (
    r"\b[A-Z0-9._%+-]+"
    r"@[A-Z0-9.-]+\.[A-Z]{2,}\b"
)


# ============================================================
# DATE HELPERS
# ============================================================

def _extract_date(text: str) -> str | None:

    text = _clean_text(text)

    match = re.search(
        DATE_PATTERN,
        text,
        re.IGNORECASE,
    )

    if match:
        return match.group(0)

    return None


def _extract_any_date(text: str) -> str | None:

    text = _clean_text(text)

    for pattern in (
        DATE_PATTERN,
        MONTH_NAME_YEAR_PATTERN,
        MONTH_YEAR_PATTERN,
    ):
        match = re.search(
            pattern,
            text,
            re.IGNORECASE,
        )

        if match:
            return match.group(0)

    return None


# ============================================================
# QUANTITY HELPERS
# ============================================================

def _extract_weight(text: str) -> str | None:

    text = _clean_text(text)

    match = re.search(
        COMPOUND_QUANTITY_PATTERN,
        text,
        re.IGNORECASE,
    )

    if match:
        return _clean_text(
            match.group(0)
        )

    match = re.search(
        WEIGHT_PATTERN,
        text,
        re.IGNORECASE,
    )

    if match:
        return re.sub(
            r"\s+",
            "",
            match.group(0),
        )

    return None


def _extract_dimension(text: str) -> str | None:

    match = re.search(
        DIMENSION_PATTERN,
        text,
        re.IGNORECASE,
    )

    if match:
        return match.group(0)

    return None


# ============================================================
# PRICE
# ============================================================

def _extract_mrp(text: str) -> str | None:

    text = _normalize_ocr_text(text)

    patterns = [

        # MRP ₹299
        r"\bMRP\b"
        r"\s*[:\-]?\s*"
        r"(?:₹|Rs\.?|INR)"
        r"\s*"
        r"([0-9]+(?:\.[0-9]{1,2})?)",

        # MRP 299
        r"\bMRP\b"
        r"\s*[:\-]?\s*"
        r"([0-9]+(?:\.[0-9]{1,2})?)",

        # Maximum Retail Price ₹299
        r"\bMAXIMUM\s+RETAIL\s+PRICE\b"
        r".{0,20}?"
        r"(?:₹|Rs\.?|INR)"
        r"\s*"
        r"([0-9]+(?:\.[0-9]{1,2})?)",
    ]

    for pattern in patterns:

        match = re.search(
            pattern,
            text,
            re.IGNORECASE,
        )

        if match:
            try:
                value = float(
                    match.group(1)
                )

                if value > 0:
                    return f"{value:.2f}"

            except (
                ValueError,
                TypeError,
            ):
                pass

    return None


def _extract_price_with_currency(
    text: str,
) -> str | None:

    match = re.search(
        r"(?:₹|Rs\.?|INR)"
        r"\s*"
        r"([0-9]+(?:\.[0-9]{1,2})?)",
        text,
        re.IGNORECASE,
    )

    if match:
        return match.group(1)

    return None


# ============================================================
# LABEL MATCHING
# ============================================================

def _matches_any(
    text: str,
    patterns: list[str],
) -> bool:

    return any(
        re.search(
            pattern,
            text,
            re.IGNORECASE,
        )
        for pattern in patterns
    )


# ============================================================
# SPATIAL DISTANCE
# ============================================================

def _same_line(
    a: dict[str, Any],
    b: dict[str, Any],
) -> bool:

    box_a = a.get("_bbox")
    box_b = b.get("_bbox")

    if not box_a or not box_b:
        return False

    tolerance = max(
        18,
        min(
            box_a["height"],
            box_b["height"],
        ) * 1.5,
    )

    return (
        abs(
            box_a["cy"] - box_b["cy"]
        )
        <= tolerance
    )


def _horizontal_gap(
    a: dict[str, Any],
    b: dict[str, Any],
) -> float:

    box_a = a.get("_bbox")
    box_b = b.get("_bbox")

    if not box_a or not box_b:
        return 999999

    return box_b["x1"] - box_a["x2"]


# ============================================================
# NEARBY VALUE
# ============================================================

def _find_nearby_value(
    detections: list[dict[str, Any]],
    label_index: int,
    extractor: Callable[[str], str | None],
    max_vertical_distance: float = 220,
) -> str | None:

    label = detections[label_index]
    label_box = label.get("_bbox")

    # First: value inside same OCR detection.
    direct_value = extractor(
        label["text"]
    )

    if direct_value:
        return direct_value

    if not label_box:
        return None

    candidates = []

    for i, candidate in enumerate(
        detections
    ):

        if i == label_index:
            continue

        candidate_box = candidate.get(
            "_bbox"
        )

        if not candidate_box:
            continue

        value = extractor(
            candidate["text"]
        )

        if not value:
            continue

        dy = abs(
            candidate_box["cy"]
            - label_box["cy"]
        )

        dx = (
            candidate_box["cx"]
            - label_box["cx"]
        )

        if dy > max_vertical_distance:
            continue

        score = 999999

        # ----------------------------------------
        # Same line, value to right
        # ----------------------------------------

        if (
            dy <= max(
                25,
                label_box["height"] * 1.5,
            )
            and dx >= -40
        ):

            gap = max(
                0,
                candidate_box["x1"]
                - label_box["x2"],
            )

            score = (
                dy * 2
                + gap
            )

        # ----------------------------------------
        # Value directly below
        # ----------------------------------------

        elif candidate_box["cy"] > label_box["cy"]:

            horizontal_alignment = abs(
                candidate_box["cx"]
                - label_box["cx"]
            )

            score = (
                dy * 2
                + horizontal_alignment
                + 80
            )

        if score < 999999:
            candidates.append(
                (
                    score,
                    value,
                )
            )

    if candidates:
        candidates.sort(
            key=lambda x: x[0]
        )

        return candidates[0][1]

    return None


# ============================================================
# MRP FROM DETECTIONS
# ============================================================

def _extract_mrp_from_detections(
    detections: list[dict[str, Any]]
) -> str | None:

    # Explicit MRP detections first.
    for item in detections:

        value = _extract_mrp(
            item["text"]
        )

        if value:
            return value

    mrp_labels = [
        r"\bMRP\b",
        r"\bMAXIMUM\s+RETAIL\s+PRICE\b",
    ]

    for i, item in enumerate(
        detections
    ):

        if not _matches_any(
            item["text"],
            mrp_labels,
        ):
            continue

        value = _find_nearby_value(
            detections,
            i,
            _extract_mrp,
            max_vertical_distance=240,
        )

        if value:
            return value

        # Sometimes value is just Rs 10.
        value = _find_nearby_value(
            detections,
            i,
            _extract_price_with_currency,
            max_vertical_distance=240,
        )

        if value:
            return value

    return None


# ============================================================
# QUANTITY
# ============================================================

def _extract_quantity_from_detections(
    detections: list[dict[str, Any]]
) -> str | None:

    labels = [
        r"\bNET\s+QUANTITY\b",
        r"\bNET\s+WEIGHT\b",
        r"\bNET\s+WT\b",
        r"\bNET\s+QTY\b",
        r"\bN\.?\s*QTY\b",
        r"\bNET\b",
    ]

    for i, item in enumerate(
        detections
    ):

        if not _matches_any(
            item["text"],
            labels,
        ):
            continue

        # Direct value.
        value = _extract_weight(
            item["text"]
        )

        if value:
            return value

        # Nearby value.
        value = _find_nearby_value(
            detections,
            i,
            _extract_weight,
            max_vertical_distance=220,
        )

        if value:
            return value

    # Global fallback.
    for item in detections:

        value = _extract_weight(
            item["text"]
        )

        if value:
            return value

    return None


# ============================================================
# BATCH / LOT
# ============================================================

def _is_date_like(value: str) -> bool:

    if re.fullmatch(
        DATE_PATTERN,
        value,
        re.IGNORECASE,
    ):
        return True

    if re.fullmatch(
        MONTH_YEAR_PATTERN,
        value,
        re.IGNORECASE,
    ):
        return True

    return False


def _extract_batch(text: str) -> str | None:

    text = _clean_text(text)

    explicit = re.search(
        r"\b(?:BATCH|LOT)"
        r"\s*(?:NO|NUMBER|CODE)?\.?"
        r"\s*[:\-]?\s*"
        r"([A-Z0-9][A-Z0-9./\-_]{2,40})",
        text,
        re.IGNORECASE,
    )

    if explicit:

        value = explicit.group(1).strip(
            " .,:;"
        )

        if (
            len(value) >= 3
            and not _is_date_like(value)
        ):
            return value

    # If the detection itself is a batch-like code.
    candidate = text.strip(
        " .,:;"
    )

    if (
        3 <= len(candidate) <= 40
        and any(
            c.isdigit()
            for c in candidate
        )
        and re.fullmatch(
            BATCH_PATTERN,
            candidate,
            re.IGNORECASE,
        )
        and not _is_date_like(candidate)
    ):
        return candidate

    return None


def _extract_batch_from_detections(
    detections: list[dict[str, Any]]
) -> str | None:

    labels = [
        r"\bBATCH\b",
        r"\bLOT\b",
        r"\bLOT\s+NO\b",
        r"\bBATCH\s+NO\b",
    ]

    for i, item in enumerate(
        detections
    ):

        if not _matches_any(
            item["text"],
            labels,
        ):
            continue

        value = _extract_batch(
            item["text"]
        )

        if value:
            return value

        value = _find_nearby_value(
            detections,
            i,
            _extract_batch,
            max_vertical_distance=200,
        )

        if value:
            return value

    # Explicit full-text fallback.
    full_text = " ".join(
        item["text"]
        for item in detections
    )

    match = re.search(
        r"\b(?:BATCH|LOT)"
        r"\s*(?:NO|NUMBER|CODE)?\.?"
        r"\s*[:\-]?\s*"
        r"([A-Z0-9][A-Z0-9./\-_]{2,40})",
        full_text,
        re.IGNORECASE,
    )

    if match:
        value = match.group(1)

        if not _is_date_like(value):
            return value

    return None


# ============================================================
# DATE OF MANUFACTURE
# ============================================================

MANUFACTURE_LABELS = [
    r"\bDATE\s+OF\s+MANUFACTURE\b",
    r"\bDATE\s+OF\s+MFG\b",
    r"\bMANUFACTURED\s+ON\b",
    r"\bMFG\b",
    r"\bMFD\b",
    r"\bDOM\b",
    r"\bPKD\b",
    r"\bPACKED\s+ON\b",
]


def _extract_manufacture_date(
    detections: list[dict[str, Any]]
) -> str | None:

    for i, item in enumerate(
        detections
    ):

        if not _matches_any(
            item["text"],
            MANUFACTURE_LABELS,
        ):
            continue

        value = _extract_any_date(
            item["text"]
        )

        if value:
            return value

        value = _find_nearby_value(
            detections,
            i,
            _extract_any_date,
            max_vertical_distance=240,
        )

        if value:
            return value

    return None


# ============================================================
# EXPIRY / USE BY
# ============================================================

EXPIRY_LABELS = [
    r"\bUSE\s+BY\b",
    r"\bUSE\s+BEFORE\b",
    r"\bEXPIRY\b",
    r"\bEXP\b",
    r"\bEXPIRY\s+DATE\b",
    r"\bDATE\s+OF\s+EXPIRY\b",
    r"\bDATE\s+OF\s+EXP\b",
    r"\bBEST\s+BEFORE\b",
]


def _extract_use_by_date(
    detections: list[dict[str, Any]]
) -> str | None:

    for i, item in enumerate(
        detections
    ):

        if not _matches_any(
            item["text"],
            EXPIRY_LABELS,
        ):
            continue

        value = _extract_any_date(
            item["text"]
        )

        if value:
            return value

        value = _find_nearby_value(
            detections,
            i,
            _extract_any_date,
            max_vertical_distance=260,
        )

        if value:
            return value

    return None


# ============================================================
# COMPANY / ROLE EXTRACTION
# ============================================================

ROLE_LABELS = {
    "manufacturer": [
        r"\bMANUFACTURED\s+BY\b",
        r"\bMANUFACTURER\b",
        r"\bMFD\s+BY\b",
    ],
    "packer": [
        r"\bPACKED\s+BY\b",
        r"\bPACKED\s+AT\b",
        r"\bPACKER\b",
    ],
    "marketer": [
        r"\bMARKETED\s+BY\b",
        r"\bMARKETER\b",
    ],
    "importer": [
        r"\bIMPORTED\s+BY\b",
        r"\bIMPORTER\b",
    ],
}


COMPANY_STOP_LABELS = [
    r"\bMANUFACTURED\s+BY\b",
    r"\bMANUFACTURER\b",
    r"\bMFD\s+BY\b",
    r"\bPACKED\s+BY\b",
    r"\bPACKED\s+AT\b",
    r"\bPACKER\b",
    r"\bMARKETED\s+BY\b",
    r"\bMARKETER\b",
    r"\bIMPORTED\s+BY\b",
    r"\bIMPORTER\b",
    r"\bBATCH\b",
    r"\bLOT\b",
    r"\bMRP\b",
    r"\bNET\s+(?:QUANTITY|WEIGHT|QTY)\b",
    r"\bFSSAI\b",
    r"\bLIC\.?\s*NO\b",
    r"\bDATE\b",
    r"\bMFG\b",
    r"\bMFD\b",
    r"\bPKD\b",
    r"\bEXPIRY\b",
    r"\bUSE\s+BY\b",
    r"\bBEST\s+BEFORE\b",
    r"\bCUSTOMER\s+CARE\b",
    r"\bCONSUMER\s+CARE\b",
    r"\bINGREDIENTS?\b",
    r"\bNUTRITION\b",
]


def _looks_like_company(text: str) -> bool:

    text_upper = text.upper()

    company_terms = [
        "PVT",
        "PRIVATE",
        "LTD",
        "LIMITED",
        "LLP",
        "INC",
        "CORP",
        "CORPORATION",
        "COMPANY",
        "CO.",
        "FOODS",
        "FOOD",
        "INDUSTRIES",
        "ENTERPRISES",
        "INTERNATIONAL",
        "INDIA",
        "TRADERS",
        "MANUFACTURING",
        "BAKERS",
        "NUTRI",
    ]

    return any(
        term in text_upper
        for term in company_terms
    )


def _extract_company_after_label(
    detections: list[dict[str, Any]],
    label_patterns: list[str],
) -> str | None:

    for i, label in enumerate(
        detections
    ):

        if not _matches_any(
            label["text"],
            label_patterns,
        ):
            continue

        label_box = label.get("_bbox")

        # ----------------------------------------
        # Case 1:
        # "MARKETED BY: PepsiCo India..."
        # in same OCR detection.
        # ----------------------------------------

        for pattern in label_patterns:

            match = re.search(
                pattern
                + r"\s*[:\-]?\s*(.+)$",
                label["text"],
                re.IGNORECASE,
            )

            if match:

                candidate = _clean_text(
                    match.group(1)
                )

                if (
                    candidate
                    and len(candidate) >= 3
                    and not _matches_any(
                        candidate,
                        COMPANY_STOP_LABELS,
                    )
                ):
                    return candidate

        if not label_box:
            continue

        candidates = []

        for j, candidate in enumerate(
            detections
        ):

            if j == i:
                continue

            box = candidate.get("_bbox")

            if not box:
                continue

            text = candidate["text"].strip()

            if not text:
                continue

            if _matches_any(
                text,
                COMPANY_STOP_LABELS,
            ):
                continue

            # Only look after label.
            if box["cy"] < label_box["cy"] - 20:
                continue

            dy = (
                box["cy"]
                - label_box["cy"]
            )

            if dy > 260:
                continue

            dx = (
                box["cx"]
                - label_box["cx"]
            )

            # Same line is strongest.
            if _same_line(
                label,
                candidate,
            ):

                if dx < -80:
                    continue

                score = (
                    abs(dy) * 2
                    + max(0, box["x1"] - label_box["x2"])
                )

            else:

                score = (
                    dy * 2
                    + abs(dx) * 0.5
                    + 80
                )

            if _looks_like_company(text):
                score -= 100

            candidates.append(
                (
                    score,
                    box["cy"],
                    box["cx"],
                    text,
                )
            )

        if candidates:

            candidates.sort(
                key=lambda x: x[0]
            )

            # Take the best candidate first.
            best = candidates[0][3]

            if len(best) >= 3:
                return _clean_text(best)

    return None


def _extract_manufacturer(
    detections: list[dict[str, Any]]
) -> str | None:

    return _extract_company_after_label(
        detections,
        ROLE_LABELS["manufacturer"],
    )


def _extract_packer(
    detections: list[dict[str, Any]]
) -> str | None:

    return _extract_company_after_label(
        detections,
        ROLE_LABELS["packer"],
    )


def _extract_marketer(
    detections: list[dict[str, Any]]
) -> str | None:

    return _extract_company_after_label(
        detections,
        ROLE_LABELS["marketer"],
    )


def _extract_importer(
    detections: list[dict[str, Any]]
) -> str | None:

    return _extract_company_after_label(
        detections,
        ROLE_LABELS["importer"],
    )


# ============================================================
# ADDRESS
# ============================================================

def _looks_like_address(text: str) -> bool:

    text_upper = text.upper()

    strong_keywords = [
        "ROAD",
        "STREET",
        "LANE",
        "NAGAR",
        "COLONY",
        "INDUSTRIAL",
        "ESTATE",
        "PLOT",
        "SECTOR",
        "DISTRICT",
        "STATE",
        "HARYANA",
        "WEST BENGAL",
        "MAHARASHTRA",
        "DELHI",
        "KARNATAKA",
        "TAMIL NADU",
        "UTTAR PRADESH",
        "GUJARAT",
        "RAJASTHAN",
        "INDIA",
        "PIN",
        "P.O.",
        "POST",
    ]

    if any(
        keyword in text_upper
        for keyword in strong_keywords
    ):
        return True

    if re.search(
        PIN_PATTERN,
        text,
    ):
        return True

    # Address-like combination:
    # contains number + several words.
    if (
        re.search(r"\d", text)
        and len(text.split()) >= 3
    ):
        return True

    return False


def _extract_address_after_label(
    detections: list[dict[str, Any]],
    labels: list[str],
) -> str | None:

    for i, item in enumerate(
        detections
    ):

        if not _matches_any(
            item["text"],
            labels,
        ):
            continue

        box = item.get("_bbox")

        if not box:
            continue

        candidates = []

        for j, candidate in enumerate(
            detections
        ):

            if j == i:
                continue

            candidate_box = candidate.get(
                "_bbox"
            )

            if not candidate_box:
                continue

            if (
                candidate_box["cy"]
                < box["cy"] - 20
            ):
                continue

            dy = (
                candidate_box["cy"]
                - box["cy"]
            )

            if dy > 320:
                continue

            text = candidate["text"].strip()

            if not text:
                continue

            if _matches_any(
                text,
                COMPANY_STOP_LABELS,
            ):
                continue

            if _looks_like_address(text):

                score = (
                    dy
                    + abs(
                        candidate_box["cx"]
                        - box["cx"]
                    ) * 0.3
                )

                candidates.append(
                    (
                        score,
                        candidate_box["cy"],
                        candidate_box["cx"],
                        text,
                    )
                )

        if candidates:

            candidates.sort(
                key=lambda x: x[0]
            )

            selected = [
                item[3]
                for item in candidates[:5]
            ]

            return _clean_text(
                " ".join(selected)
            )

    return None


# ============================================================
# FSSAI / LICENCE
# ============================================================

def _extract_license(
    text: str
) -> str | None:

    patterns = [
        r"\bLIC\.?\s*NO\.?\s*[:\-]?\s*(\d{14})",
        r"\bLICENSE\s*(?:NO|NUMBER)?\.?\s*[:\-]?\s*(\d{14})",
        r"\bFSSAI\s*(?:LIC(?:ENSE)?\.?\s*)?(?:NO\.?)?\s*[:\-]?\s*(\d{14})",
    ]

    for pattern in patterns:

        match = re.search(
            pattern,
            text,
            re.IGNORECASE,
        )

        if match:
            return match.group(1)

    return None


def _extract_all_license_numbers(
    detections: list[dict[str, Any]]
) -> list[str]:

    numbers = []

    for item in detections:

        text = item["text"]

        # Explicit licence context.
        for pattern in (
            r"\bLIC\.?\s*NO\.?\s*[:\-]?\s*(\d{14})",
            r"\bLICENSE\s*(?:NO|NUMBER)?\.?\s*[:\-]?\s*(\d{14})",
            r"\bFSSAI\s*(?:LIC(?:ENSE)?\.?\s*)?(?:NO\.?)?\s*[:\-]?\s*(\d{14})",
        ):

            for match in re.finditer(
                pattern,
                text,
                re.IGNORECASE,
            ):

                number = match.group(1)

                if number not in numbers:
                    numbers.append(number)

    return numbers


# ============================================================
# COMPANY <-> FSSAI ASSOCIATION
# ============================================================

def _extract_license_associations(
    detections: list[dict[str, Any]]
) -> list[dict[str, Any]]:

    associations = []

    for i, item in enumerate(
        detections
    ):

        license_number = _extract_license(
            item["text"]
        )

        if not license_number:
            continue

        box = item.get("_bbox")

        nearest_company = None
        nearest_distance = float("inf")

        for j, candidate in enumerate(
            detections
        ):

            if i == j:
                continue

            candidate_box = candidate.get(
                "_bbox"
            )

            if not candidate_box:
                continue

            text = candidate["text"].strip()

            if not _looks_like_company(
                text
            ):
                continue

            distance = (
                abs(
                    candidate_box["cy"]
                    - box["cy"]
                )
                if box
                else 999999
            )

            if distance < nearest_distance:

                nearest_distance = distance
                nearest_company = text

        associations.append(
            {
                "company": nearest_company,
                "license_number": license_number,
                "source_detection": i,
            }
        )

    return associations


# ============================================================
# CONSUMER CARE
# ============================================================

def _extract_consumer_care(
    detections: list[dict[str, Any]]
) -> dict[str, Any]:

    labels = [
        r"\bCUSTOMER\s+CARE\b",
        r"\bCONSUMER\s+CARE\b",
        r"\bCONSUMER\s+COMPLAINT\b",
        r"\bTOLL\s*FREE\b",
        r"\bHELPLINE\b",
        r"\bHELP\s*LINE\b",
    ]

    label_indices = []

    for i, item in enumerate(
        detections
    ):

        if _matches_any(
            item["text"],
            labels,
        ):
            label_indices.append(i)

    phones = []
    emails = []

    # ----------------------------------------
    # Prefer numbers/emails near customer-care
    # ----------------------------------------

    for i in label_indices:

        label_box = detections[i].get(
            "_bbox"
        )

        if not label_box:
            continue

        for candidate in detections:

            candidate_box = candidate.get(
                "_bbox"
            )

            if not candidate_box:
                continue

            dy = abs(
                candidate_box["cy"]
                - label_box["cy"]
            )

            if dy > 280:
                continue

            phones.extend(
                re.findall(
                    PHONE_PATTERN,
                    candidate["text"],
                    re.IGNORECASE,
                )
            )

            emails.extend(
                re.findall(
                    EMAIL_PATTERN,
                    candidate["text"],
                    re.IGNORECASE,
                )
            )

    # ----------------------------------------
    # Fallback if label exists but proximity
    # missed values.
    # ----------------------------------------

    if label_indices and not phones:

        full_text = " ".join(
            item["text"]
            for item in detections
        )

        phones.extend(
            re.findall(
                PHONE_PATTERN,
                full_text,
                re.IGNORECASE,
            )
        )

    if label_indices and not emails:

        full_text = " ".join(
            item["text"]
            for item in detections
        )

        emails.extend(
            re.findall(
                EMAIL_PATTERN,
                full_text,
                re.IGNORECASE,
            )
        )

    phones = list(
        dict.fromkeys(
            phones
        )
    )

    emails = list(
        dict.fromkeys(
            emails
        )
    )

    return {
        "label_detected": bool(
            label_indices
        ),
        "phone_numbers": phones,
        "email_addresses": emails,
    }


# ============================================================
# COUNTRY OF ORIGIN
# ============================================================

def _extract_country_of_origin(
    detections: list[dict[str, Any]]
) -> str | None:

    labels = [
        r"\bCOUNTRY\s+OF\s+ORIGIN\b",
        r"\bMADE\s+IN\b",
        r"\bPRODUCT\s+OF\b",
    ]

    for i, item in enumerate(
        detections
    ):

        if not _matches_any(
            item["text"],
            labels,
        ):
            continue

        # Same detection.
        for pattern in labels:

            match = re.search(
                pattern
                + r"\s*[:\-]?\s*"
                r"([A-Za-z][A-Za-z\s]{2,40})",
                item["text"],
                re.IGNORECASE,
            )

            if match:

                value = _clean_text(
                    match.group(1)
                )

                if value:
                    return value

        # Nearby value.
        value = _find_nearby_value(
            detections,
            i,
            lambda text: (
                re.sub(
                    r"^(?:COUNTRY\s+OF\s+ORIGIN|MADE\s+IN|PRODUCT\s+OF)"
                    r"\s*[:\-]?\s*",
                    "",
                    text,
                    flags=re.IGNORECASE,
                ).strip()
                if re.sub(
                    r"^(?:COUNTRY\s+OF\s+ORIGIN|MADE\s+IN|PRODUCT\s+OF)"
                    r"\s*[:\-]?\s*",
                    "",
                    text,
                    flags=re.IGNORECASE,
                ).strip()
                else None
            ),
            max_vertical_distance=220,
        )

        if value:
            return value

    return None


# ============================================================
# PRODUCT NAME
# ============================================================

PRODUCT_EXCLUSION_PATTERNS = [
    r"\bMRP\b",
    r"\bNET\b",
    r"\bQUANTITY\b",
    r"\bWEIGHT\b",
    r"\bINGREDIENTS?\b",
    r"\bNUTRITION(?:AL)?\b",
    r"\bENERGY\b",
    r"\bPROTEIN\b",
    r"\bCARBOHYDRATE\b",
    r"\bFAT\b",
    r"\bSUGAR\b",
    r"\bSALT\b",
    r"\bSODIUM\b",
    r"\bMANUFACTURED\b",
    r"\bMANUFACTURER\b",
    r"\bMARKETED\b",
    r"\bPACKED\b",
    r"\bIMPORTER\b",
    r"\bCUSTOMER\s+CARE\b",
    r"\bCONSUMER\s+CARE\b",
    r"\bFSSAI\b",
    r"\bLIC\.?\s*NO\b",
    r"\bBATCH\b",
    r"\bLOT\b",
    r"\bUSE\s+BY\b",
    r"\bEXPIRY\b",
    r"\bBEST\s+BEFORE\b",
    r"\bDATE\b",
    r"\bCOUNTRY\s+OF\s+ORIGIN\b",
    r"\bMADE\s+IN\b",
    r"\bMARKETED\s+BY\b",
    r"\bMANUFACTURED\s+BY\b",
    r"\bPACKED\s+BY\b",
]


def _is_product_name_candidate(
    text: str
) -> bool:

    text = _clean_text(text)

    if len(text) < 2:
        return False

    if len(text) > 100:
        return False

    if _matches_any(
        text,
        PRODUCT_EXCLUSION_PATTERNS,
    ):
        return False

    # Pure numbers are not product names.
    if re.fullmatch(
        r"[\d\s./\-]+",
        text,
    ):
        return False

    # Email / phone / licence.
    if re.search(
        EMAIL_PATTERN,
        text,
        re.IGNORECASE,
    ):
        return False

    if re.fullmatch(
        PHONE_PATTERN,
        text,
        re.IGNORECASE,
    ):
        return False

    if re.fullmatch(
        LICENSE_PATTERN,
        text,
    ):
        return False

    return True


def _extract_product_name(
    detections: list[dict[str, Any]]
) -> str | None:

    candidates = []

    valid_boxes = [
        d["_bbox"]
        for d in detections
        if d.get("_bbox")
    ]

    max_height = (
        max(
            box["height"]
            for box in valid_boxes
        )
        if valid_boxes
        else 0
    )

    max_width = (
        max(
            box["width"]
            for box in valid_boxes
        )
        if valid_boxes
        else 0
    )

    for index, item in enumerate(
        detections
    ):

        text = item["text"]

        if not _is_product_name_candidate(
            text
        ):
            continue

        box = item.get("_bbox")

        score = 0.0

        # OCR confidence.
        score += (
            item["confidence"] * 20
        )

        if box:

            # Large text is often brand/product text.
            if max_height > 0:
                score += (
                    box["height"]
                    / max_height
                ) * 35

            if max_width > 0:
                score += (
                    box["width"]
                    / max_width
                ) * 10

            # Central / upper package area.
            # We do not assume a fixed image resolution.
            if box["cy"] >= 0:
                score += 5

            # Prominent short-to-medium labels.
            word_count = len(
                text.split()
            )

            if 1 <= word_count <= 7:
                score += 12

            # Avoid tiny legal/declaration text.
            if box["height"] < 12:
                score -= 15

        # Brand/product-like capitalization.
        uppercase_ratio = sum(
            1
            for c in text
            if c.isupper()
        ) / max(
            1,
            sum(
                1
                for c in text
                if c.isalpha()
            ),
        )

        if uppercase_ratio > 0.55:
            score += 5

        candidates.append(
            (
                score,
                index,
                text,
            )
        )

    if not candidates:
        return None

    candidates.sort(
        key=lambda x: x[0],
        reverse=True,
    )

    return candidates[0][2]


# ============================================================
# GENERIC LABELLED TEXT
# ============================================================

def _extract_labelled_text(
    detections: list[dict[str, Any]],
    label_patterns: list[str],
    max_distance: float = 220,
) -> str | None:

    for i, item in enumerate(
        detections
    ):

        if not _matches_any(
            item["text"],
            label_patterns,
        ):
            continue

        # Same detection.
        for pattern in label_patterns:

            match = re.search(
                pattern
                + r"\s*[:\-]?\s*(.+)$",
                item["text"],
                re.IGNORECASE,
            )

            if match:

                value = _clean_text(
                    match.group(1)
                )

                if value:
                    return value

        value = _find_nearby_value(
            detections,
            i,
            lambda text: (
                text
                if len(
                    _clean_text(text)
                ) >= 2
                else None
            ),
            max_vertical_distance=max_distance,
        )

        if value:
            return value

    return None


# ============================================================
# UNIT SALE PRICE
# ============================================================

def _extract_unit_sale_price(
    detections: list[dict[str, Any]]
) -> str | None:

    labels = [
        r"\bUNIT\s+SALE\s+PRICE\b",
        r"\bSALE\s+PRICE\s+PER\b",
        r"\bUNIT\s+PRICE\b",
        r"\bPRICE\s+PER\s+UNIT\b",
    ]

    def extract_unit_value(
        text: str,
    ) -> str | None:

        pattern = (
            r"(?:UNIT\s+SALE\s+PRICE|"
            r"SALE\s+PRICE\s+PER|"
            r"UNIT\s+PRICE|"
            r"PRICE\s+PER\s+UNIT)"
            r"\s*[:\-]?\s*"
            r"(?:₹|Rs\.?|INR)?\s*"
            r"([0-9]+(?:\.[0-9]{1,4})?)"
        )

        match = re.search(
            pattern,
            text,
            re.IGNORECASE,
        )

        if match:
            return match.group(1)

        return None

    for i, item in enumerate(
        detections
    ):

        value = extract_unit_value(
            item["text"]
        )

        if value:
            return value

        if _matches_any(
            item["text"],
            labels,
        ):

            value = _find_nearby_value(
                detections,
                i,
                lambda text: (
                    re.search(
                        r"(?:₹|Rs\.?|INR)?\s*"
                        r"([0-9]+(?:\.[0-9]{1,4})?)",
                        text,
                        re.IGNORECASE,
                    ).group(1)
                    if re.search(
                        r"(?:₹|Rs\.?|INR)?\s*"
                        r"([0-9]+(?:\.[0-9]{1,4})?)",
                        text,
                        re.IGNORECASE,
                    )
                    else None
                ),
                max_vertical_distance=220,
            )

            if value:
                return value

    return None


# ============================================================
# DIMENSIONS
# ============================================================

def _extract_dimensions(
    detections: list[dict[str, Any]]
) -> list[str]:

    dimensions = []

    for item in detections:

        matches = re.findall(
            DIMENSION_PATTERN,
            item["text"],
            re.IGNORECASE,
        )

        for match in matches:

            if match not in dimensions:
                dimensions.append(match)

    return dimensions


# ============================================================
# CONFIDENCE HELPERS
# ============================================================

def _field_confidence(
    detections: list[dict[str, Any]],
    value: Any,
    label_patterns: list[str] | None = None,
) -> float:

    if value is None:
        return 0.0

    if not detections:
        return 0.0

    if not label_patterns:
        return round(
            min(
                1.0,
                sum(
                    d["confidence"]
                    for d in detections
                )
                / len(detections),
            ),
            3,
        )

    matching = [
        d["confidence"]
        for d in detections
        if _matches_any(
            d["text"],
            label_patterns,
        )
    ]

    if matching:
        return round(
            min(
                1.0,
                max(matching),
            ),
            3,
        )

    return 0.60


# ============================================================
# MAIN EXTRACTION
# ============================================================

def extract_product_information(
    ocr_results: list[dict[str, Any]]
) -> dict[str, Any]:
    """
    Convert PaddleOCR detections into structured
    SmartLabel AI product information.

    IMPORTANT:
    This is an extraction layer.

    It does NOT determine whether the package is
    legally compliant.

    The downstream compliance engine must evaluate:
        - applicability
        - mandatory declarations
        - correctness
        - completeness
        - placement
        - readability
        - font size
        - exceptions
    """

    detections = _prepare_detections(
        ocr_results
    )

    # --------------------------------------------------------
    # Spatial ordering
    # --------------------------------------------------------

    spatial_detections = sorted(
        detections,
        key=lambda item: (
            item["_bbox"]["cy"]
            if item.get("_bbox")
            else 999999,

            item["_bbox"]["cx"]
            if item.get("_bbox")
            else 999999,
        ),
    )

    # --------------------------------------------------------
    # Raw OCR text
    # --------------------------------------------------------

    clean_text = _clean_text(
        " ".join(
            item["text"]
            for item in detections
        )
    )

    # --------------------------------------------------------
    # Extract fields
    # --------------------------------------------------------

    product_name = _extract_product_name(
        detections
    )

    generic_name = _extract_labelled_text(
        detections,
        [
            r"\bCOMMON\s+NAME\b",
            r"\bGENERIC\s+NAME\b",
            r"\bNAME\s+OF\s+COMMODITY\b",
            r"\bCOMMODITY\b",
        ],
    )

    mrp = _extract_mrp_from_detections(
        detections
    )

    net_quantity = _extract_quantity_from_detections(
        detections
    )

    unit_sale_price = _extract_unit_sale_price(
        detections
    )

    batch_number = _extract_batch_from_detections(
        detections
    )

    manufacture_date = _extract_manufacture_date(
        detections
    )

    use_by_date = _extract_use_by_date(
        detections
    )

    manufacturer = _extract_manufacturer(
        detections
    )

    packer = _extract_packer(
        detections
    )

    marketer = _extract_marketer(
        detections
    )

    importer = _extract_importer(
        detections
    )

    # --------------------------------------------------------
    # Addresses
    # --------------------------------------------------------

    manufacturer_address = _extract_address_after_label(
        detections,
        ROLE_LABELS["manufacturer"],
    )

    packer_address = _extract_address_after_label(
        detections,
        ROLE_LABELS["packer"],
    )

    importer_address = _extract_address_after_label(
        detections,
        ROLE_LABELS["importer"],
    )

    # --------------------------------------------------------
    # FSSAI
    # --------------------------------------------------------

    license_numbers = (
        _extract_all_license_numbers(
            detections
        )
    )

    license_number = (
        license_numbers[0]
        if license_numbers
        else None
    )

    license_associations = (
        _extract_license_associations(
            detections
        )
    )

    # --------------------------------------------------------
    # Consumer care
    # --------------------------------------------------------

    consumer_care = _extract_consumer_care(
        detections
    )

    # --------------------------------------------------------
    # Country
    # --------------------------------------------------------

    country_of_origin = (
        _extract_country_of_origin(
            detections
        )
    )

    # --------------------------------------------------------
    # Dimensions
    # --------------------------------------------------------

    dimensions = _extract_dimensions(
        detections
    )

    # --------------------------------------------------------
    # Basic validation
    # --------------------------------------------------------

    if mrp:

        try:
            if float(mrp) <= 0:
                mrp = None
        except (
            ValueError,
            TypeError,
        ):
            mrp = None

    if net_quantity:

        if not re.search(
            WEIGHT_PATTERN,
            net_quantity,
            re.IGNORECASE,
        ):
            net_quantity = None

    if batch_number:

        if (
            len(batch_number) < 3
            or _is_date_like(batch_number)
        ):
            batch_number = None

    # --------------------------------------------------------
    # Evidence / field confidence
    # --------------------------------------------------------

    field_confidence = {

        "product_name": _field_confidence(
            detections,
            product_name,
        ),

        "generic_name": _field_confidence(
            detections,
            generic_name,
            [
                r"\bCOMMON\s+NAME\b",
                r"\bGENERIC\s+NAME\b",
                r"\bNAME\s+OF\s+COMMODITY\b",
                r"\bCOMMODITY\b",
            ],
        ),

        "mrp": _field_confidence(
            detections,
            mrp,
            [
                r"\bMRP\b",
                r"\bMAXIMUM\s+RETAIL\s+PRICE\b",
            ],
        ),

        "net_quantity": _field_confidence(
            detections,
            net_quantity,
            [
                r"\bNET\b",
                r"\bNET\s+QUANTITY\b",
                r"\bNET\s+WEIGHT\b",
                r"\bN\.?\s*QTY\b",
            ],
        ),

        "manufacturer": _field_confidence(
            detections,
            manufacturer,
            ROLE_LABELS["manufacturer"],
        ),

        "packer": _field_confidence(
            detections,
            packer,
            ROLE_LABELS["packer"],
        ),

        "marketer": _field_confidence(
            detections,
            marketer,
            ROLE_LABELS["marketer"],
        ),

        "importer": _field_confidence(
            detections,
            importer,
            ROLE_LABELS["importer"],
        ),

        "batch_number": _field_confidence(
            detections,
            batch_number,
            [
                r"\bBATCH\b",
                r"\bLOT\b",
            ],
        ),

        "manufacture_date": _field_confidence(
            detections,
            manufacture_date,
            MANUFACTURE_LABELS,
        ),

        "use_by_date": _field_confidence(
            detections,
            use_by_date,
            EXPIRY_LABELS,
        ),

        "license_number": _field_confidence(
            detections,
            license_number,
            [
                r"\bFSSAI\b",
                r"\bLIC\.?\s*NO\b",
            ],
        ),

        "country_of_origin": _field_confidence(
            detections,
            country_of_origin,
            [
                r"\bCOUNTRY\s+OF\s+ORIGIN\b",
                r"\bMADE\s+IN\b",
            ],
        ),

        "unit_sale_price": _field_confidence(
            detections,
            unit_sale_price,
            [
                r"\bUNIT\s+SALE\s+PRICE\b",
                r"\bSALE\s+PRICE\s+PER\b",
                r"\bUNIT\s+PRICE\b",
            ],
        ),
    }

    # --------------------------------------------------------
    # Return
    # --------------------------------------------------------

    return {

        # ====================================================
        # PRODUCT
        # ====================================================

        "product_name": product_name,

        "generic_name": generic_name,

        # ====================================================
        # PRICE / QUANTITY
        # ====================================================

        "mrp": mrp,

        "unit_sale_price": unit_sale_price,

        "net_quantity": net_quantity,

        "dimensions": dimensions,

        # ====================================================
        # BUSINESS DETAILS
        # ====================================================

        "manufacturer": manufacturer,

        "manufacturer_address":
            manufacturer_address,

        "packer": packer,

        "packer_address":
            packer_address,

        "marketer": marketer,

        "importer": importer,

        "importer_address":
            importer_address,

        # ====================================================
        # TRACEABILITY
        # ====================================================

        "batch_number": batch_number,

        "manufacture_date":
            manufacture_date,

        "use_by_date":
            use_by_date,

        # ====================================================
        # LICENCE
        # ====================================================

        "license_number":
            license_number,

        "license_numbers":
            license_numbers,

        "license_associations":
            license_associations,

        # ====================================================
        # CONSUMER
        # ====================================================

        "consumer_care":
            consumer_care,

        # ====================================================
        # ORIGIN
        # ====================================================

        "country_of_origin":
            country_of_origin,

        # ====================================================
        # EXTRACTION CONFIDENCE
        # ====================================================

        "field_confidence":
            field_confidence,

        # ====================================================
        # DEBUG / EVIDENCE
        # ====================================================

        "raw_text":
            clean_text,

        "ocr_detections":
            spatial_detections,
    }