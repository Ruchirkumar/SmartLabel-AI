from pathlib import Path
from datetime import datetime
import re
import html

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
    PageBreak,
    Image,
)


REPORT_DIR = Path("reports")
REPORT_DIR.mkdir(parents=True, exist_ok=True)


def _safe_filename(filename: str) -> str:
    """
    Convert an uploaded filename into a safe PDF filename.
    """

    stem = Path(filename).stem

    stem = re.sub(
        r"[^A-Za-z0-9_-]+",
        "_",
        stem,
    )

    stem = stem.strip("_")

    if not stem:
        stem = "smartlabel_report"

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    return f"{stem}_{timestamp}.pdf"


def _value(value):
    """
    Safely convert values to displayable text.
    """

    if value is None:
        return "Not detected"

    if isinstance(value, list):
        if not value:
            return "Not detected"

        return ", ".join(str(item) for item in value)

    return str(value)


def _safe_paragraph_text(value) -> str:
    """
    Escape text before inserting it into a ReportLab Paragraph.
    """

    return html.escape(_value(value))


def _build_styles():
    """
    Create PDF styles.
    """

    styles = getSampleStyleSheet()

    title_style = ParagraphStyle(
        "ReportTitle",
        parent=styles["Title"],
        fontSize=20,
        leading=24,
        alignment=TA_CENTER,
        spaceAfter=8,
    )

    subtitle_style = ParagraphStyle(
        "ReportSubtitle",
        parent=styles["Normal"],
        fontSize=9,
        leading=12,
        alignment=TA_CENTER,
        spaceAfter=14,
    )

    heading_style = ParagraphStyle(
        "ReportHeading",
        parent=styles["Heading2"],
        fontSize=13,
        leading=16,
        spaceBefore=10,
        spaceAfter=7,
    )

    body_style = ParagraphStyle(
        "ReportBody",
        parent=styles["BodyText"],
        fontSize=9,
        leading=13,
    )

    small_style = ParagraphStyle(
        "ReportSmall",
        parent=styles["BodyText"],
        fontSize=7.5,
        leading=10,
    )

    return {
        "title": title_style,
        "subtitle": subtitle_style,
        "heading": heading_style,
        "body": body_style,
        "small": small_style,
    }


def _add_page_number(canvas, doc):
    """
    Add page number to every page.
    """

    canvas.saveState()

    page_number = canvas.getPageNumber()

    canvas.setFont(
        "Helvetica",
        8,
    )

    canvas.drawCentredString(
        A4[0] / 2,
        10 * mm,
        f"SmartLabel AI | Page {page_number}",
    )

    canvas.restoreState()


def _add_original_image(
    story,
    styles,
    filename: str,
    image_path: str,
):
    """
    Add the uploaded source image to the PDF as evidence.
    """

    if not image_path:
        return

    image_file = Path(image_path)

    if not image_file.exists():
        story.append(
            Paragraph(
                "<b>Evidence image:</b> Source image was not found "
                "on the server.",
                styles["small"],
            )
        )
        return

    story.append(
        Paragraph(
            "1. Original Label Image Evidence",
            styles["heading"],
        )
    )

    story.append(
        Paragraph(
            "The following image was provided as the source evidence "
            "for the automated SmartLabel AI compliance analysis.",
            styles["body"],
        )
    )

    story.append(Spacer(1, 6))

    try:
        evidence_image = Image(
            str(image_file)
        )

        max_width = 165 * mm
        max_height = 190 * mm

        width = evidence_image.imageWidth
        height = evidence_image.imageHeight

        if width <= 0 or height <= 0:
            raise ValueError("Invalid image dimensions")

        scale = min(
            max_width / width,
            max_height / height,
            1,
        )

        evidence_image.drawWidth = width * scale
        evidence_image.drawHeight = height * scale

        story.append(evidence_image)

        story.append(Spacer(1, 8))

        story.append(
            Paragraph(
                f"<b>Evidence file:</b> "
                f"{_safe_paragraph_text(filename)}",
                styles["small"],
            )
        )

    except Exception as exc:
        story.append(
            Paragraph(
                "<b>Evidence image could not be embedded.</b>",
                styles["small"],
            )
        )

        story.append(
            Paragraph(
                f"Reason: {_safe_paragraph_text(str(exc))}",
                styles["small"],
            )
        )


