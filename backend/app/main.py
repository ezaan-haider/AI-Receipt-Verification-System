import os
import time
import requests

from datetime import datetime, timezone

from fastapi.security import OAuth2PasswordRequestForm

from app.auth import (
    create_access_token,
    verify_password,
)
from app.dependencies import (
    get_current_user,
    require_admin,
)
from app.services.storage import delete_receipt

from fastapi import (
    FastAPI,
    UploadFile,
    File,
    Form,
    Depends,
    HTTPException,
)
from sqlalchemy.orm import Session

from app import models, schemas
from app.database import engine, Base, get_db
from app.services.duplicate import (
    calculate_bytes_hash,
    find_duplicate_by_hash,
    find_possible_duplicate_by_fields,
)
from app.services.image_quality import (
    assess_image_quality_bytes,
)

from app.services.storage import (
    delete_receipt,
    download_receipt_bytes,
    upload_receipt,
)
from app.services.verifier import verify_receipt
from app.services.vision_extractor import extract_receipt_from_image
from app.services.storage import upload_receipt


def get_image_mime_type(image_url: str) -> str:
    clean_url = image_url.split("?")[0].lower()

    if clean_url.endswith(".png"):
        return "image/png"

    if clean_url.endswith(".webp"):
        return "image/webp"

    return "image/jpeg"



app = FastAPI(
    title="AI Receipt Verification API",
    version="1.0.0",
)

Base.metadata.create_all(bind=engine)

@app.get("/")
def root():
    return {"message": "Receipt Verification OCR API is running"}


@app.get("/health")
def health_check():
    return {"status": "healthy"}

@app.post(
    "/auth/login",
    response_model=schemas.TokenResponse,
)
def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db),
):
    user = (
        db.query(models.User)
        .filter(models.User.username == form_data.username)
        .first()
    )

    if not user or not verify_password(
        form_data.password,
        user.password_hash,
    ):
        raise HTTPException(
            status_code=401,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not user.is_active:
        raise HTTPException(
            status_code=403,
            detail="Account is disabled",
        )

    access_token = create_access_token(
        user_id=user.id,
        username=user.username,
        role=user.role,
    )

    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user_id": user.id,
        "username": user.username,
        "full_name": user.full_name,
        "role": user.role,
    }

@app.get(
    "/auth/me",
    response_model=schemas.CurrentUserResponse,
)
def get_me(
    current_user: models.User = Depends(get_current_user),
):
    return current_user

