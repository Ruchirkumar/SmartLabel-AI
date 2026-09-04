"""
SmartLabel AI - AI Analysis Layer

This module interprets the deterministic compliance-engine results.
It does NOT replace the compliance engine.

The compliance engine decides PASS / FAIL / REVIEW.
This layer converts those results into:
- risk level
- confidence
- findings
- recommendations
- human-readable explanation
"""


def _safe_text(value):
    """Convert a value to clean text."""
    if value is None:
        return ""

    if isinstance(value, list):
        return ", ".join(str(item) for item in value)

    return str(value).strip()


def _calculate_risk(compliance_result):
    """
    Calculate risk from deterministic compliance results.

    Rules:
    - Any FAIL -> HIGH
    - Any REVIEW -> MEDIUM
    - Otherwise -> LOW
    """
    checks = compliance_result.get("checks", [])

    failed = sum(
        1 for check in checks
        if str(check.get("status", "")).upper() == "FAIL"
    )

    review = sum(
        1 for check in checks
        if str(check.get("status", "")).upper() in {"REVIEW", "WARNING"}
    )

    if failed > 0:
        return "HIGH"

    if review > 0:
        return "MEDIUM"

    return "LOW"


def _calculate_confidence(compliance_result, product_information):
    """
    Estimate confidence in the automated analysis.

    This is NOT a legal probability.
    It represents confidence in the available extracted data
    and deterministic rule results.
    """
    checks = compliance_result.get("checks", [])

    if not checks:
        return 0.0

    passed = sum(
        1 for check in checks
        if str(check.get("status", "")).upper() == "PASS"
    )

    failed = sum(
        1 for check in checks
        if str(check.get("status", "")).upper() == "FAIL"
    )

    review = sum(
        1 for check in checks
        if str(check.get("status", "")).upper() in {"REVIEW", "WARNING"}
    )

    total = len(checks)

    # Base confidence from rule results.
    confidence = passed / total

    # Missing core product information reduces confidence.
    important_fields = [
        "product_name",
        "mrp",
        "net_quantity",
        "manufacturer",
        "batch_number",
        "manufacture_date",
        "use_by_date",
    ]

    missing_fields = 0

    for field in important_fields:
        if not _safe_text(product_information.get(field)):
            missing_fields += 1

    missing_penalty = min(missing_fields * 0.03, 0.20)

    confidence -= missing_penalty

    # REVIEW results indicate uncertainty.
    confidence -= min(review * 0.05, 0.20)

    # FAIL results indicate stronger uncertainty.
    confidence -= min(failed * 0.10, 0.30)

    confidence = max(0.0, min(1.0, confidence))

    return round(confidence, 2)


def _build_findings(compliance_result):
    """Convert compliance checks into concise AI findings."""
    findings = []

    checks = compliance_result.get("checks", [])

    for check in checks:
        status = str(check.get("status", "")).upper()

        if status == "FAIL":
            severity = "HIGH"

        elif status in {"REVIEW", "WARNING"}:
            severity = "MEDIUM"

        else:
            severity = "LOW"

        findings.append(
            {
                "rule_id": check.get("rule_id"),
                "field": check.get("field"),
                "severity": severity,
                "status": status,
                "finding": check.get("message", ""),
                "value": check.get("value"),
            }
        )

    return findings


