from datetime import datetime

from sqlalchemy import Column, DateTime, Float, ForeignKey, Integer, String, Text

from app.database.database import Base


class Analysis(Base):
    __tablename__ = "analyses"

    id = Column(
        Integer,
        primary_key=True,
        index=True,
    )

    user_id = Column(
        Integer,
        ForeignKey("users.id"),
        nullable=True,
        index=True,
    )

    filename = Column(
        String(255),
        nullable=False,
    )

    product_name = Column(
        String(500),
        nullable=True,
    )

    mrp = Column(
        String(100),
        nullable=True,
    )

    net_quantity = Column(
        String(100),
        nullable=True,
    )

    manufacturer = Column(
        Text,
        nullable=True,
    )

    marketer = Column(
        Text,
        nullable=True,
    )

    batch_number = Column(
        String(200),
        nullable=True,
    )

    manufacture_date = Column(
        String(100),
        nullable=True,
    )

    use_by_date = Column(
        String(100),
        nullable=True,
    )

    license_number = Column(
        String(200),
        nullable=True,
    )

    overall_status = Column(
        String(100),
        nullable=True,
    )

    risk_level = Column(
        String(100),
        nullable=True,
    )

    compliance_score = Column(
        Float,
        nullable=True,
    )

    report_path = Column(
        Text,
        nullable=True,
    )

    created_at = Column(
        DateTime,
        default=datetime.utcnow,
        nullable=False,
    )