import os
from uuid import uuid4

import cloudinary
import cloudinary.uploader
import requests

cloudinary.config(
    cloud_name=os.getenv("CLOUDINARY_CLOUD_NAME"),
    api_key=os.getenv("CLOUDINARY_API_KEY"),
    api_secret=os.getenv("CLOUDINARY_API_SECRET"),
    secure=True,
)


def upload_receipt(
    file_bytes: bytes,
) -> dict:
    result = cloudinary.uploader.upload(
        file_bytes,
        folder="receipt-verification",
        public_id=str(uuid4()),
        resource_type="image",
        overwrite=False,
    )

    return {
        "url": result["secure_url"],
        "public_id": result["public_id"],
    }


def download_receipt_bytes(image_url: str) -> bytes:
    if not image_url:
        raise ValueError("Receipt image URL is missing")

    response = requests.get(
        image_url,
        timeout=30,
    )
    response.raise_for_status()

    return response.content


def delete_receipt(public_id: str) -> None:
    if not public_id:
        return

    cloudinary.uploader.destroy(
        public_id,
        resource_type="image",
        invalidate=True,
    )