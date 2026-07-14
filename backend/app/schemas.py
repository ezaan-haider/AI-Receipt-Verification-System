from pydantic import BaseModel
from typing import Optional

from datetime import datetime
from typing import Literal, Optional

from pydantic import BaseModel, Field


class TokenResponse(BaseModel):
    access_token: str
    token_type: str
    user_id: int
    username: str
    full_name: str
    role: str


class CurrentUserResponse(BaseModel):
    id: int
    username: str
    full_name: str
    role: str

    class Config:
        from_attributes = True


class AdminReviewRequest(BaseModel):
    final_status: Literal[
        "APPROVED",
        "REJECTED",
        "NEEDS_MORE_INFORMATION",
    ]

    reviewer_comment: str = Field(
        min_length=3,
        max_length=1000,
    )


class AdminReviewResponse(BaseModel):
    id: int
    verification_status: str
    final_status: str
    reviewer_comment: str
    reviewed_at: datetime
    reviewed_by: str

class ReceiptResponse(BaseModel):
    id: int
    employee_name: str
    claim_amount: float
    image_path: str
    verification_status: str

    class Config:
        from_attributes = True


class ReceiptListResponse(BaseModel):
    id: int
    employee_name: str
    claim_amount: float

    vendor: Optional[str] = None
    receipt_date: Optional[str] = None
    extracted_total: Optional[float] = None

    verification_status: str
    final_status: Optional[str] = None

    image_quality_score: Optional[float] = None
    extraction_confidence: Optional[float] = None
    processing_time_seconds: Optional[float] = None

    class Config:
        from_attributes = True

class ReceiptDetailResponse(BaseModel):
    id: int
    employee_name: str
    claim_amount: float
    image_path: str
    image_hash: Optional[str] = None

    image_quality_score: Optional[float] = None
    image_quality_flags: Optional[str] = None
    image_public_id: Optional[str] = None
    image_url: Optional[str] = None

    receipt_text: Optional[str] = None

    vendor: Optional[str] = None
    receipt_date: Optional[str] = None
    extracted_total: Optional[float] = None
    currency: Optional[str] = None
    receipt_number: Optional[str] = None

    extraction_confidence: Optional[float] = None
    extraction_warnings: Optional[str] = None
    extraction_method: Optional[str] = None
    processing_time_seconds: Optional[float] = None

    verification_status: str
    verification_reason: Optional[str] = None
    reviewer_comment: Optional[str] = None
    reviewed_at: Optional[datetime] = None
    final_status: Optional[str] = None

    class Config:
        from_attributes = True