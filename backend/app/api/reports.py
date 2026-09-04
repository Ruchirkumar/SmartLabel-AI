from pathlib import Path

from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse


router = APIRouter(
    prefix="/api/reports",
    tags=["Reports"],
)


REPORTS_DIR = Path("reports")
REPORTS_DIR.mkdir(parents=True, exist_ok=True)


@router.get("/{filename}")
def download_report(filename: str):
    report_path = REPORTS_DIR / filename

    if not report_path.exists():
        raise HTTPException(
            status_code=404,
            detail="Report not found.",
        )

    if report_path.suffix.lower() != ".pdf":
        raise HTTPException(
            status_code=400,
            detail="Only PDF reports can be downloaded.",
        )

    return FileResponse(
        path=report_path,
        media_type="application/pdf",
        filename=report_path.name,
    )