import re
from typing import Any


# ============================================================
# BASIC HELPERS
# ============================================================

def _clean_text(text: str) -> str:
    """Normalize OCR text for easier matching."""
    text = str(text or "")
    text = text.replace("\n", " ")
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def _normalize_ocr_text(text: str) -> str:
    """Normalize common OCR mistakes and label variations."""

    text = _clean_text(text)

    replacements = {
        "M.R.P.": "MRP",
        "M.R.P": "MRP",
        "M R P": "MRP",

        "LIC. NO.": "LIC NO",
        "LIC. NO": "LIC NO",
        "LIC.NO": "LIC NO",

        "BATCH NO.": "BATCH NO",
        "BATCH NO": "BATCH NO",

        "LOT NO.": "LOT NO",
        "LOT NO": "LOT NO",

        "USE BY DATE:": "USE BY DATE",
        "DATE OF EXPIRY:": "DATE OF EXPIRY",
        "DATE OF EXPIRY": "DATE OF EXPIRY",

        "DATE OF MFG:": "DATE OF MFG",
        "DATE OF MANUFACTURE:": "DATE OF MANUFACTURE",

        "PACKED BY": "PACKED BY",
        "PACKED AT": "PACKED AT",

        "MARKETED BY": "MARKETED BY",
        "MANUFACTURED BY": "MANUFACTURED BY",

        "NET QTY": "NET QUANTITY",
        "NET WT": "NET WEIGHT",

        "CUST CARE": "CUSTOMER CARE",
        "CUSTOMER CARE NO": "CUSTOMER CARE",
        "CONSUMER CARE": "CUSTOMER CARE",
    }

    for old, new in replacements.items():
        text = text.replace(old, new)

    return text


# ============================================================
# BOUNDING BOX
# ============================================================

def _bbox_info(bbox):
    """Return x/y center and dimensions from PaddleOCR bbox."""

    if not bbox or len(bbox) < 4:
        return None

    try:
        xs = [float(point[0]) for point in bbox]
        ys = [float(point[1]) for point in bbox]

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

        try:
            confidence = float(
                item.get("confidence", 0)
            )
        except (TypeError, ValueError):
            confidence = 0.0

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
    r"\d{1,2}[/-]\d{1,2}[/-]\d{2,4}"
    r"\b"
)

MONTH_YEAR_PATTERN = (
    r"\b"
    r"(?:0?[1-9]|1[0-2])"
    r"[/-]"
    r"\d{2,4}"
    r"\b"
)

WEIGHT_PATTERN = (
    r"\b\d+(?:\.\d+)?\s*"
    r"(?:mg|g|kg|ml|l|"
    r"milligram|milligrams|"
    r"gram|grams|"
    r"kilogram|kilograms|"
    r"millilitre|millilitres|"
    r"milliliter|milliliters|"
    r"litre|litres|liter|liters)"
    r"\b"
)

DIMENSION_PATTERN = (
    r"\b"
    r"\d+(?:\.\d+)?"
    r"\s*(?:mm|cm|m)"
    r"(?:\s*[xX×]\s*"
    r"\d+(?:\.\d+)?"
    r"\s*(?:mm|cm|m))+"
    r"\b"
)

BATCH_PATTERN = (
    r"\b[A-Z0-9][A-Z0-9/\-]{3,30}\b"
)

