from typing import Any

import requests

API_BASE_URL = "http://127.0.0.1:8000"
REQUEST_TIMEOUT = 30


class APIError(Exception):
    pass


def _headers(token: str | None = None) -> dict[str, str]:
    if not token:
        return {}

    return {
        "Authorization": f"Bearer {token}",
    }


def _handle_response(response: requests.Response) -> Any:
    try:
        payload = response.json()
    except ValueError:
        payload = None

    if response.ok:
        return payload

    if isinstance(payload, dict):
        detail = payload.get("detail", "Request failed")
    else:
        detail = response.text or "Request failed"

    raise APIError(str(detail))


def login(username: str, password: str) -> dict:
    response = requests.post(
        f"{API_BASE_URL}/auth/login",
        data={
            "username": username,
            "password": password,
        },
        timeout=REQUEST_TIMEOUT,
    )

    return _handle_response(response)


def submit_receipt(
    token: str,
    claim_amount: float,
    uploaded_file,
) -> dict:
    response = requests.post(
        f"{API_BASE_URL}/receipts",
        headers=_headers(token),
        data={
            "claim_amount": claim_amount,
        },
        files={
            "receipt_image": (
                uploaded_file.name,
                uploaded_file.getvalue(),
                uploaded_file.type,
            )
        },
        timeout=REQUEST_TIMEOUT,
    )

    return _handle_response(response)


def process_receipt(
    token: str,
    receipt_id: int,
) -> dict:
    response = requests.post(
        f"{API_BASE_URL}/receipts/{receipt_id}/process",
        headers=_headers(token),
        timeout=60,
    )

    return _handle_response(response)


def get_my_receipts(token: str) -> list[dict]:
    response = requests.get(
        f"{API_BASE_URL}/my-receipts",
        headers=_headers(token),
        timeout=REQUEST_TIMEOUT,
    )

    return _handle_response(response)


def get_all_receipts(token: str) -> list[dict]:
    response = requests.get(
        f"{API_BASE_URL}/receipts",
        headers=_headers(token),
        timeout=REQUEST_TIMEOUT,
    )

    return _handle_response(response)


def get_receipt(
    token: str,
    receipt_id: int,
) -> dict:
    response = requests.get(
        f"{API_BASE_URL}/receipts/{receipt_id}",
        headers=_headers(token),
        timeout=REQUEST_TIMEOUT,
    )

    return _handle_response(response)


def review_receipt(
    token: str,
    receipt_id: int,
    final_status: str,
    reviewer_comment: str,
) -> dict:
    response = requests.patch(
        f"{API_BASE_URL}/receipts/{receipt_id}/review",
        headers=_headers(token),
        json={
            "final_status": final_status,
            "reviewer_comment": reviewer_comment,
        },
        timeout=REQUEST_TIMEOUT,
    )

    return _handle_response(response)