import hashlib

def calculate_bytes_hash(file_bytes: bytes) -> str:
    return hashlib.sha256(file_bytes).hexdigest()


def calculate_file_hash(file_path: str) -> str:
    sha256_hash = hashlib.sha256()

    with open(file_path, "rb") as file:
        for byte_block in iter(lambda: file.read(4096), b""):
            sha256_hash.update(byte_block)

    return sha256_hash.hexdigest()


def find_duplicate_by_hash(db, ReceiptModel, image_hash: str, current_receipt_id: int | None = None):
    query = db.query(ReceiptModel).filter(ReceiptModel.image_hash == image_hash)

    if current_receipt_id is not None:
        query = query.filter(ReceiptModel.id != current_receipt_id)

    return query.first()


def find_possible_duplicate_by_fields(
    db,
    ReceiptModel,
    vendor: str | None,
    receipt_date: str | None,
    extracted_total: float | None,
    current_receipt_id: int | None = None,
):
    if not vendor or not receipt_date or extracted_total is None:
        return None

    query = db.query(ReceiptModel).filter(
        ReceiptModel.vendor == vendor,
        ReceiptModel.receipt_date == receipt_date,
        ReceiptModel.extracted_total == extracted_total,
    )

    if current_receipt_id is not None:
        query = query.filter(ReceiptModel.id != current_receipt_id)

    return query.first()