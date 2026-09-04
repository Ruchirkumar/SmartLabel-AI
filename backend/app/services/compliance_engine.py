import re
from datetime import datetime
from typing import Any, Dict, List, Optional


# ============================================================
# SMARTLABEL AI
# Legal Metrology (Packaged Commodities) Rules, 2011
# Compliance Engine
#
# This engine evaluates declarations detected through OCR /
# information extraction.
#
# Applicability-dependent and visual requirements are marked
# REVIEW when they cannot be reliably determined automatically.
#
# This engine does NOT provide an official legal determination.
# ============================================================


# ============================================================
# BASIC HELPERS
# ============================================================

def _clean(value: Any) -> Optional[str]:
    """Return a cleaned string or None."""

    if value is None:
        return None

    value = str(value).strip()

    if not value:
        return None

    if value.lower() in {
        "null",
        "none",
        "n/a",
        "na",
        "not available",
        "not detected",
        "unknown",
    }:
        return None

    return value


def _check_present(value: Any) -> bool:
    return _clean(value) is not None


def _parse_date(value: Any) -> Optional[datetime]:
    """
    Try common Indian label date formats.

    Supports:
        01/08/2026
        01-08-2026
        01.08.2026
        01/08/26
        01-08-26
        01.08.26
        01 08 2026
    """

    value = _clean(value)

    if not value:
        return None

    formats = [
        "%d/%m/%Y",
        "%d-%m-%Y",
        "%d.%m.%Y",
        "%d/%m/%y",
        "%d-%m-%y",
        "%d.%m.%y",
        "%d %m %Y",
    ]

    for fmt in formats:
        try:
            return datetime.strptime(value, fmt)
        except ValueError:
            continue

    return None


# ============================================================
# VALIDATORS
# ============================================================

def _valid_net_quantity(value: Any) -> bool:
    """
    Validate common metric quantity declarations.

    Examples:
        40g
        500 g
        1kg
        1 L
        250ml
    """

    value = _clean(value)

    if not value:
        return False

    pattern = re.compile(
        r"^\s*\d+(?:\.\d+)?\s*"
        r"(?:mg|g|kg|ml|l|litre|liter|litres|liters)"
        r"\s*$",
        re.IGNORECASE,
    )

    return bool(pattern.match(value))


def _valid_mrp(value: Any) -> bool:
    """
    Validate common MRP formats.

    Examples:
        299
        299.00
        Rs. 299
        ₹299
        INR 299
    """

    value = _clean(value)

    if not value:
        return False

    value = value.replace(",", "")

    pattern = re.compile(
        r"^(?:₹|rs\.?|inr)?\s*"
        r"\d+(?:\.\d{1,2})?$",
        re.IGNORECASE,
    )

    return bool(pattern.match(value))


def _valid_fssai(value: Any) -> bool:
    """
    FSSAI licence numbers are generally 14 digits.

    This is an optional food-product check and is not treated
    as a universal Legal Metrology declaration.
    """

    value = _clean(value)

    if not value:
        return False

    digits = re.sub(r"\D", "", value)

    return len(digits) == 14


def _valid_phone(value: Any) -> bool:
    """Basic Indian consumer-care telephone validation."""

    value = _clean(value)

    if not value:
        return False

    digits = re.sub(r"\D", "", value)

    return len(digits) >= 10


def _valid_email(value: Any) -> bool:
    """Basic email validation."""

    value = _clean(value)

    if not value:
        return False

    pattern = re.compile(
        r"^[^@\s]+@[^@\s]+\.[^@\s]+$"
    )

    return bool(pattern.match(value))


def _has_indian_metric_unit(value: Any) -> bool:
    """Check whether quantity uses a metric-style unit."""

    value = _clean(value)

    if not value:
        return False

    return bool(
        re.search(
            r"\b(?:mg|g|kg|ml|l|litre|liter|litres|liters)\b",
            value,
            re.IGNORECASE,
        )
    )


# ============================================================
# CHECK OBJECT
# ============================================================

