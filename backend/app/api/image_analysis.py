from pathlib import Path
import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database.database import get_db
from app.dependencies.auth import get_current_user
from app.models.analysis import Analysis
from app.models.user import User

from app.services.visual.quality import analyze_image_quality
from app.services.visual.enhancement import enhance_image
from app.services.ocr import extract_text
from app.services.information_extraction import extract_product_information
from app.services.compliance_engine import run_compliance_checks
from app.services.reporting.pdf_report import generate_pdf_report


router = APIRouter(
    prefix="/api",
    tags=["Image Analysis"],
)


UPLOAD_DIR = Path("uploads")
ENHANCED_DIR = UPLOAD_DIR / "enhanced"

UPLOAD_DIR.mkdir(
    parents=True,
    exist_ok=True,
)

ENHANCED_DIR.mkdir(
    parents=True,
    exist_ok=True,
)


@router.post("/analyze-image/{filename}")
def analyze_image(
    filename: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    image_path = UPLOAD_DIR / filename

    if not image_path.exists():
        raise HTTPException(
            status_code=404,
            detail="Image not found.",
        )

    try:
        # --------------------------------------------------
        # 1. IMAGE QUALITY
        # --------------------------------------------------

        quality = analyze_image_quality(
            str(image_path)
        )

        # --------------------------------------------------
        # 2. IMAGE ENHANCEMENT
        # --------------------------------------------------

        enhanced_image_path = None

        if quality.get(
            "enhancement_required",
            False,
        ):
            enhanced_filename = (
                f"{uuid.uuid4()}_enhanced.jpg"
            )

            enhanced_path = (
                ENHANCED_DIR / enhanced_filename
            )

            enhanced_image_path = enhance_image(
                str(image_path),
                str(enhanced_path),
            )

        # --------------------------------------------------
        # 3. OCR
        # --------------------------------------------------

        ocr_image = (
            enhanced_image_path
            or str(image_path)
        )

        ocr_result = extract_text(
            ocr_image
        )

        # --------------------------------------------------
        # 4. INFORMATION EXTRACTION
        # --------------------------------------------------

        product_information = (
            extract_product_information(
                ocr_result
            )
        )

        # --------------------------------------------------
        # 5. COMPLIANCE ENGINE
        # --------------------------------------------------

        compliance_result = (
            run_compliance_checks(
                product_information
            )
        )

        # --------------------------------------------------
        # 6. PDF REPORT
        # --------------------------------------------------

        pdf_path = generate_pdf_report(
            filename=filename,
            product_information=product_information,
            compliance_result=compliance_result,
            quality_result=quality,
            image_path=str(image_path),
        )

        # --------------------------------------------------
        # 7. DATABASE PERSISTENCE
        # --------------------------------------------------

        analysis = Analysis(
            # Associate this analysis with
            # the currently authenticated user
            user_id=current_user.id,

            filename=filename,

            product_name=product_information.get(
                "product_name"
            ),

            mrp=product_information.get(
                "mrp"
            ),

            net_quantity=product_information.get(
                "net_quantity"
            ),

            manufacturer=product_information.get(
                "manufacturer"
            ),

            marketer=product_information.get(
                "marketer"
            ),

            batch_number=product_information.get(
                "batch_number"
            ),

            manufacture_date=product_information.get(
                "manufacture_date"
            ),

            use_by_date=product_information.get(
                "use_by_date"
            ),

            license_number=product_information.get(
                "license_number"
            ),

            overall_status=compliance_result.get(
                "overall_status"
            ),

            risk_level=compliance_result.get(
                "risk_level"
            ),

            compliance_score=(
                compliance_result.get(
                    "compliance_score",
                    compliance_result.get(
                        "score"
                    ),
                )
            ),

            report_path=pdf_path,
        )

        db.add(analysis)
        db.commit()
        db.refresh(analysis)

        # --------------------------------------------------
        # 8. RESPONSE
        # --------------------------------------------------

        return {
            "success": True,

            "analysis_id": analysis.id,

            "user_id": current_user.id,

            "filename": filename,

            "quality": quality,

            "ocr": ocr_result,

            "product_information": (
                product_information
            ),

            "compliance": (
                compliance_result
            ),

            "report_path": pdf_path,

            "created_at": (
                analysis.created_at
            ),
        }

    except (ValueError, FileNotFoundError) as exc:

        db.rollback()

        raise HTTPException(
            status_code=400,
            detail=str(exc),
        )

    except Exception as exc:

        db.rollback()

        raise HTTPException(
            status_code=500,
            detail=(
                f"Image analysis failed: {str(exc)}"
            ),
        )