LICENSE_PATTERN = (
    r"\b\d{8,20}\b"
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
# GENERIC EXTRACTORS
# ============================================================

def _extract_date(text: str) -> str | None:

    match = re.search(
        DATE_PATTERN,
        text,
        re.IGNORECASE,
    )

    if match:
        return match.group(0)

    return None


def _extract_month_year(text: str) -> str | None:

    match = re.search(
        MONTH_YEAR_PATTERN,
        text,
        re.IGNORECASE,
    )

    if match:
        return match.group(0)

    return None


def _extract_weight(text: str) -> str | None:

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


def _extract_mrp(text: str) -> str | None:

    text = _normalize_ocr_text(text)

    patterns = [

        # MRP ₹299
        (
            r"\bM\.?\s*R\.?\s*P\.?\b"
            r"\s*[:\-]?\s*"
            r"(?:₹|Rs\.?|INR)"
            r"\s*"
            r"([0-9]+(?:\.[0-9]{1,2})?)"
        ),

        # MRP 299
        (
            r"\bM\.?\s*R\.?\s*P\.?\b"
            r"\s*[:\-]?\s*"
            r"([0-9]+(?:\.[0-9]{1,2})?)"
        ),

        # MRP Rs 299
        (
            r"\bMRP\b"
            r".{0,20}?"
            r"(?:₹|Rs\.?|INR)"
            r"\s*"
            r"([0-9]+(?:\.[0-9]{1,2})?)"
        ),
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

    pattern = (
        r"(?:₹|Rs\.?|INR)"
        r"\s*"
        r"([0-9]+(?:\.[0-9]{1,2})?)"
    )

    match = re.search(
        pattern,
        text,
        re.IGNORECASE,
    )

    if match:
        return match.group(1)

    return None


# ============================================================
# BATCH / LOT
# ============================================================

def _extract_batch(text: str) -> str | None:

    text = _clean_text(text)

    cleaned = re.sub(
        r"\b(?:BATCH|LOT)\s*"
        r"(?:NO|NUMBER|CODE)?\.?"
        r"\s*[:\-]?\s*",
        "",
        text,
        flags=re.IGNORECASE,
    ).strip()

    if re.fullmatch(
        DATE_PATTERN,
        cleaned,
        re.IGNORECASE,
    ):
        return None

    candidates = re.findall(
        BATCH_PATTERN,
        cleaned,
        re.IGNORECASE,
    )

    for candidate in candidates:

        candidate = candidate.strip(
            " .,:;"
        )

        if (
            len(candidate) >= 4
            and any(
                char.isdigit()
                for char in candidate
            )
            and not re.fullmatch(
                DATE_PATTERN,
                candidate,
                re.IGNORECASE,
            )
        ):
            return candidate

    return None


# ============================================================
# LICENSE
# ============================================================

def _extract_license(text: str) -> str | None:

    patterns = [

        r"\bLIC\.?\s*NO\.?\s*[:\-]?\s*"
        r"(\d{8,20})",

        r"\bLICENSE\s*"
        r"(?:NO|NUMBER)?\.?\s*[:\-]?\s*"
        r"(\d{8,20})",

        r"\bFSSAI\s*"
        r"(?:LIC(?:ENSE)?\.?\s*)?"
        r"(?:NO\.?)?\s*[:\-]?\s*"
        r"(\d{8,20})",
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

    full_text = " ".join(
        item["text"]
        for item in detections
    )

    numbers = []

    patterns = [

        r"\bLIC\.?\s*NO\.?\s*[:\-]?\s*"
        r"(\d{8,20})",

        r"\bLICENSE\s*"
        r"(?:NO|NUMBER)?\.?\s*[:\-]?\s*"
        r"(\d{8,20})",

        r"\bFSSAI\s*"
        r"(?:LIC(?:ENSE)?\.?\s*)?"
        r"(?:NO\.?)?\s*[:\-]?\s*"
        r"(\d{8,20})",
    ]

    for pattern in patterns:

        for match in re.finditer(
            pattern,
            full_text,
            re.IGNORECASE,
        ):

            value = match.group(1)

            if value not in numbers:
                numbers.append(value)

    for item in detections:

        value = _extract_license(
            item["text"]
        )

        if value and value not in numbers:
            numbers.append(value)

    return numbers


# ============================================================
# SPATIAL HELPERS
# ============================================================

def _find_nearby_value(
    detections: list[dict[str, Any]],
    label_index: int,
    extractor,
    max_vertical_distance: float = 180,
) -> str | None:

    label = detections[label_index]

    value = extractor(
        label["text"]
    )

    if value:
        return value

    label_bbox = label.get("_bbox")

    if not label_bbox:
        return None

    candidates = []

    for i, candidate in enumerate(
        detections
    ):

        if i == label_index:
            continue

        candidate_bbox = candidate.get(
            "_bbox"
        )

        if not candidate_bbox:
            continue

        vertical_distance = abs(
            candidate_bbox["cy"]
            - label_bbox["cy"]
        )

        horizontal_distance = (
            candidate_bbox["cx"]
            - label_bbox["cx"]
        )

        if (
            vertical_distance
            > max_vertical_distance
        ):
            continue

        candidate_value = extractor(
            candidate["text"]
        )

        if not candidate_value:
            continue

        # Same line / value to right.
        if (
            vertical_distance
            <= max(
                25,
                label_bbox["height"] * 1.5,
            )
            and horizontal_distance > -30
        ):

            score = (
                vertical_distance
                + max(
                    0,
                    100 - horizontal_distance,
                )
            )

            candidates.append(
                (
                    score,
                    candidate_value,
                )
            )

        # Value below label.
        elif (
            candidate_bbox["cy"]
            > label_bbox["cy"]
            and vertical_distance
            <= max_vertical_distance
        ):

            score = (
                vertical_distance
                + 100
            )

            candidates.append(
                (
                    score,
                    candidate_value,
                )
            )

    if candidates:

        candidates.sort(
            key=lambda item: item[0]
        )

        return candidates[0][1]

    return None


# ============================================================
# MRP
# ============================================================

def _extract_mrp_from_detections(
    detections: list[dict[str, Any]]
) -> str | None:

    full_text = " ".join(
        item["text"]
        for item in detections
    )

    value = _extract_mrp(
        full_text
    )

    if value:
        return value

    for item in detections:

        value = _extract_mrp(
            item["text"]
        )

        if value:
            return value

    mrp_label_pattern = (
        r"\bM\.?\s*R\.?\s*P\.?\b"
        r"|\bM\s+R\s+P\b"
    )

    for i, item in enumerate(
        detections
    ):

        if not re.search(
            mrp_label_pattern,
            item["text"],
            re.IGNORECASE,
        ):
            continue

        value = _find_nearby_value(
            detections,
            i,
            _extract_mrp,
            max_vertical_distance=220,
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

    quantity_labels = [

        r"\bNET\s+QTY\b",
        r"\bNET\s+QUANTITY\b",
        r"\bNET\s+WT\b",
        r"\bNET\s+WEIGHT\b",
        r"\bNET\b",
        r"\bWEIGHT\b",
    ]

    for i, item in enumerate(
        detections
    ):

        if any(
            re.search(
                pattern,
                item["text"],
                re.IGNORECASE,
            )
            for pattern in quantity_labels
        ):

            value = _find_nearby_value(
                detections,
                i,
                _extract_weight,
                max_vertical_distance=220,
            )

            if value:
                return value

    full_text = " ".join(
        item["text"]
        for item in detections
    )

    value = _extract_weight(
        full_text
    )

    if value:
        return value

    return None


# ============================================================
# BATCH / LOT
# ============================================================

def _extract_batch_from_detections(
    detections: list[dict[str, Any]]
) -> str | None:

    for i, item in enumerate(
        detections
    ):

        if re.search(
            r"\bBATCH\s*(?:NO|NUMBER|CODE)?",
            item["text"],
            re.IGNORECASE,
        ):

            value = _find_nearby_value(
                detections,
                i,
                _extract_batch,
                max_vertical_distance=180,
            )

            if value:
                return value

    for i, item in enumerate(
        detections
    ):

        if re.search(
            r"\bLOT\s*(?:NO|NUMBER|CODE)?",
            item["text"],
            re.IGNORECASE,
        ):

            value = _find_nearby_value(
                detections,
                i,
                _extract_batch,
                max_vertical_distance=180,
            )

            if value:
                return value

    full_text = " ".join(
        item["text"]
        for item in detections
    )

    explicit_patterns = [

        r"\bBATCH\s*(?:NO|NUMBER|CODE)?\.?"
        r"\s*[:\-]?\s*"
        r"([A-Z0-9][A-Z0-9/\-]{3,30})",

        r"\bLOT\s*(?:NO|NUMBER|CODE)?\.?"
        r"\s*[:\-]?\s*"
        r"([A-Z0-9][A-Z0-9/\-]{3,30})",
    ]

    for pattern in explicit_patterns:

        match = re.search(
            pattern,
            full_text,
            re.IGNORECASE,
        )

        if match:

            value = match.group(1)

            if not re.fullmatch(
                DATE_PATTERN,
                value,
                re.IGNORECASE,
            ):
                return value

    return None


# ============================================================
# DATE OF MANUFACTURE
# ============================================================

def _extract_manufacture_date(
    detections: list[dict[str, Any]]
) -> str | None:

    manufacture_patterns = [

        r"DATE\s+OF\s+MANUFACTURE",
        r"DATE\s+OF\s+MFG",
        r"MANUFACTURE",
        r"MANUFACTUR",
        r"\bMFG\b",
        r"\bMFD\b",
        r"\bPKD\b",
        r"\bPACKED\s+ON\b",
    ]

    for i, item in enumerate(
        detections
    ):

        if any(
            re.search(
                pattern,
                item["text"],
                re.IGNORECASE,
            )
            for pattern in manufacture_patterns
        ):

            value = _extract_date(
                item["text"]
            )

            if value:
                return value

            value = _find_nearby_value(
                detections,
                i,
                _extract_date,
                max_vertical_distance=220,
            )

            if value:
                return value

    full_text = " ".join(
        item["text"]
        for item in detections
    )

    patterns = [

        r"DATE\s+OF\s+MANUFACTURE"
        r"\s*[:\-]?\s*("
        + DATE_PATTERN
        + r")",

        r"DATE\s+OF\s+MFG"
        r"\s*[:\-]?\s*("
        + DATE_PATTERN
        + r")",

        r"\bMFD\b"
        r"\s*[:\-]?\s*("
        + DATE_PATTERN
        + r")",

        r"\bPKD\b"
        r"\s*[:\-]?\s*("
        + DATE_PATTERN
        + r")",
    ]

    for pattern in patterns:

        match = re.search(
            pattern,
            full_text,
            re.IGNORECASE,
        )

        if match:
            return match.group(1)

    return None


# ============================================================
# EXPIRY / USE-BY / BEST-BEFORE
# ============================================================

def _extract_use_by_date(
    detections: list[dict[str, Any]]
) -> str | None:

    expiry_patterns = [

        r"\bUSE\s+BY\b",
        r"\bUSE\s+BEFORE\b",
        r"\bEXPIRY\b",
        r"\bEXPIRY\s+DATE\b",
        r"\bDATE\s+OF\s+EXPIRY\b",
        r"\bDATE\s+OF\s+EXP\b",
        r"\bBEST\s+BEFORE\b",
        r"\bBEST\s+BEFORE\s+DATE\b",
    ]

    for i, item in enumerate(
        detections
    ):

        if any(
            re.search(
                pattern,
                item["text"],
                re.IGNORECASE,
            )
            for pattern in expiry_patterns
        ):

            value = _extract_date(
                item["text"]
            )

            if value:
                return value

            value = _find_nearby_value(
                detections,
                i,
                _extract_date,
                max_vertical_distance=240,
            )

            if value:
                return value

            # Some products use month/year.
            value = _find_nearby_value(
                detections,
                i,
                _extract_month_year,
                max_vertical_distance=240,
            )

            if value:
                return value

    full_text = " ".join(
        item["text"]
        for item in detections
    )

    full_text = _normalize_ocr_text(
        full_text
    )

    patterns = [

        r"DATE\s+OF\s+EXPIRY"
        r"\s*[:\-]?\s*("
        + DATE_PATTERN
        + r")",

        r"EXPIRY\s+DATE"
        r"\s*[:\-]?\s*("
        + DATE_PATTERN
        + r")",

        r"USE\s+BY"
        r"\s*[:\-]?\s*("
        + DATE_PATTERN
        + r")",

        r"BEST\s+BEFORE"
        r"\s*[:\-]?\s*("
        + DATE_PATTERN
        + r")",

        r"EXPIRY"
        r"\s*[:\-]?\s*("
        + DATE_PATTERN
        + r")",
    ]

    for pattern in patterns:

        match = re.search(
            pattern,
            full_text,
            re.IGNORECASE,
        )

        if match:
            return match.group(1)

    return None


# ============================================================
# MANUFACTURER / PACKER / IMPORTER
# ============================================================

def _extract_company_after_label(
    detections: list[dict[str, Any]],
    label_patterns: list[str],
) -> str | None:

    stop_patterns = [

        r"\bMARKETED\s+BY\b",
        r"\bMANUFACTURED\s+BY\b",
        r"\bMANUFACTURER\b",
        r"\bPACKED\s+BY\b",
        r"\bPACKER\b",
        r"\bIMPORTER\b",

        r"\bBATCH\b",
        r"\bLOT\b",
        r"\bDATE\b",
        r"\bUSE\s+BY\b",
        r"\bEXPIRY\b",
        r"\bMRP\b",
        r"\bLIC\.?\s*NO\b",
        r"\bFSSAI\b",
        r"\bNET\s+(?:QTY|QUANTITY|WEIGHT)\b",
        r"\bINGREDIENT\b",
        r"\bCOMMODITY\b",
        r"\bCUSTOMER\s+CARE\b",
    ]

    for i, item in enumerate(
        detections
    ):

        if not any(
            re.search(
                pattern,
                item["text"],
                re.IGNORECASE,
            )
            for pattern in label_patterns
        ):
            continue

        label_bbox = item.get(
            "_bbox"
        )

        if not label_bbox:
            continue

        parts = []

        for j, candidate in enumerate(
            detections
        ):

            if j == i:
                continue

            candidate_bbox = candidate.get(
                "_bbox"
            )

            if not candidate_bbox:
                continue

            if (
                candidate_bbox["cy"]
                < label_bbox["cy"] - 25
            ):
                continue

            distance = (
                candidate_bbox["cy"]
                - label_bbox["cy"]
            )

            if distance > 280:
                continue

            candidate_text = (
                candidate["text"].strip()
            )

            if not candidate_text:
                continue

            if any(
                re.search(
                    pattern,
                    candidate_text,
                    re.IGNORECASE,
                )
                for pattern in stop_patterns
            ):
                continue

            if re.fullmatch(
                r"[0-9.\s%]+",
                candidate_text,
            ):
                continue

            parts.append(
                (
                    candidate_bbox["cy"],
                    candidate_bbox["cx"],
                    candidate_text,
                )
            )

        if parts:

            parts.sort(
                key=lambda x: (
                    x[0],
                    x[1],
                )
            )

            text = " ".join(
                part[2]
                for part in parts[:6]
            )

            text = _clean_text(text)

            if len(text) >= 5:
                return text

    return None


def _extract_manufacturer(
    detections: list[dict[str, Any]]
) -> str | None:

    return _extract_company_after_label(
        detections,
        [
            r"\bMANUFACTURED\s+BY\b",
            r"\bMANUFACTURER\b",
            r"\bMFD\s+BY\b",
        ],
    )


def _extract_packer(
    detections: list[dict[str, Any]]
) -> str | None:

    return _extract_company_after_label(
        detections,
        [
            r"\bPACKED\s+BY\b",
            r"\bPACKER\b",
            r"\bPACKED\s+AT\b",
        ],
    )


def _extract_marketer(
    detections: list[dict[str, Any]]
) -> str | None:

    return _extract_company_after_label(
        detections,
        [
            r"\bMARKETED\s+BY\b",
            r"\bMARKETER\b",
        ],
    )


def _extract_importer(
    detections: list[dict[str, Any]]
) -> str | None:

    return _extract_company_after_label(
        detections,
        [
            r"\bIMPORTED\s+BY\b",
            r"\bIMPORTER\b",
        ],
    )


# ============================================================
# ADDRESS
# ============================================================

def _looks_like_address(text: str) -> bool:

    text_upper = text.upper()

    address_keywords = [
        "ROAD",
        "RD",
        "STREET",
        "ST",
        "LANE",
        "LN",
        "NAGAR",
        "COLONY",
        "INDUSTRIAL",
        "ESTATE",
        "PLOT",
        "SECTOR",
        "DISTRICT",
        "DIST",
        "STATE",
        "INDIA",
        "PIN",
    ]

    if any(
        keyword in text_upper
        for keyword in address_keywords
    ):
        return True

    if re.search(
        PIN_PATTERN,
        text,
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

        if not any(
            re.search(
                label,
                item["text"],
                re.IGNORECASE,
            )
            for label in labels
        ):
            continue

        bbox = item.get("_bbox")

        if not bbox:
            continue

        candidates = []

        for j, candidate in enumerate(
            detections
        ):

            if j == i:
                continue

            candidate_bbox = candidate.get(
                "_bbox"
            )

            if not candidate_bbox:
                continue

            if (
                candidate_bbox["cy"]
                < bbox["cy"] - 20
            ):
                continue

            distance = (
                candidate_bbox["cy"]
                - bbox["cy"]
            )

            if distance > 300:
                continue

            text = candidate["text"].strip()

            if not text:
                continue

            if _looks_like_address(
                text
            ):
                candidates.append(
                    (
                        candidate_bbox["cy"],
                        candidate_bbox["cx"],
                        text,
                    )
                )

        if candidates:

            candidates.sort(
                key=lambda x: (
                    x[0],
                    x[1],
                )
            )

            return _clean_text(
                " ".join(
                    x[2]
                    for x in candidates[:5]
                )
            )

    return None


# ============================================================
# CONSUMER CARE
# ============================================================

def _extract_consumer_care(
    detections: list[dict[str, Any]]
) -> dict[str, Any]:

    full_text = " ".join(
        item["text"]
        for item in detections
    )

    customer_care_patterns = [
        r"\bCUSTOMER\s+CARE\b",
        r"\bCONSUMER\s+CARE\b",
        r"\bCONSUMER\s+COMPLAINT\b",
        r"\bTOLL\s+FREE\b",
        r"\bHELPLINE\b",
        r"\bHELP\s*LINE\b",
    ]

    found_label = any(
        re.search(
            pattern,
            full_text,
            re.IGNORECASE,
        )
        for pattern in customer_care_patterns
    )

    phones = re.findall(
        PHONE_PATTERN,
        full_text,
        re.IGNORECASE,
    )

    emails = re.findall(
        EMAIL_PATTERN,
        full_text,
        re.IGNORECASE,
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
        "label_detected": found_label,
        "phone_numbers": phones,
        "email_addresses": emails,
    }


# ============================================================
# COUNTRY OF ORIGIN
# ============================================================

def _extract_country_of_origin(
    detections: list[dict[str, Any]]
) -> str | None:

    full_text = " ".join(
        item["text"]
        for item in detections
    )

    patterns = [

        r"COUNTRY\s+OF\s+ORIGIN"
        r"\s*[:\-]?\s*"
        r"([A-Za-z][A-Za-z\s]{2,40})",

        r"MADE\s+IN"
        r"\s*[:\-]?\s*"
        r"([A-Za-z][A-Za-z\s]{2,40})",

        r"PRODUCT\s+OF"
        r"\s*[:\-]?\s*"
        r"([A-Za-z][A-Za-z\s]{2,40})",
    ]

    for pattern in patterns:

        match = re.search(
            pattern,
            full_text,
            re.IGNORECASE,
        )

        if match:

            value = _clean_text(
                match.group(1)
            )

            # Avoid swallowing unrelated fields.
            value = re.split(
                r"\b(?:MRP|BATCH|LOT|"
                r"NET|DATE|EXPIRY|"
                r"FSSAI|LIC)\b",
                value,
                flags=re.IGNORECASE,
            )[0].strip()

            if value:
                return value

    return None


# ============================================================
# GENERIC COMMODITY / PRODUCT NAME
# ============================================================

def _extract_product_name(
    detections: list[dict[str, Any]]
) -> str | None:

    product_keywords = [

        "OATS",
        "WAFERS",
        "CHIPS",
        "POTATO CHIPS",
        "VEGGIE STIX",
        "BISCUIT",
        "BISCUITS",
        "NOODLES",
        "COOKIES",
        "JUICE",
        "DRINK",
        "SNACK",
        "CEREAL",
        "CEREALS",
        "FLOUR",
        "RICE",
        "SUGAR",
        "SALT",
        "TEA",
        "COFFEE",
        "BREAD",
        "MILK",
        "BUTTER",
        "BISCUIT",
    ]

    candidates = []

    for item in detections:

        text = item["text"].strip()

        if len(text) < 2:
            continue

        upper = text.upper()

        score = 0

        for keyword in product_keywords:

            if keyword in upper:
                score += 10

        bbox = item.get(
            "_bbox"
        )

        if bbox:

            if bbox["height"] >= 40:
                score += 4

            if bbox["width"] >= 150:
                score += 2

        score += item["confidence"]

        if score > 0:

            candidates.append(
                (
                    score,
                    text,
                )
            )

    if candidates:

        candidates.sort(
            key=lambda x: x[0],
            reverse=True,
        )

        return candidates[0][1]

    return None


# ============================================================
# GENERIC FIELD FINDER
# ============================================================

def _extract_labelled_text(
    detections: list[dict[str, Any]],
    label_patterns: list[str],
    max_distance: float = 220,
) -> str | None:

    for i, item in enumerate(
        detections
    ):

        if not any(
            re.search(
                pattern,
                item["text"],
                re.IGNORECASE,
            )
            for pattern in label_patterns
        ):
            continue

        bbox = item.get(
            "_bbox"
        )

        if not bbox:
            continue

        candidates = []

        for j, candidate in enumerate(
            detections
        ):

            if j == i:
                continue

            candidate_bbox = candidate.get(
                "_bbox"
            )

            if not candidate_bbox:
                continue

            dy = abs(
                candidate_bbox["cy"]
                - bbox["cy"]
            )

            dx = (
                candidate_bbox["cx"]
                - bbox["cx"]
            )

            if dy > max_distance:
                continue

            if dx < -100:
                continue

            text = candidate["text"].strip()

            if not text:
                continue

            score = dy + abs(
                max(0, -dx)
            )

            candidates.append(
                (
                    score,
                    text,
                )
            )

        if candidates:

            candidates.sort(
                key=lambda x: x[0]
            )

            return candidates[0][1]

    return None


# ============================================================
# UNIT SALE PRICE
# ============================================================

def _extract_unit_sale_price(
    detections: list[dict[str, Any]]
) -> str | None:

    full_text = " ".join(
        item["text"]
        for item in detections
    )

    patterns = [

        r"(?:UNIT\s+SALE\s+PRICE)"
        r"\s*[:\-]?\s*"
        r"(?:₹|Rs\.?|INR)?\s*"
        r"([0-9]+(?:\.[0-9]{1,2})?)",

        r"(?:SALE\s+PRICE\s+PER)"
        r"\s*[:\-]?\s*"
        r"(?:₹|Rs\.?|INR)?\s*"
        r"([0-9]+(?:\.[0-9]{1,2})?)",
    ]

    for pattern in patterns:

        match = re.search(
            pattern,
            full_text,
            re.IGNORECASE,
        )

        if match:
            return match.group(1)

    return None


# ============================================================
# MAIN EXTRACTION
# ============================================================

def extract_product_information(
    ocr_results: list[dict[str, Any]]
) -> dict[str, Any]:
    """
    Convert PaddleOCR detections into structured product information.

    This extraction layer is designed for SmartLabel AI.

    It extracts:
        - Product / commodity name
        - MRP
        - Net quantity
        - Unit sale price
        - Manufacturer
        - Manufacturer address
        - Packer
        - Packer address
        - Importer
        - Importer address
        - Marketer
        - Batch / Lot number
        - Manufacture / packing date
        - Expiry / Use-by / Best-before
        - FSSAI licence numbers
        - Consumer care phone/email
        - Country of origin
        - Dimensions
        - Raw OCR text
        - OCR evidence

    NOTE:
    Extraction is NOT legal compliance by itself.
    The compliance engine must decide whether a declaration
    is mandatory, applicable, correctly formatted and readable.
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
    # Full OCR text
    # --------------------------------------------------------

    full_text = " ".join(
        item["text"]
        for item in detections
    )

    clean_text = _clean_text(
        full_text
    )

    # --------------------------------------------------------
    # Core declarations
    # --------------------------------------------------------

    product_name = (
        _extract_product_name(
            detections
        )
    )

    mrp = (
        _extract_mrp_from_detections(
            detections
        )
    )

    net_quantity = (
        _extract_quantity_from_detections(
            detections
        )
    )

    unit_sale_price = (
        _extract_unit_sale_price(
            detections
        )
    )

    batch_number = (
        _extract_batch_from_detections(
            detections
        )
    )

    manufacture_date = (
        _extract_manufacture_date(
            detections
        )
    )

    use_by_date = (
        _extract_use_by_date(
            detections
        )
    )

    # --------------------------------------------------------
    # Manufacturer / Packer / Importer
    # --------------------------------------------------------

    manufacturer = (
        _extract_manufacturer(
            detections
        )
    )

    packer = (
        _extract_packer(
            detections
        )
    )

    importer = (
        _extract_importer(
            detections
        )
    )

    marketer = (
        _extract_marketer(
            detections
        )
    )

    manufacturer_address = (
        _extract_address_after_label(
            detections,
            [
                r"\bMANUFACTURED\s+BY\b",
                r"\bMANUFACTURER\b",
                r"\bMFD\s+BY\b",
            ],
        )
    )

    packer_address = (
        _extract_address_after_label(
            detections,
            [
                r"\bPACKED\s+BY\b",
                r"\bPACKER\b",
                r"\bPACKED\s+AT\b",
            ],
        )
    )

    importer_address = (
        _extract_address_after_label(
            detections,
            [
                r"\bIMPORTED\s+BY\b",
                r"\bIMPORTER\b",
            ],
        )
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

    # --------------------------------------------------------
    # Consumer care
    # --------------------------------------------------------

    consumer_care = (
        _extract_consumer_care(
            detections
        )
    )

    # --------------------------------------------------------
    # Country of origin
    # --------------------------------------------------------

    country_of_origin = (
        _extract_country_of_origin(
            detections
        )
    )

    # --------------------------------------------------------
    # Dimensions
    # --------------------------------------------------------

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

    # --------------------------------------------------------
    # Generic commodity description
    # --------------------------------------------------------

    generic_name = (
        _extract_labelled_text(
            detections,
            [
                r"\bCOMMON\s+NAME\b",
                r"\bGENERIC\s+NAME\b",
                r"\bNAME\s+OF\s+COMMODITY\b",
                r"\bCOMMODITY\b",
            ],
        )
    )

    # --------------------------------------------------------
    # Quantity validation
    # --------------------------------------------------------

    if net_quantity:

        if not re.fullmatch(
            WEIGHT_PATTERN,
            net_quantity,
            re.IGNORECASE,
        ):
            net_quantity = None

    # --------------------------------------------------------
    # MRP validation
    # --------------------------------------------------------

    if mrp:

        try:

            mrp_value = float(
                mrp
            )

            if mrp_value <= 0:
                mrp = None

        except (
            ValueError,
            TypeError,
        ):

            mrp = None

    # --------------------------------------------------------
    # Batch validation
    # --------------------------------------------------------

    if batch_number:

        if (
            len(batch_number) < 4
            or not any(
                char.isdigit()
                for char in batch_number
            )
            or re.fullmatch(
                DATE_PATTERN,
                batch_number,
                re.IGNORECASE,
            )
        ):

            batch_number = None

    # --------------------------------------------------------
    # FSSAI validation
    # --------------------------------------------------------

    valid_license_numbers = []

    for number in license_numbers:

        digits = re.sub(
            r"\D",
            "",
            str(number),
        )

        if len(digits) == 14:

            if digits not in valid_license_numbers:
                valid_license_numbers.append(
                    digits
                )

    license_numbers = (
        valid_license_numbers
    )

    license_number = (
        license_numbers[0]
        if license_numbers
        else None
    )

    # --------------------------------------------------------
    # Return structured information
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

        # ====================================================
        # CONSUMER INFORMATION
        # ====================================================

        "consumer_care":
            consumer_care,

        # ====================================================
        # IMPORT INFORMATION
        # ====================================================

        "country_of_origin":
            country_of_origin,

        # ====================================================
        # DEBUG / EVIDENCE
        # ====================================================

        "raw_text":
            clean_text,

        "ocr_detections":
            spatial_detections,
    }