def _make_check(
    rule_id: str,
    rule_name: str,
    status: str,
    message: str,
    field: Optional[str] = None,
    value: Any = None,
    requirement: Optional[str] = None,
) -> Dict[str, Any]:

    return {
        "rule_id": rule_id,
        "rule_name": rule_name,
        "requirement": requirement or rule_name,
        "status": status,
        "message": message,
        "field": field,
        "value": value,
    }


# ============================================================
# CORE RULES
# ============================================================

def check_product_name(data: Dict[str, Any]) -> Dict[str, Any]:

    value = data.get("product_name")

    if _check_present(value):
        return _make_check(
            "LM-001",
            "Product / common name",
            "PASS",
            "Product or common name was detected.",
            "product_name",
            value,
            "The package should declare the common or generic name of the commodity.",
        )

    return _make_check(
        "LM-001",
        "Product / common name",
        "FAIL",
        "Product or common name could not be detected.",
        "product_name",
        value,
        "The package should declare the common or generic name of the commodity.",
    )


def check_mrp(data: Dict[str, Any]) -> Dict[str, Any]:

    value = data.get("mrp")

    if not _check_present(value):
        return _make_check(
            "LM-002",
            "Maximum Retail Price",
            "FAIL",
            "Maximum Retail Price (MRP) could not be detected.",
            "mrp",
            value,
            "MRP should be declared in the prescribed manner and inclusive of applicable taxes.",
        )

    if _valid_mrp(value):
        return _make_check(
            "LM-002",
            "Maximum Retail Price",
            "PASS",
            f"MRP detected: {value}.",
            "mrp",
            value,
            "MRP should be declared in the prescribed manner and inclusive of applicable taxes.",
        )

    return _make_check(
        "LM-002",
        "Maximum Retail Price",
        "REVIEW",
        f"MRP was detected but its extracted format needs review: {value}.",
        "mrp",
        value,
        "MRP should be declared in the prescribed manner and inclusive of applicable taxes.",
    )


def check_net_quantity(data: Dict[str, Any]) -> Dict[str, Any]:

    value = data.get("net_quantity")

    if not _check_present(value):
        return _make_check(
            "LM-003",
            "Net quantity",
            "FAIL",
            "Net quantity could not be detected.",
            "net_quantity",
            value,
            "Net quantity should be declared using the applicable metric unit.",
        )

    if _valid_net_quantity(value):
        return _make_check(
            "LM-003",
            "Net quantity",
            "PASS",
            f"Net quantity detected: {value}.",
            "net_quantity",
            value,
            "Net quantity should be declared using the applicable metric unit.",
        )

    if _has_indian_metric_unit(value):
        return _make_check(
            "LM-003",
            "Net quantity",
            "REVIEW",
            f"Net quantity was detected but its numerical/unit format needs review: {value}.",
            "net_quantity",
            value,
            "Net quantity should be declared using the applicable metric unit.",
        )

    return _make_check(
        "LM-003",
        "Net quantity",
        "REVIEW",
        f"Quantity was detected but the unit could not be confidently validated: {value}.",
        "net_quantity",
        value,
        "Net quantity should be declared using the applicable metric unit.",
    )


def check_manufacturer(data: Dict[str, Any]) -> Dict[str, Any]:

    value = data.get("manufacturer")

    if _check_present(value):
        return _make_check(
            "LM-004",
            "Manufacturer / packer details",
            "PASS",
            "Manufacturer or packer details were detected.",
            "manufacturer",
            value,
            "The package should contain the prescribed manufacturer/packer/importer declaration, as applicable.",
        )

    return _make_check(
        "LM-004",
        "Manufacturer / packer details",
        "FAIL",
        "Manufacturer or packer details could not be detected.",
        "manufacturer",
        value,
        "The package should contain the prescribed manufacturer/packer/importer declaration, as applicable.",
    )


def check_marketer(data: Dict[str, Any]) -> Dict[str, Any]:

    value = data.get("marketer")

    if _check_present(value):
        return _make_check(
            "LM-005",
            "Marketer details",
            "PASS",
            "Marketer details were detected.",
            "marketer",
            value,
            "Where applicable, marketer information should be correctly declared.",
        )

    return _make_check(
        "LM-005",
        "Marketer details",
        "REVIEW",
        "Marketer details were not confidently detected. Applicability should be reviewed.",
        "marketer",
        value,
        "Where applicable, marketer information should be correctly declared.",
    )


