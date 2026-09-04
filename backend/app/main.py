import os

from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.sessions import SessionMiddleware

from app.database.database import Base, engine

from app.models.analysis import Analysis
from app.models.user import User
from app.models.password_reset import PasswordResetToken

from app.api.auth import router as auth_router
from app.api.uploads import router as upload_router
from app.api.image_analysis import router as image_analysis_router
from app.api.ocr import router as ocr_router
from app.api.reports import router as reports_router
from app.api.history import router as history_router


# --------------------------------------------------
# ENVIRONMENT
# --------------------------------------------------

load_dotenv()


# --------------------------------------------------
# DATABASE
# --------------------------------------------------

Base.metadata.create_all(bind=engine)


# --------------------------------------------------
# APPLICATION
# --------------------------------------------------

app = FastAPI(
    title="SmartLabel AI",
    description="AI-powered Legal Metrology compliance system",
    version="0.1.0",
)


# --------------------------------------------------
# SESSION
# --------------------------------------------------

app.add_middleware(
    SessionMiddleware,
    secret_key=os.getenv(
        "SESSION_SECRET",
        "dev-session-secret-change-me",
    ),
    same_site="lax",
    https_only=False,
)


# --------------------------------------------------
# CORS
# --------------------------------------------------

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# --------------------------------------------------
# ROUTES
# --------------------------------------------------

app.include_router(auth_router)

app.include_router(upload_router)
app.include_router(image_analysis_router)
app.include_router(ocr_router)
app.include_router(reports_router)
app.include_router(history_router)


# --------------------------------------------------
# HEALTH
# --------------------------------------------------

@app.get("/api/health")
def health_check():
    return {
        "status": "ok",
        "service": "SmartLabel AI",
    }