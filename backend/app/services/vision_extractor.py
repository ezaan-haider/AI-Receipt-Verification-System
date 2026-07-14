import os
from pathlib import Path

from dotenv import load_dotenv
from google import genai
from google.genai import types

from app.extraction_schemas import ReceiptExtraction

load_dotenv()

API_KEY = os.getenv("GEMINI_API_KEY")
MODEL_NAME = os.getenv(
    "GEMINI_MODEL_NAME",
    "gemini-3.1-flash-lite-preview",
)

if not API_KEY:
    raise RuntimeError("GEMINI_API_KEY is missing from .env")

client = genai.Client(api_key=API_KEY)


EXTRACTION_PROMPT = """
Analyse this receipt image and extract structured receipt information.

Return only information supported by the image.

Extraction rules:

1. Full receipt transcription
- Transcribe all readable text visible on the receipt.
- Preserve the approximate reading order from top to bottom.
- Include headings, vendor information, dates, item names, quantities, prices,
  totals, tax information, receipt numbers, and footer text when readable.
- Do not invent missing or unreadable text.
- Store this full transcription in the field "receipt_text".

2. Vendor
- Extract the business, shop, restaurant, supplier, or merchant name.
- Ignore generic form labels such as Date, Page, Receipt, Total, Cashier,
  Thank You, Invoice, and Customer.

3. Receipt date
- Extract the transaction date exactly as displayed.
- Do not infer or invent a date.
- Dates may use day/month/year, month/day/year, dots, hyphens, or slashes.
- Accept formats like:
  - DD-MM-YYYY
  - DD-MM-YY
  - DD.MM.YYYY
  - DD.MM.YY
  - DD/MM/YY
  - DD/MM/YYYY

4. Total
- Extract the final amount payable.
- Prefer labels such as Total, Grand Total, Amount Due, Balance Due,
  Net Payable, or Total Due.
- Do not confuse the total with subtotal, tax, cash tendered, change,
  individual item prices, or item count.
- If the total is handwritten, use the number visually associated with
  the total label.
- Return null when the total cannot be read confidently.

5. Currency
- Extract a visible currency symbol or currency code.
- Examples include PKR, Rs, R, ZAR, USD, GBP, £, $, and €.
- Do not assume a currency merely from the vendor or apparent country.
- Return PKR if no currency is visible.

6. Receipt number
- Extract only a clearly labelled receipt, invoice, slip, transaction,
  order, or till number.
- Do not use phone numbers, tax numbers, dates, times, or item counts.

7. Items
- Extract visible purchased items when reasonably clear.
- Do not invent missing quantities or prices.

8. Confidence and warnings
- extraction_confidence must reflect confidence in the key fields:
  vendor, date, total, currency, and receipt number.
- Add warnings for illegible handwriting, cropped content, ambiguous totals,
  missing dates, missing currency, or uncertain values.
- Do not approve or reject the claim. Only extract information.
"""


def extract_receipt_from_image(
    image_bytes: bytes,
    mime_type: str,
) -> ReceiptExtraction:
    response = client.models.generate_content(
        model=MODEL_NAME,
        contents=[
            types.Part.from_text(
                text=EXTRACTION_PROMPT
            ),
            types.Part.from_bytes(
                data=image_bytes,
                mime_type=mime_type,
            ),
        ],
        config=types.GenerateContentConfig(
            response_mime_type="application/json",
            response_schema=ReceiptExtraction,
            temperature=0,
        ),
    )

    if response.parsed is not None:
        return response.parsed

    if not response.text:
        raise ValueError(
            "Gemini returned no extraction result"
        )

    return ReceiptExtraction.model_validate_json(
        response.text
    )


def _get_mime_type(extension: str) -> str:
    extension = extension.lower()

    mime_types = {
        ".jpg": "image/jpeg",
        ".jpeg": "image/jpeg",
        ".png": "image/png",
        ".webp": "image/webp",
    }

    if extension not in mime_types:
        raise ValueError(f"Unsupported image format: {extension}")

    return mime_types[extension]

def _mime_type_from_url(image_url: str) -> str:
    clean_url = image_url.split("?")[0].lower()

    if clean_url.endswith(".png"):
        return "image/png"

    if clean_url.endswith(".webp"):
        return "image/webp"

    return "image/jpeg"