def check_batch_number(data: Dict[str, Any]) -> Dict[str, Any]:

    value = data.get("batch_number")

    if _check_present(value):
        return _make_check(
            "LM-006",
            "Batch / Lot / Code",
            "PASS",
            f"Batch/Lot/Code information detected: {value}.",
            "batch_number",
            value,
            "Where applicable, batch/lot/code identification should be declared.",
        )

    return _make_check(
        "LM-006",
        "Batch / Lot / Code",
        "REVIEW",
        "Batch/Lot/Code information could not be detected. Applicability depends on the commodity.",
        "batch_number",
        value,
        "Where applicable, batch/lot/code identification should be declared.",
    )


def check_manufacture_date(data: Dict[str, Any]) -> Dict[str, Any]:

    value = data.get("manufacture_date")

    if not _check_present(value):
        return _make_check(
            "LM-007",
            "Date / month and year of manufacture or packing",
            "FAIL",
            "Manufacture/packing date information could not be detected.",
            "manufacture_date",
            value,
            "Applicable date/month/year information should be declared.",
        )

    parsed = _parse_date(value)

    if parsed:
        return _make_check(
            "LM-007",
            "Date / month and year of manufacture or packing",
            "PASS",
            f"Manufacture date detected: {value}.",
            "manufacture_date",
            value,
            "Applicable date/month/year information should be declared.",
        )

    month_year_pattern = re.compile(
        r"^(0?[1-9]|1[0-2])[\s/-]\d{4}$"
    )

    if month_year_pattern.match(value):
        return _make_check(
            "LM-007",
            "Date / month and year of manufacture or packing",
            "PASS",
            f"Month/year declaration detected: {value}.",
            "manufacture_date",
            value,
            "Applicable date/month/year information should be declared.",
        )

    return _make_check(
        "LM-007",
        "Date / month and year of manufacture or packing",
        "REVIEW",
        f"Manufacture/packing date was detected but its format could not be confidently validated: {value}.",
        "manufacture_date",
        value,
        "Applicable date/month/year information should be declared.",
    )


def check_expiry_date(data: Dict[str, Any]) -> Dict[str, Any]:

    value = data.get("use_by_date")

    if not _check_present(value):
        return _make_check(
            "LM-008",
            "Best before / Use-by declaration",
            "REVIEW",
            "Expiry, Use-by, Best-before or equivalent date was not detected. Applicability should be reviewed for the product category.",
            "use_by_date",
            value,
            "Where applicable, best-before/use-by information should be declared.",
        )

    parsed = _parse_date(value)

    if parsed:
        return _make_check(
            "LM-008",
            "Best before / Use-by declaration",
            "PASS",
            f"Expiry/Use-by date detected: {value}.",
            "use_by_date",
            value,
            "Where applicable, best-before/use-by information should be declared.",
        )

    return _make_check(
        "LM-008",
        "Best before / Use-by declaration",
        "REVIEW",
        f"Expiry/Use-by declaration was detected but could not be fully validated: {value}.",
        "use_by_date",
        value,
        "Where applicable, best-before/use-by information should be declared.",
    )


def check_date_order(data: Dict[str, Any]) -> Dict[str, Any]:

    mfg = _parse_date(data.get("manufacture_date"))
    expiry = _parse_date(data.get("use_by_date"))

    if not mfg or not expiry:
        return _make_check(
            "LM-009",
            "Manufacture and expiry consistency",
            "REVIEW",
            "Both valid manufacture and expiry dates are required for this consistency check.",
            requirement="Where both dates are applicable, the expiry/use-by date should not precede manufacture.",
        )

    if expiry >= mfg:
        return _make_check(
            "LM-009",
            "Manufacture and expiry consistency",
            "PASS",
            "Expiry/Use-by date is not earlier than the manufacture date.",
            requirement="Where both dates are applicable, the expiry/use-by date should not precede manufacture.",
        )

    return _make_check(
        "LM-009",
        "Manufacture and expiry consistency",
        "FAIL",
        "Expiry/Use-by date appears earlier than the manufacture date.",
        requirement="Where both dates are applicable, the expiry/use-by date should not precede manufacture.",
    )


