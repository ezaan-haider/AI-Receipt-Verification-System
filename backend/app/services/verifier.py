from datetime import datetime


def verify_receipt(
    claim_amount: float,
    extracted_total: float | None,
    receipt_date: str | None,
    extraction_confidence: float | None,
    image_quality_score: float | None = None,
    image_quality_flags: str | None = None,
):
    reasons = []

    if image_quality_score is not None and image_quality_score < 60:
        reasons.append(f"Poor image quality: {image_quality_flags}.")

    if extraction_confidence is None or extraction_confidence < 0.70:
        reasons.append("Low extraction confidence.")

    if extracted_total is None:
        reasons.append("Could not extract total amount.")
    else:
        if abs(claim_amount - extracted_total) > 0.01:
            reasons.append(
                f"Claim amount {claim_amount} does not match receipt total {extracted_total}."
            )

    if receipt_date:
        parsed_date = parse_date(receipt_date)

        if parsed_date:
            if parsed_date > datetime.now():
                reasons.append("Receipt date is in the future.")
        else:
            reasons.append("Could not validate receipt date format.")
    else:
        reasons.append("Receipt date missing.")

    if reasons:
        return {
            "status": "NEEDS_REVIEW",
            "reason": " ".join(reasons),
        }

    return {
        "status": "APPROVED",
        "reason": "Claim amount matches receipt total and required fields were extracted.",
    }


from datetime import datetime


def parse_date(date_text: str):
    formats = [
        "%d-%m-%Y",
        "%d-%m-%y",
        "%d.%m.%Y",
        "%d.%m.%y",
        "%d/%m/%Y",
        "%d/%m/%y",
        "%Y-%m-%d",

        "%d-%b-%Y",
        "%d-%b-%y",
        "%d %b %Y",
        "%d %b %y",

        "%d-%B-%Y",
        "%d-%B-%y",
        "%d %B %Y",
        "%d %B %y",
    ]

    cleaned_date = date_text.strip()

    for fmt in formats:
        try:
            return datetime.strptime(cleaned_date, fmt)
        except ValueError:
            continue

    return None