def _build_recommendations(compliance_result, product_information):
    """Generate practical recommendations from the results."""
    recommendations = []

    checks = compliance_result.get("checks", [])

    failed_checks = [
        check for check in checks
        if str(check.get("status", "")).upper() == "FAIL"
    ]

    review_checks = [
        check for check in checks
        if str(check.get("status", "")).upper() in {"REVIEW", "WARNING"}
    ]

    if failed_checks:
        for check in failed_checks:
            rule_name = check.get("rule_name", "this requirement")

            recommendations.append(
                f"Review and correct the {rule_name.lower()} declaration."
            )

    if review_checks:
        for check in review_checks:
            rule_name = check.get("rule_name", "this requirement")

            recommendations.append(
                f"Manually verify the {rule_name.lower()} because "
                f"the automated result requires review."
            )

    # Specific data-quality checks.
    manufacturer = _safe_text(product_information.get("manufacturer"))

    if manufacturer:
        # OCR can sometimes capture surrounding nutrition-table text.
        suspicious_terms = [
            "total fat",
            "saturated fat",
            "trans fat",
            "cholesterol",
            "sodium",
            "energy (kcal)",
            "protein (g)",
        ]

        manufacturer_lower = manufacturer.lower()

        if any(term in manufacturer_lower for term in suspicious_terms):
            recommendations.append(
                "Verify the manufacturer/packer text manually because "
                "OCR appears to have captured nearby nutrition-table text."
            )

    marketer = _safe_text(product_information.get("marketer"))

    if marketer:
        marketer_lower = marketer.lower()

        suspicious_marketer_terms = [
            "per per",
            "sene",
            "bboh",
            "srda",
            "er 2",
        ]

        if any(term in marketer_lower for term in suspicious_marketer_terms):
            recommendations.append(
                "Verify the marketer declaration manually because "
                "the extracted OCR text appears noisy."
            )

    if not recommendations:
        recommendations.append(
            "No immediate issues were identified by the configured "
            "automated compliance checks."
        )

    return recommendations


def _build_summary(compliance_result, risk_level):
    """Create a human-readable overall explanation."""
    summary = compliance_result.get("summary", {})

    total = summary.get("total_checks", 0)
    passed = summary.get("passed", 0)
    failed = summary.get("failed", 0)
    review = summary.get("review_required", 0)

    if risk_level == "HIGH":
        return (
            f"{failed} of {total} configured compliance checks failed. "
            f"The label requires corrective action before it should be "
            f"considered compliant."
        )

    if risk_level == "MEDIUM":
        return (
            f"{passed} of {total} configured checks passed, while "
            f"{review} require manual review. The automated result should "
            f"not be treated as final compliance until those items are verified."
        )

    return (
        f"All {total} configured compliance checks passed. "
        f"The detected declarations appear complete under the currently "
        f"configured rules."
    )


def analyze_compliance(compliance_result, product_information=None):
    """
    Main AI-analysis function.

    Parameters
    ----------
    compliance_result:
        Output generated by run_compliance_checks()

    product_information:
        Output generated by information extraction.

    Returns
    -------
    dict
        Structured AI analysis result.
    """
    if product_information is None:
        product_information = {}

    risk_level = _calculate_risk(compliance_result)

    confidence = _calculate_confidence(
        compliance_result,
        product_information,
    )

    findings = _build_findings(compliance_result)

    recommendations = _build_recommendations(
        compliance_result,
        product_information,
    )

    summary = _build_summary(
        compliance_result,
        risk_level,
    )

    overall_status = compliance_result.get(
        "overall_status",
        "REVIEW",
    )

    # Don't allow a perfect-looking AI result when OCR quality
    # clearly suggests manual verification.
    if recommendations and risk_level == "LOW":
        noisy_extraction = any(
            phrase in recommendation.lower()
            for recommendation in recommendations
            for phrase in [
                "ocr appears",
                "extracted ocr text appears",
            ]
        )

        if noisy_extraction:
            risk_level = "MEDIUM"

    return {
        "overall_status": overall_status,
        "risk_level": risk_level,
        "confidence": confidence,
        "summary": summary,
        "findings": findings,
        "recommendations": recommendations,
        "analysis_type": "rule_based_ai_assisted",
        "disclaimer": (
            "This analysis is based on extracted label information and "
            "configured automated rules. It is intended for screening and "
            "review assistance and is not a substitute for official legal "
            "or regulatory determination."
        ),
    }


# Backward-compatible alias.
# This makes it easy to call the service using either name.
def run_ai_analysis(compliance_result, product_information=None):
    return analyze_compliance(
        compliance_result,
        product_information,
    )