# ============================================================
# FOOD-SPECIFIC CHECK
# ============================================================

def check_fssai_license(data: Dict[str, Any]) -> Dict[str, Any]:

    numbers = data.get("license_numbers")

    if not isinstance(numbers, list):
        numbers = []

    valid_numbers = []

    for number in numbers:

        if _valid_fssai(number):

            digits = re.sub(
                r"\D",
                "",
                str(number),
            )

            if digits not in valid_numbers:
                valid_numbers.append(digits)

    primary = data.get("license_number")

    if not valid_numbers and _valid_fssai(primary):

        valid_numbers.append(
            re.sub(
                r"\D",
                "",
                str(primary),
            )
        )

    if valid_numbers:

        return _make_check(
            "FOOD-001",
            "FSSAI licence number",
            "PASS",
            f"Detected {len(valid_numbers)} valid 14-digit FSSAI licence number(s).",
            "license_numbers",
            valid_numbers,
            "Food products may be subject to separate food-regulatory declaration requirements.",
        )

    return _make_check(
        "FOOD-001",
        "FSSAI licence number",
        "REVIEW",
        "No valid 14-digit FSSAI licence number was confidently detected. This is a food-specific check and should not automatically determine Legal Metrology compliance.",
        "license_numbers",
        numbers,
        "Food products may be subject to separate food-regulatory declaration requirements.",
    )


# ============================================================
# IMPORTED PRODUCT
# ============================================================

def check_importer(data: Dict[str, Any]) -> Dict[str, Any]:

    value = data.get("importer")
    is_imported = data.get("is_imported")

    if _check_present(value):

        return _make_check(
            "LM-011",
            "Importer details",
            "PASS",
            "Importer details were detected.",
            "importer",
            value,
            "Imported packages should contain the applicable importer declaration.",
        )

    if is_imported is True:

        return _make_check(
            "LM-011",
            "Importer details",
            "FAIL",
            "The product was identified as imported but importer details could not be detected.",
            "importer",
            value,
            "Imported packages should contain the applicable importer declaration.",
        )

    return _make_check(
        "LM-011",
        "Importer details",
        "REVIEW",
        "Importer information was not detected. Product import status was not established.",
        "importer",
        value,
        "Imported packages should contain the applicable importer declaration.",
    )


def check_country_of_origin(data: Dict[str, Any]) -> Dict[str, Any]:

    value = data.get("country_of_origin")
    is_imported = data.get("is_imported")

    if _check_present(value):

        return _make_check(
            "LM-012",
            "Country of origin",
            "PASS",
            f"Country of origin detected: {value}.",
            "country_of_origin",
            value,
            "Imported products should carry the applicable country-of-origin declaration.",
        )

    if is_imported is True:

        return _make_check(
            "LM-012",
            "Country of origin",
            "FAIL",
            "Product identified as imported but country of origin was not detected.",
            "country_of_origin",
            value,
            "Imported products should carry the applicable country-of-origin declaration.",
        )

    return _make_check(
        "LM-012",
        "Country of origin",
        "REVIEW",
        "Country of origin was not detected and import status could not be established.",
        "country_of_origin",
        value,
        "Imported products should carry the applicable country-of-origin declaration.",
    )


# ============================================================
# CONSUMER CARE
# ============================================================

def check_consumer_care(data: Dict[str, Any]) -> Dict[str, Any]:

    phone = data.get("consumer_care_phone")
    email = data.get("consumer_care_email")
    address = data.get("consumer_care_address")

    has_phone = _valid_phone(phone)
    has_email = _valid_email(email)
    has_address = _check_present(address)

    if has_phone or has_email or has_address:

        return _make_check(
            "LM-013",
            "Consumer care details",
            "PASS",
            "Consumer-care/contact information was detected.",
            "consumer_care",
            {
                "phone": phone,
                "email": email,
                "address": address,
            },
            "Applicable consumer-care/contact details should be declared.",
        )

    return _make_check(
        "LM-013",
        "Consumer care details",
        "FAIL",
        "Consumer-care/contact information could not be detected.",
        "consumer_care",
        None,
        "Applicable consumer-care/contact details should be declared.",
    )


# ============================================================
# UNIT SALE PRICE
# ============================================================

