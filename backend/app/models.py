from sqlalchemy import (
    Column,
    Integer,
    String,
    Float,
    DateTime,
    Text,
    Boolean,
    ForeignKey,
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.database import Base

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)

    username = Column(
        String(100),
        unique=True,
        nullable=False,
        index=True,
    )

    full_name = Column(String(150), nullable=False)

    password_hash = Column(String(255), nullable=False)

    role = Column(
        String(20),
        nullable=False,
        default="EMPLOYEE",
    )

    is_active = Column(
        Boolean,
        nullable=False,
        default=True,
    )

    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
    )

class Receipt(Base):
    __tablename__ = "receipts"

    id = Column(Integer, primary_key=True, index=True)

    employee_name = Column(String(100), nullable=False)
    claim_amount = Column(Float, nullable=False)

    image_path = Column(String(255), nullable=False)
    image_hash = Column(String(255), nullable=True, index=True)

    image_quality_score = Column(Float, nullable=True)
    image_quality_flags = Column(Text, nullable=True)

    receipt_text = Column(Text, nullable=True)

    vendor = Column(String(150), nullable=True)
    receipt_date = Column(String(50), nullable=True)
    extracted_total = Column(Float, nullable=True)
    currency = Column(String(20), nullable=True)
    receipt_number = Column(String(100), nullable=True)

    extraction_confidence = Column(Float, nullable=True)
    extraction_warnings = Column(Text, nullable=True)
    extraction_method = Column(
        String(50),
        nullable=False,
        default="GEMINI_VISION",
    )
    processing_time_seconds = Column(Float, nullable=True)
    submitted_by_id = Column(
        Integer,
        ForeignKey("users.id"),
        nullable=True,
        index=True,
    )

    reviewed_by_id = Column(
        Integer,
        ForeignKey("users.id"),
        nullable=True,
    )

    reviewed_at = Column(
        DateTime(timezone=True),
        nullable=True,
    )

    submitted_by = relationship(
        "User",
        foreign_keys=[submitted_by_id],
    )

    reviewed_by = relationship(
        "User",
        foreign_keys=[reviewed_by_id],
    )

    verification_status = Column(String(50), default="PENDING")
    verification_reason = Column(Text, nullable=True)

    reviewer_comment = Column(Text, nullable=True)
    final_status = Column(String(50), nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())