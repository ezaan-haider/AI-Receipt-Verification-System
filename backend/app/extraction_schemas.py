from pydantic import BaseModel, Field


class ReceiptItem(BaseModel):
    description: str | None = None
    quantity: float | None = None
    unit_price: float | None = None
    line_total: float | None = None


class ReceiptExtraction(BaseModel):
    receipt_text: str | None = None

    vendor: str | None = None
    receipt_date: str | None = None
    extracted_total: float | None = None
    currency: str | None = None
    receipt_number: str | None = None

    items: list[ReceiptItem] = Field(default_factory=list)

    extraction_confidence: float = Field(
        default=0.0,
        ge=0.0,
        le=1.0,
    )

    warnings: list[str] = Field(default_factory=list)