def check_unit_sale_price(data: Dict[str, Any]) -> Dict[str, Any]:

    value = data.get("unit_sale_price")

    if _check_present(value):

        return _make_check(
            "LM-014",
            "Unit sale price",
            "PASS",
            f"Unit sale price detected: {value}.",
            "unit_sale_price",
            value,
            "Unit sale price should be declared where applicable.",
        )

    return _make_check(
        "LM-014",
        "Unit sale price",
        "REVIEW",
        "Unit sale price was not detected. Applicability depends on package/product category and quantity.",
        "unit_sale_price",
        value,
        "Unit sale price should be declared where applicable.",
    )


# ============================================================
# DIMENSIONS
# ============================================================

def check_dimensions(data: Dict[str, Any]) -> Dict[str, Any]:

    value = data.get("dimensions")

    if _check_present(value):

        return _make_check(
            "LM-015",
            "Dimensions",
            "PASS",
            f"Dimension information detected: {value}.",
            "dimensions",
            value,
            "Applicable commodities/packages should declare prescribed dimensions.",
        )

    return _make_check(
        "LM-015",
        "Dimensions",
        "REVIEW",
        "Dimensions were not detected. This requirement is applicable only to relevant commodities/packages.",
        "dimensions",
        value,
        "Applicable commodities/packages should declare prescribed dimensions.",
    )


# ============================================================
# PACKER DETAILS
# ============================================================

def check_packer_details(data: Dict[str, Any]) -> Dict[str, Any]:

    value = data.get("packer")

    if _check_present(value):

        return _make_check(
            "LM-016",
            "Packer details",
            "PASS",
            "Packer details were detected.",
            "packer",
            value,
            "Where applicable, prescribed packer details should be declared.",
        )

    return _make_check(
        "LM-016",
        "Packer details",
        "REVIEW",
        "Separate packer details were not detected. Applicability depends on whether the manufacturer and packer are the same entity.",
        "packer",
        value,
        "Where applicable, prescribed packer details should be declared.",
    )


# ============================================================
# DECLARATION COMPLETENESS
# ============================================================

def check_declaration_completeness(
    data: Dict[str, Any],
) -> Dict[str, Any]:
    """
    High-level declaration completeness check.

    This does not replace individual rule checks.
    """

    required_candidates = {
        "product_name": data.get("product_name"),
        "mrp": data.get("mrp"),
        "net_quantity": data.get("net_quantity"),
        "manufacturer": data.get("manufacturer"),
    }

    missing = [
        field
        for field, value in required_candidates.items()
        if not _check_present(value)
    ]

    if not missing:

        return _make_check(
            "LM-017",
            "Core declaration completeness",
            "PASS",
            "Core product, MRP, quantity and manufacturer/packer declarations were detected.",
            requirement="Core mandatory package declarations should be present as applicable.",
        )

    return _make_check(
        "LM-017",
        "Core declaration completeness",
        "FAIL",
        "One or more core declarations were not detected: "
        + ", ".join(missing),
        requirement="Core mandatory package declarations should be present as applicable.",
    )


# ============================================================
# VISUAL RULES
# ============================================================

def check_declaration_readability(
    data: Dict[str, Any],
) -> Dict[str, Any]:

    visual_result = data.get("visual_compliance")

    if not visual_result:

        return _make_check(
            "VIS-001",
            "Declaration readability",
            "REVIEW",
            "OCR confirms text detection, but readability cannot be conclusively established without visual analysis.",
            requirement="Mandatory declarations should be clear and legible.",
        )

    value = visual_result.get("readability")

    if str(value).lower() in {
        "pass",
        "good",
        "clear",
        "readable",
    }:

        return _make_check(
            "VIS-001",
            "Declaration readability",
            "PASS",
            "Visual analysis indicates that declarations are readable.",
            requirement="Mandatory declarations should be clear and legible.",
        )

    if str(value).lower() in {
        "fail",
        "poor",
        "unreadable",
    }:

        return _make_check(
            "VIS-001",
            "Declaration readability",
            "FAIL",
            "Visual analysis indicates that one or more declarations may not be sufficiently readable.",
            requirement="Mandatory declarations should be clear and legible.",
        )

    return _make_check(
        "VIS-001",
        "Declaration readability",
        "REVIEW",
        "Visual readability result requires manual review.",
        requirement="Mandatory declarations should be clear and legible.",
    )