def generate_pdf_report(
    filename: str,
    product_information: dict,
    compliance_result: dict,
    quality_result: dict | None = None,
    image_path: str | None = None,
) -> str:
    """
    Generate a SmartLabel AI compliance screening report.

    Args:
        filename:
            Original uploaded image filename.

        product_information:
            OCR/extracted product information.

        compliance_result:
            Compliance engine result.

        quality_result:
            Optional image quality analysis result.

        image_path:
            Local filesystem path of the uploaded source image.
            This image will be embedded into the PDF as evidence.

    Returns:
        Relative path to generated PDF.
    """

    pdf_filename = _safe_filename(filename)

    pdf_path = REPORT_DIR / pdf_filename

    doc = SimpleDocTemplate(
        str(pdf_path),
        pagesize=A4,
        rightMargin=15 * mm,
        leftMargin=15 * mm,
        topMargin=15 * mm,
        bottomMargin=18 * mm,
        title="SmartLabel AI Compliance Report",
        author="SmartLabel AI",
    )

    styles = _build_styles()

    story = []

    # =========================================================
    # TITLE
    # =========================================================

    story.append(
        Paragraph(
            "SmartLabel AI",
            styles["title"],
        )
    )

    story.append(
        Paragraph(
            "Automated Legal Metrology Label Compliance Screening Report",
            styles["subtitle"],
        )
    )

    story.append(
        Paragraph(
            f"<b>Source Image:</b> "
            f"{_safe_paragraph_text(filename)}",
            styles["body"],
        )
    )

    story.append(
        Paragraph(
            f"<b>Generated:</b> "
            f"{datetime.now().strftime('%d-%m-%Y %H:%M:%S')}",
            styles["body"],
        )
    )

    story.append(Spacer(1, 8))

    # =========================================================
    # ORIGINAL IMAGE EVIDENCE
    # =========================================================

    if image_path:

        _add_original_image(
            story=story,
            styles=styles,
            filename=filename,
            image_path=image_path,
        )

        story.append(
            PageBreak()
        )

    # =========================================================
    # OVERALL RESULT
    # =========================================================

    story.append(
        Paragraph(
            "2. Overall Compliance Result",
            styles["heading"],
        )
    )

    overall_status = _value(
        compliance_result.get(
            "overall_status",
            "UNKNOWN",
        )
    )

    risk_level = _value(
        compliance_result.get(
            "risk_level",
            "UNKNOWN",
        )
    )

    confidence = compliance_result.get(
        "confidence",
        None,
    )

    if isinstance(confidence, (int, float)):

        # Support both:
        # 0.95 -> 95%
        # 95 -> 95%
        if confidence <= 1:
            confidence_text = f"{confidence * 100:.1f}%"
        else:
            confidence_text = f"{confidence:.1f}%"

    else:
        confidence_text = "Not available"

    overall_data = [
        ["Status", _safe_paragraph_text(overall_status)],
        ["Risk Level", _safe_paragraph_text(risk_level)],
        ["Confidence", confidence_text],
    ]

    overall_table = Table(
        overall_data,
        colWidths=[
            45 * mm,
            120 * mm,
        ],
    )

    overall_table.setStyle(
        TableStyle(
            [
                (
                    "BACKGROUND",
                    (0, 0),
                    (0, -1),
                    colors.HexColor("#E8EEF7"),
                ),
                (
                    "FONTNAME",
                    (0, 0),
                    (0, -1),
                    "Helvetica-Bold",
                ),
                (
                    "FONTNAME",
                    (1, 0),
                    (1, -1),
                    "Helvetica",
                ),
                (
                    "GRID",
                    (0, 0),
                    (-1, -1),
                    0.5,
                    colors.grey,
                ),
                (
                    "VALIGN",
                    (0, 0),
                    (-1, -1),
                    "MIDDLE",
                ),
                (
                    "TOPPADDING",
                    (0, 0),
                    (-1, -1),
                    6,
                ),
                (
                    "BOTTOMPADDING",
                    (0, 0),
                    (-1, -1),
                    6,
                ),
            ]
        )
    )

    story.append(
        overall_table
    )

    story.append(
        Spacer(1, 8)
    )

    # =========================================================
    # SUMMARY
    # =========================================================

    summary = compliance_result.get(
        "summary",
        compliance_result.get(
            "summary_text",
            None,
        ),
    )

    if isinstance(summary, dict):

        summary_data = [
            [
                "Total Checks",
                _safe_paragraph_text(
                    summary.get("total_checks")
                ),
            ],
            [
                "Passed",
                _safe_paragraph_text(
                    summary.get("passed")
                ),
            ],
            [
                "Failed",
                _safe_paragraph_text(
                    summary.get("failed")
                ),
            ],
            [
                "Review Required",
                _safe_paragraph_text(
                    summary.get("review_required")
                ),
            ],
        ]

        summary_table = Table(
            summary_data,
            colWidths=[
                65 * mm,
                100 * mm,
            ],
        )

        summary_table.setStyle(
            TableStyle(
                [
                    (
                        "BACKGROUND",
                        (0, 0),
                        (0, -1),
                        colors.HexColor("#F2F2F2"),
                    ),
                    (
                        "FONTNAME",
                        (0, 0),
                        (0, -1),
                        "Helvetica-Bold",
                    ),
                    (
                        "GRID",
                        (0, 0),
                        (-1, -1),
                        0.5,
                        colors.grey,
                    ),
                    (
                        "TOPPADDING",
                        (0, 0),
                        (-1, -1),
                        5,
                    ),
                    (
                        "BOTTOMPADDING",
                        (0, 0),
                        (-1, -1),
                        5,
                    ),
                ]
            )
        )

        story.append(
            summary_table
        )

    elif summary:

        story.append(
            Paragraph(
                f"<b>Summary:</b> "
                f"{_safe_paragraph_text(summary)}",
                styles["body"],
            )
        )

    # =========================================================
    # PRODUCT INFORMATION
    # =========================================================

    story.append(
        Paragraph(
            "3. Extracted Product Information",
            styles["heading"],
        )
    )

    product_fields = [
        ("Product Name", "product_name"),
        ("MRP", "mrp"),
        ("Net Quantity", "net_quantity"),
        ("Manufacturer", "manufacturer"),
        ("Marketer", "marketer"),
        ("Batch / Lot Number", "batch_number"),
        ("Date of Manufacture", "manufacture_date"),
        ("Expiry / Use-by Date", "use_by_date"),
        ("FSSAI Licence Number", "license_number"),
        ("All Licence Numbers", "license_numbers"),
    ]

    product_data = [
        [
            "Field",
            "Detected Value",
        ]
    ]

    for label, key in product_fields:

        product_data.append(
            [
                label,
                _safe_paragraph_text(
                    product_information.get(key)
                ),
            ]
        )

    product_table = Table(
        product_data,
        colWidths=[
            55 * mm,
            110 * mm,
        ],
        repeatRows=1,
    )

    product_table.setStyle(
        TableStyle(
            [
                (
                    "BACKGROUND",
                    (0, 0),
                    (-1, 0),
                    colors.HexColor("#D9E2F3"),
                ),
                (
                    "FONTNAME",
                    (0, 0),
                    (-1, 0),
                    "Helvetica-Bold",
                ),
                (
                    "GRID",
                    (0, 0),
                    (-1, -1),
                    0.4,
                    colors.grey,
                ),
                (
                    "VALIGN",
                    (0, 0),
                    (-1, -1),
                    "TOP",
                ),
                (
                    "TOPPADDING",
                    (0, 0),
                    (-1, -1),
                    5,
                ),
                (
                    "BOTTOMPADDING",
                    (0, 0),
                    (-1, -1),
                    5,
                ),
            ]
        )
    )

    story.append(
        product_table
    )

    # =========================================================
    # IMAGE QUALITY
    # =========================================================

    if quality_result:

        story.append(
            Paragraph(
                "4. Image Quality Analysis",
                styles["heading"],
            )
        )

        quality_data = [
            [
                "Metric",
                "Result",
            ]
        ]

        for key, value in quality_result.items():

            quality_data.append(
                [
                    str(key)
                    .replace("_", " ")
                    .title(),

                    _safe_paragraph_text(value),
                ]
            )

        quality_table = Table(
            quality_data,
            colWidths=[
                65 * mm,
                100 * mm,
            ],
            repeatRows=1,
        )

        quality_table.setStyle(
            TableStyle(
                [
                    (
                        "BACKGROUND",
                        (0, 0),
                        (-1, 0),
                        colors.HexColor("#D9E2F3"),
                    ),
                    (
                        "FONTNAME",
                        (0, 0),
                        (-1, 0),
                        "Helvetica-Bold",
                    ),
                    (
                        "GRID",
                        (0, 0),
                        (-1, -1),
                        0.4,
                        colors.grey,
                    ),
                    (
                        "VALIGN",
                        (0, 0),
                        (-1, -1),
                        "TOP",
                    ),
                    (
                        "TOPPADDING",
                        (0, 0),
                        (-1, -1),
                        5,
                    ),
                    (
                        "BOTTOMPADDING",
                        (0, 0),
                        (-1, -1),
                        5,
                    ),
                ]
            )
        )

        story.append(
            quality_table
        )

    # =========================================================
    # COMPLIANCE FINDINGS
    # =========================================================

    story.append(
        PageBreak()
    )

    story.append(
        Paragraph(
            "5. Compliance Checks",
            styles["heading"],
        )
    )

    findings = compliance_result.get(
        "findings",
        compliance_result.get(
            "checks",
            [],
        ),
    )

    if findings:

        findings_data = [
            [
                "Rule",
                "Field",
                "Status",
                "Finding",
            ]
        ]

        for item in findings:

            if not isinstance(item, dict):
                continue

            rule_id = _value(
                item.get("rule_id")
            )

            field = _value(
                item.get("field")
            )

            status = _value(
                item.get("status")
            )

            finding = item.get(
                "finding",
                item.get(
                    "message",
                    "",
                ),
            )

            findings_data.append(
                [
                    _safe_paragraph_text(rule_id),
                    _safe_paragraph_text(field),
                    _safe_paragraph_text(status),
                    _safe_paragraph_text(finding),
                ]
            )

        findings_table = Table(
            findings_data,
            colWidths=[
                25 * mm,
                30 * mm,
                25 * mm,
                85 * mm,
            ],
            repeatRows=1,
        )

        findings_table.setStyle(
            TableStyle(
                [
                    (
                        "BACKGROUND",
                        (0, 0),
                        (-1, 0),
                        colors.HexColor("#D9E2F3"),
                    ),
                    (
                        "FONTNAME",
                        (0, 0),
                        (-1, 0),
                        "Helvetica-Bold",
                    ),
                    (
                        "GRID",
                        (0, 0),
                        (-1, -1),
                        0.4,
                        colors.grey,
                    ),
                    (
                        "VALIGN",
                        (0, 0),
                        (-1, -1),
                        "TOP",
                    ),
                    (
                        "FONTSIZE",
                        (0, 0),
                        (-1, -1),
                        7.5,
                    ),
                    (
                        "TOPPADDING",
                        (0, 0),
                        (-1, -1),
                        4,
                    ),
                    (
                        "BOTTOMPADDING",
                        (0, 0),
                        (-1, -1),
                        4,
                    ),
                ]
            )
        )

        story.append(
            findings_table
        )

    else:

        story.append(
            Paragraph(
                "No compliance findings were returned.",
                styles["body"],
            )
        )

    # =========================================================
    # RECOMMENDATIONS
    # =========================================================

    story.append(
        Paragraph(
            "6. Recommendations",
            styles["heading"],
        )
    )

    recommendations = compliance_result.get(
        "recommendations",
        [],
    )

    if recommendations:

        for recommendation in recommendations:

            story.append(
                Paragraph(
                    f"&bull; "
                    f"{_safe_paragraph_text(recommendation)}",
                    styles["body"],
                )
            )

            story.append(
                Spacer(1, 3)
            )

    else:

        story.append(
            Paragraph(
                "No recommendations were generated.",
                styles["body"],
            )
        )

    # =========================================================
    # RAW OCR INFORMATION
    # =========================================================

    raw_text = product_information.get(
        "raw_text"
    )

    if raw_text:

        story.append(
            PageBreak()
        )

        story.append(
            Paragraph(
                "7. OCR Extracted Text",
                styles["heading"],
            )
        )

        escaped_raw_text = html.escape(
            _value(raw_text)
        )

        escaped_raw_text = escaped_raw_text.replace(
            "\n",
            "<br/>",
        )

        story.append(
            Paragraph(
                escaped_raw_text,
                styles["small"],
            )
        )

    # =========================================================
    # DISCLAIMER
    # =========================================================

    story.append(
        Spacer(1, 12)
    )

    disclaimer = compliance_result.get(
        "disclaimer",
        "This automated result evaluates detected label "
        "declarations and configured rules. It is not a "
        "substitute for official legal or regulatory "
        "determination.",
    )

    story.append(
        Paragraph(
            "<b>Disclaimer:</b> "
            + _safe_paragraph_text(disclaimer),
            styles["small"],
        )
    )

    # =========================================================
    # BUILD PDF
    # =========================================================

    doc.build(
        story,
        onFirstPage=_add_page_number,
        onLaterPages=_add_page_number,
    )

    return str(pdf_path)