@app.post("/receipts", response_model=schemas.ReceiptResponse)
def submit_receipt(
    claim_amount: float = Form(...),
    receipt_image: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    if claim_amount <= 0:
        raise HTTPException(
            status_code=400,
            detail="Claim amount must be greater than 0",
        )

    allowed_extensions = [".jpg", ".jpeg", ".png", ".webp"]

    original_filename = receipt_image.filename or ""
    file_extension = os.path.splitext(original_filename)[1].lower()

    if file_extension not in allowed_extensions:
        raise HTTPException(
            status_code=400,
            detail="Only JPG, JPEG, PNG, and WEBP files are allowed",
        )

    file_bytes = receipt_image.file.read()

    if not file_bytes:
        raise HTTPException(
            status_code=400,
            detail="Uploaded file is empty",
        )

    image_hash = calculate_bytes_hash(file_bytes)

    try:
        upload_result = upload_receipt(
            file_bytes=file_bytes,
            filename=original_filename,
        )
    except Exception as exc:
        raise HTTPException(
            status_code=502,
            detail=f"Cloudinary image upload failed: {exc}",
        ) from exc

    new_receipt = models.Receipt(
        employee_name=current_user.full_name,
        submitted_by_id=current_user.id,
        claim_amount=claim_amount,
        image_path=upload_result["url"],
        image_public_id=upload_result["public_id"],
        image_hash=image_hash,
        verification_status="PENDING",
    )

    try:
        db.add(new_receipt)
        db.commit()
        db.refresh(new_receipt)

    except Exception as exc:
        db.rollback()

        # Prevent orphaned Cloudinary image if database insert fails
        try:
            from app.services.storage import delete_receipt

            delete_receipt(upload_result["public_id"])
        except Exception:
            pass

        raise HTTPException(
            status_code=500,
            detail=f"Receipt could not be saved: {exc}",
        ) from exc

    return new_receipt

@app.get(
    "/my-receipts",
    response_model=list[schemas.ReceiptListResponse],
)
def list_my_receipts(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    return (
        db.query(models.Receipt)
        .filter(
            models.Receipt.submitted_by_id
            == current_user.id
        )
        .order_by(models.Receipt.id.desc())
        .all()
    )

@app.get("/receipts", response_model=list[schemas.ReceiptListResponse])
def list_receipts(
    db: Session = Depends(get_db),
    admin: models.User = Depends(require_admin),
):
    receipts = db.query(models.Receipt).order_by(models.Receipt.id.desc()).all()
    return receipts

@app.get(
    "/receipts/{receipt_id}",
    response_model=schemas.ReceiptDetailResponse,
)
def get_receipt(
    receipt_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    receipt = (
        db.query(models.Receipt)
        .filter(models.Receipt.id == receipt_id)
        .first()
    )

    if not receipt:
        raise HTTPException(
            status_code=404,
            detail="Receipt not found",
        )

    if (
        current_user.role != "ADMIN"
        and receipt.submitted_by_id != current_user.id
    ):
        raise HTTPException(
            status_code=403,
            detail="You cannot view this receipt",
        )

    return receipt


@app.delete("/receipts/{receipt_id}")
def delete_receipt_endpoint(
    receipt_id: int,
    db: Session = Depends(get_db),
    admin: models.User = Depends(require_admin),
):
    receipt = (
        db.query(models.Receipt)
        .filter(models.Receipt.id == receipt_id)
        .first()
    )

    if not receipt:
        raise HTTPException(
            status_code=404,
            detail="Receipt not found",
        )

    try:
        # Delete the cloud image first
        if receipt.image_public_id:
            delete_receipt(receipt.image_public_id)

        # Delete the database record
        db.delete(receipt)
        db.commit()

        return {
            "message": "Receipt deleted successfully",
            "receipt_id": receipt_id,
        }

    except Exception as exc:
        db.rollback()

        raise HTTPException(
            status_code=500,
            detail=f"Receipt deletion failed: {exc}",
        ) from exc

@app.post("/receipts/{receipt_id}/process")
def process_receipt(
    receipt_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    receipt = (
        db.query(models.Receipt)
        .filter(models.Receipt.id == receipt_id)
        .first()
    )

    if not receipt:
        raise HTTPException(
            status_code=404,
            detail="Receipt not found",
        )

    if (
        current_user.role != "ADMIN"
        and receipt.submitted_by_id != current_user.id
    ):
        raise HTTPException(
            status_code=403,
            detail="You cannot process this receipt",
        )

    if not receipt.image_path:
        raise HTTPException(
            status_code=404,
            detail="Receipt image URL is missing",
        )

    process_started = time.perf_counter()

    try:
        # 1. Download image bytes from Cloudinary
        image_bytes = download_receipt_bytes(
            receipt.image_path
        )

        if not image_bytes:
            raise ValueError(
                "Downloaded receipt image is empty"
            )

        # 2. Assess image quality using downloaded bytes
        quality_result = assess_image_quality_bytes(
            image_bytes
        )

        receipt.image_quality_score = (
            quality_result["score"]
        )

        receipt.image_quality_flags = (
            ", ".join(quality_result["flags"])
            if quality_result["flags"]
            else None
        )

        # 3. Send the image bytes directly to Gemini Vision
        mime_type = get_image_mime_type(
            receipt.image_path
        )

        vision_result = extract_receipt_from_image(
            image_bytes=image_bytes,
            mime_type=mime_type,
        )

        receipt.receipt_text = (
            vision_result.receipt_text
        )
        receipt.vendor = vision_result.vendor
        receipt.receipt_date = (
            vision_result.receipt_date
        )
        receipt.extracted_total = (
            vision_result.extracted_total
        )
        receipt.currency = vision_result.currency
        receipt.receipt_number = (
            vision_result.receipt_number
        )

        receipt.extraction_confidence = (
            vision_result.extraction_confidence
        )

        receipt.extraction_warnings = (
            ", ".join(vision_result.warnings)
            if vision_result.warnings
            else None
        )

        receipt.extraction_method = "GEMINI_VISION"

        # 4. Duplicate detection
        exact_duplicate = find_duplicate_by_hash(
            db=db,
            ReceiptModel=models.Receipt,
            image_hash=receipt.image_hash,
            current_receipt_id=receipt.id,
        )

        possible_duplicate = (
            find_possible_duplicate_by_fields(
                db=db,
                ReceiptModel=models.Receipt,
                vendor=receipt.vendor,
                receipt_date=receipt.receipt_date,
                extracted_total=receipt.extracted_total,
                current_receipt_id=receipt.id,
            )
        )

        # 5. Deterministic verification
        verification = verify_receipt(
            claim_amount=receipt.claim_amount,
            extracted_total=receipt.extracted_total,
            receipt_date=receipt.receipt_date,
            extraction_confidence=(
                receipt.extraction_confidence
            ),
            image_quality_score=(
                receipt.image_quality_score
            ),
            image_quality_flags=(
                receipt.image_quality_flags
            ),
        )

        if exact_duplicate:
            receipt.verification_status = "REJECTED"
            receipt.verification_reason = (
                "Exact duplicate image detected. "
                f"Matches receipt ID "
                f"{exact_duplicate.id}."
            )

        elif possible_duplicate:
            receipt.verification_status = (
                "NEEDS_REVIEW"
            )
            receipt.verification_reason = (
                "Possible duplicate receipt detected. "
                f"Similar to receipt ID "
                f"{possible_duplicate.id}."
            )

        else:
            receipt.verification_status = (
                verification["status"]
            )
            receipt.verification_reason = (
                verification["reason"]
            )

        receipt.processing_time_seconds = round(
            time.perf_counter() - process_started,
            3,
        )

        db.commit()
        db.refresh(receipt)

        return {
            "id": receipt.id,
            "vendor": receipt.vendor,
            "receipt_date": receipt.receipt_date,
            "extracted_total": (
                receipt.extracted_total
            ),
            "currency": receipt.currency,
            "receipt_number": (
                receipt.receipt_number
            ),
            "extraction_confidence": (
                receipt.extraction_confidence
            ),
            "extraction_warnings": (
                receipt.extraction_warnings
            ),
            "extraction_method": (
                receipt.extraction_method
            ),
            "image_quality_score": (
                receipt.image_quality_score
            ),
            "image_quality_flags": (
                receipt.image_quality_flags
            ),
            "verification_status": (
                receipt.verification_status
            ),
            "verification_reason": (
                receipt.verification_reason
            ),
            "processing_time_seconds": (
                receipt.processing_time_seconds
            ),
        }

    except requests.RequestException as exc:
        db.rollback()

        raise HTTPException(
            status_code=502,
            detail=(
                "Could not download the receipt "
                f"from Cloudinary: {exc}"
            ),
        ) from exc

    except Exception as exc:
        db.rollback()

        raise HTTPException(
            status_code=500,
            detail=f"Receipt processing failed: {exc}",
        ) from exc

@app.patch(
    "/receipts/{receipt_id}/review",
    response_model=schemas.AdminReviewResponse,
)
def review_receipt(
    receipt_id: int,
    review: schemas.AdminReviewRequest,
    db: Session = Depends(get_db),
    admin: models.User = Depends(require_admin),
):
    receipt = (
        db.query(models.Receipt)
        .filter(models.Receipt.id == receipt_id)
        .first()
    )

    if not receipt:
        raise HTTPException(
            status_code=404,
            detail="Receipt not found",
        )

    if receipt.verification_status == "PENDING":
        raise HTTPException(
            status_code=409,
            detail="Receipt must be processed before review",
        )

    receipt.final_status = review.final_status
    receipt.reviewer_comment = (
        review.reviewer_comment.strip()
    )
    receipt.reviewed_by_id = admin.id
    receipt.reviewed_at = datetime.now(timezone.utc)

    db.commit()
    db.refresh(receipt)

    return {
        "id": receipt.id,
        "verification_status": receipt.verification_status,
        "final_status": receipt.final_status,
        "reviewer_comment": receipt.reviewer_comment,
        "reviewed_at": receipt.reviewed_at,
        "reviewed_by": admin.full_name,
    }