def check_declaration_visibility(
    data: Dict[str, Any],
) -> Dict[str, Any]:

    visual_result = data.get("visual_compliance")

    if not visual_result:

        return _make_check(
            "VIS-002",
            "Declaration visibility",
            "REVIEW",
            "Visibility and conspicuousness require image-based analysis.",
            requirement="Required declarations should be displayed in the prescribed visible manner.",
        )

    value = visual_result.get("visibility")

    if str(value).lower() in {
        "pass",
        "good",
        "visible",
        "clear",
    }:

        return _make_check(
            "VIS-002",
            "Declaration visibility",
            "PASS",
            "Visual analysis indicates that declarations are visible.",
            requirement="Required declarations should be displayed in the prescribed visible manner.",
        )

    if str(value).lower() in {
        "fail",
        "poor",
        "hidden",
        "obscured",
    }:

        return _make_check(
            "VIS-002",
            "Declaration visibility",
            "FAIL",
            "Visual analysis indicates that one or more declarations may be obscured or insufficiently visible.",
            requirement="Required declarations should be displayed in the prescribed visible manner.",
        )

    return _make_check(
        "VIS-002",
        "Declaration visibility",
        "REVIEW",
        "Visual visibility result requires manual review.",
        requirement="Required declarations should be displayed in the prescribed visible manner.",
    )


def check_font_size(
    data: Dict[str, Any],
) -> Dict[str, Any]:

    visual_result = data.get("visual_compliance")

    if not visual_result:

        return _make_check(
            "VIS-003",
            "Declaration font size",
            "REVIEW",
            "Font size cannot be reliably determined from OCR alone. Image scale/calibration is required.",
            requirement="Mandatory declarations must satisfy the applicable minimum character-height requirements.",
        )

    value = visual_result.get("font_size")

    if value is None:

        return _make_check(
            "VIS-003",
            "Declaration font size",
            "REVIEW",
            "Font-size measurement was not available.",
            requirement="Mandatory declarations must satisfy the applicable minimum character-height requirements.",
        )

    return _make_check(
        "VIS-003",
        "Declaration font size",
        "REVIEW",
        f"Measured font-size result requires comparison with the applicable package/category threshold: {value}.",
        "font_size",
        value,
        "Mandatory declarations must satisfy the applicable minimum character-height requirements.",
    )


# ============================================================
# SCORE + RISK
# ============================================================

def _calculate_risk(
    pass_count: int,
    fail_count: int,
    review_count: int,
    total: int,
) -> str:

    if total == 0:
        return "UNKNOWN"

    fail_ratio = fail_count / total
    review_ratio = review_count / total

    if fail_count >= 3 or fail_ratio >= 0.30:
        return "HIGH"

    if fail_count > 0:
        return "MEDIUM"

    if review_ratio >= 0.30:
        return "MEDIUM"

    return "LOW"


def _recommendations(
    checks: List[Dict[str, Any]],
) -> List[str]:

    recommendations = []

    for check in checks:

        status = check.get("status")
        rule_name = check.get("rule_name")
        message = check.get("message")

        if status == "FAIL":

            recommendations.append(
                f"Review and correct the {rule_name} declaration. "
                f"Finding: {message}"
            )

        elif status == "REVIEW":

            recommendations.append(
                f"Manually verify the {rule_name}. "
                f"Finding: {message}"
            )

    # Remove duplicates while preserving order.

    unique = []

    for item in recommendations:

        if item not in unique:
            unique.append(item)

    return unique


# ============================================================
# MAIN ENGINE
# ============================================================

