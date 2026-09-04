from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database.database import get_db
from app.dependencies.auth import get_current_user
from app.models.analysis import Analysis
from app.models.user import User


router = APIRouter(
    prefix="/api/history",
    tags=["History"],
)


# ============================================================
# GET ALL ANALYSIS HISTORY FOR CURRENT USER
# ============================================================

@router.get("/")
def get_history(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Return previous SmartLabel AI analyses
    belonging only to the currently authenticated user.
    """

    analyses = (
        db.query(Analysis)
        .filter(
            Analysis.user_id == current_user.id
        )
        .order_by(Analysis.created_at.desc())
        .all()
    )

    return {
        "count": len(analyses),
        "history": [
            {
                "id": analysis.id,
                "filename": analysis.filename,
                "product_name": analysis.product_name,
                "mrp": analysis.mrp,
                "net_quantity": analysis.net_quantity,
                "manufacturer": analysis.manufacturer,
                "marketer": analysis.marketer,
                "batch_number": analysis.batch_number,
                "manufacture_date": analysis.manufacture_date,
                "use_by_date": analysis.use_by_date,
                "license_number": analysis.license_number,
                "overall_status": analysis.overall_status,
                "risk_level": analysis.risk_level,
                "compliance_score": analysis.compliance_score,
                "report_path": analysis.report_path,
                "created_at": analysis.created_at,
            }
            for analysis in analyses
        ],
    }


# ============================================================
# GET SINGLE ANALYSIS FOR CURRENT USER
# ============================================================

@router.get("/{analysis_id}")
def get_analysis(
    analysis_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Return one analysis only if it belongs
    to the currently authenticated user.
    """

    analysis = (
        db.query(Analysis)
        .filter(
            Analysis.id == analysis_id,
            Analysis.user_id == current_user.id,
        )
        .first()
    )

    if not analysis:
        raise HTTPException(
            status_code=404,
            detail=f"Analysis {analysis_id} not found.",
        )

    return {
        "id": analysis.id,
        "filename": analysis.filename,
        "product_name": analysis.product_name,
        "mrp": analysis.mrp,
        "net_quantity": analysis.net_quantity,
        "manufacturer": analysis.manufacturer,
        "marketer": analysis.marketer,
        "batch_number": analysis.batch_number,
        "manufacture_date": analysis.manufacture_date,
        "use_by_date": analysis.use_by_date,
        "license_number": analysis.license_number,
        "overall_status": analysis.overall_status,
        "risk_level": analysis.risk_level,
        "compliance_score": analysis.compliance_score,
        "report_path": analysis.report_path,
        "created_at": analysis.created_at,
    }