def run_compliance_checks(
    product_information: Dict[str, Any],
) -> Dict[str, Any]:

    """
    Run SmartLabel AI compliance checks.

    Important:
        This engine evaluates detectable declarations and
        configured rules. It does NOT independently certify
        legal compliance.

    OCR-based checks:
        - declarations
        - values
        - dates
        - quantity
        - MRP
        - contact information

    Visual checks:
        - readability
        - visibility
        - font size

    Conditional requirements:
        - importer
        - country of origin
        - unit sale price
        - dimensions
        - best-before/use-by
        - batch/lot
        - marketer/packer
    """

    if not isinstance(product_information, dict):

        raise ValueError(
            "product_information must be a dictionary."
        )

    checks: List[Dict[str, Any]] = [

        # ----------------------------------------------------
        # CORE DECLARATIONS
        # ----------------------------------------------------

        check_product_name(
            product_information
        ),

        check_mrp(
            product_information
        ),

        check_net_quantity(
            product_information
        ),

        check_manufacturer(
            product_information
        ),

        check_marketer(
            product_information
        ),

        check_packer_details(
            product_information
        ),

        check_batch_number(
            product_information
        ),

        check_manufacture_date(
            product_information
        ),

        check_expiry_date(
            product_information
        ),

        check_date_order(
            product_information
        ),

        # ----------------------------------------------------
        # IMPORTED PRODUCT
        # ----------------------------------------------------

        check_importer(
            product_information
        ),

        check_country_of_origin(
            product_information
        ),

        # ----------------------------------------------------
        # CONSUMER / PRICE / QUANTITY
        # ----------------------------------------------------

        check_consumer_care(
            product_information
        ),

        check_unit_sale_price(
            product_information
        ),

        check_dimensions(
            product_information
        ),

        # ----------------------------------------------------
        # COMPLETENESS
        # ----------------------------------------------------

        check_declaration_completeness(
            product_information
        ),

        # ----------------------------------------------------
        # VISUAL COMPLIANCE
        # ----------------------------------------------------

        check_declaration_readability(
            product_information
        ),

        check_declaration_visibility(
            product_information
        ),

        check_font_size(
            product_information
        ),

        # ----------------------------------------------------
        # FOOD-SPECIFIC OPTIONAL CHECK
        # ----------------------------------------------------

        check_fssai_license(
            product_information
        ),
    ]

    # ========================================================
    # COUNTS
    # ========================================================

    pass_count = sum(
        1
        for check in checks
        if check["status"] == "PASS"
    )

    fail_count = sum(
        1
        for check in checks
        if check["status"] == "FAIL"
    )

    review_count = sum(
        1
        for check in checks
        if check["status"] == "REVIEW"
    )

    total = len(checks)

    # ========================================================
    # SCORE
    # ========================================================

    score = (
        round(
            (pass_count / total) * 100
        )
        if total
        else 0
    )

    # ========================================================
    # OVERALL STATUS
    # ========================================================

    if fail_count > 0:

        overall_status = "NON_COMPLIANT"

    elif review_count > 0:

        overall_status = "REVIEW_REQUIRED"

    else:

        overall_status = "COMPLIANT"

    # ========================================================
    # RISK
    # ========================================================

    risk_level = _calculate_risk(
        pass_count,
        fail_count,
        review_count,
        total,
    )

    # ========================================================
    # RECOMMENDATIONS
    # ========================================================

    recommendations = _recommendations(
        checks
    )

    # ========================================================
    # CONFIDENCE
    # ========================================================

    confidence = (
        round(
            pass_count / total,
            2,
        )
        if total
        else 0
    )

    # ========================================================
    # RESULT
    # ========================================================

    return {
        "overall_status": overall_status,

        # Main score used by frontend/PDF.
        "score": score,

        # Alias used by database/backend.
        "compliance_score": score,

        "risk_level": risk_level,

        "confidence": confidence,

        "summary": {
            "total_checks": total,
            "passed": pass_count,
            "failed": fail_count,
            "review_required": review_count,
        },

        "checks": checks,

        # Alias used by PDF generator.
        "findings": checks,

        "recommendations": recommendations,

        "disclaimer": (
            "This automated result evaluates detected label "
            "declarations and configured rules based on the "
            "Legal Metrology (Packaged Commodities) Rules, "
            "2011 and applicable amendments. Results requiring "
            "product-category applicability, visual assessment, "
            "or legal interpretation should be manually reviewed. "
            "This system is not a substitute for an official "
            "legal or regulatory determination."
        ),
    }


# ============================================================
# API ALIAS
# ============================================================

check_compliance = run_compliance_checks