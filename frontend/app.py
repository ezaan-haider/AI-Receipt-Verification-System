import pandas as pd
import streamlit as st

from api_client import (
    API_BASE_URL,
    APIError,
    delete_receipt,
    get_all_receipts,
    get_my_receipts,
    get_receipt,
    login,
    process_receipt,
    review_receipt,
    submit_receipt,
)

st.set_page_config(
    page_title="AI Receipt Verification",
    page_icon="🧾",
    layout="wide",
)


def initialize_session():
    defaults = {
        "authenticated": False,
        "token": None,
        "user_id": None,
        "username": None,
        "full_name": None,
        "role": None,
    }

    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


def logout():
    for key in [
        "authenticated",
        "token",
        "user_id",
        "username",
        "full_name",
        "role",
    ]:
        st.session_state[key] = None

    st.session_state.authenticated = False
    st.rerun()


def status_label(receipt: dict) -> str:
    final_status = receipt.get("final_status")

    if final_status:
        return f"Final: {final_status}"

    return f"System: {receipt.get('verification_status', 'PENDING')}"


def render_login():
    st.title("AI Receipt Verification System")
    st.caption(
        "Secure receipt submission and administrative review"
    )

    left, centre, right = st.columns([1, 1.2, 1])

    with centre:
        with st.form("login_form"):
            st.subheader("Sign in")

            username = st.text_input("Username")
            password = st.text_input(
                "Password",
                type="password",
            )

            submitted = st.form_submit_button(
                "Sign in",
                use_container_width=True,
            )

        if submitted:
            if not username.strip() or not password:
                st.error("Enter your username and password.")
                return

            try:
                result = login(
                    username=username.strip(),
                    password=password,
                )

                st.session_state.authenticated = True
                st.session_state.token = result["access_token"]
                st.session_state.user_id = result["user_id"]
                st.session_state.username = result["username"]
                st.session_state.full_name = result["full_name"]
                st.session_state.role = result["role"]

                st.rerun()

            except APIError as exc:
                st.error(str(exc))

            except Exception:
                st.error(
                    "Could not connect to the backend."
                )


def render_sidebar():
    st.sidebar.title("Receipt Verification")

    st.sidebar.write(
        f"**{st.session_state.full_name}**"
    )
    st.sidebar.caption(
        st.session_state.role.title()
    )

    if st.sidebar.button(
        "Sign out",
        use_container_width=True,
    ):
        logout()


def render_upload_page():
    st.title("Submit Receipt")
    st.write(
        "Upload a receipt and enter the amount being claimed."
    )

    with st.form(
        "receipt_upload_form",
        clear_on_submit=True,
    ):
        claim_amount = st.number_input(
            "Claim amount",
            min_value=0.01,
            step=0.01,
            format="%.2f",
        )

        receipt_image = st.file_uploader(
            "Receipt image",
            type=["jpg", "jpeg", "png", "webp"],
        )

        submitted = st.form_submit_button(
            "Submit and verify",
            use_container_width=True,
        )

    if submitted:
        if receipt_image is None:
            st.error("Upload a receipt image.")
            return

        try:
            with st.status(
                "Processing receipt...",
                expanded=True,
            ) as status:
                st.write("Uploading image...")

                created = submit_receipt(
                    token=st.session_state.token,
                    claim_amount=claim_amount,
                    uploaded_file=receipt_image,
                )

                receipt_id = created["id"]

                st.write("Analysing receipt...")

                result = process_receipt(
                    token=st.session_state.token,
                    receipt_id=receipt_id,
                )

                status.update(
                    label="Receipt processed",
                    state="complete",
                )

            st.success(
                f"Receipt #{receipt_id} was submitted."
            )

            col1, col2, col3 = st.columns(3)

            col1.metric(
                "Claim amount",
                f"{claim_amount:,.2f}",
            )

            extracted_total = result.get(
                "extracted_total"
            )

            col2.metric(
                "Extracted total",
                (
                    f"{extracted_total:,.2f}"
                    if extracted_total is not None
                    else "Not found"
                ),
            )

            col3.metric(
                "Processing time",
                (
                    f"{result.get('processing_time_seconds', 0):.2f}s"
                ),
            )

            st.subheader("Verification result")

            st.write(
                f"**Status:** "
                f"{result['verification_status']}"
            )

            st.write(
                f"**Reason:** "
                f"{result['verification_reason']}"
            )

            if result.get("extraction_warnings"):
                st.warning(
                    result["extraction_warnings"]
                )

        except APIError as exc:
            st.error(str(exc))

        except Exception:
            st.error(
                "The receipt could not be processed."
            )


def render_employee_history():
    st.title("My Receipts")

    try:
        receipts = get_my_receipts(
            st.session_state.token
        )
    except APIError as exc:
        st.error(str(exc))
        return

    if not receipts:
        st.info("You have not submitted any receipts.")
        return

    rows = []

    for receipt in receipts:
        rows.append(
            {
                "ID": receipt["id"],
                "Vendor": receipt.get("vendor"),
                "Claim": receipt["claim_amount"],
                "Extracted total": receipt.get(
                    "extracted_total"
                ),
                "Date": receipt.get("receipt_date"),
                "Status": status_label(receipt),
            }
        )

    st.dataframe(
        pd.DataFrame(rows),
        use_container_width=True,
        hide_index=True,
    )

    receipt_ids = [
        receipt["id"]
        for receipt in receipts
    ]

    selected_id = st.selectbox(
        "View receipt details",
        receipt_ids,
    )

    render_receipt_detail(selected_id, admin=False)


def render_receipt_detail(
    receipt_id: int,
    admin: bool,
):
    try:
        receipt = get_receipt(
            st.session_state.token,
            receipt_id,
        )
    except APIError as exc:
        st.error(str(exc))
        return

    st.divider()

    left, right = st.columns([1, 1.4])

    with left:
        st.subheader("Receipt image")

        image_path = receipt["image_path"].replace(
            "\\",
            "/",
        )

        st.image(
            f"{API_BASE_URL}/{image_path}",
            use_container_width=True,
        )

    with right:
        st.subheader("Extracted information")

        details = {
            "Employee": receipt["employee_name"],
            "Vendor": receipt.get("vendor"),
            "Receipt date": receipt.get(
                "receipt_date"
            ),
            "Claim amount": receipt.get(
                "claim_amount"
            ),
            "Extracted total": receipt.get(
                "extracted_total"
            ),
            "Currency": receipt.get("currency"),
            "Receipt number": receipt.get(
                "receipt_number"
            ),
            "Extraction confidence": receipt.get(
                "extraction_confidence"
            ),
            "System status": receipt.get(
                "verification_status"
            ),
            "System reason": receipt.get(
                "verification_reason"
            ),
            "Final status": receipt.get(
                "final_status"
            ),
            "Reviewer comment": receipt.get(
                "reviewer_comment"
            ),
        }

        for label, value in details.items():
            st.write(f"**{label}:** {value or '—'}")

    st.subheader("Receipt transcription")

    st.text_area(
        "Full text identified from the receipt",
        value=receipt.get("receipt_text") or "",
        height=300,
        disabled=True,
        label_visibility="collapsed",
    )

    if receipt.get("extraction_warnings"):
        st.warning(receipt["extraction_warnings"])

    if receipt.get("image_quality_flags"):
        st.warning(
            "Image quality: "
            + receipt["image_quality_flags"]
        )

    if admin:
        render_admin_review(receipt)
        render_delete_receipt(receipt)


def render_admin_review(receipt: dict):
    st.subheader("Administrative decision")

    current_final_status = receipt.get(
        "final_status"
    )

    if current_final_status:
        st.info(
            f"Current final status: "
            f"{current_final_status}"
        )

    with st.form(
        f"review_form_{receipt['id']}"
    ):
        decision = st.selectbox(
            "Decision",
            [
                "APPROVED",
                "REJECTED",
                "NEEDS_MORE_INFORMATION",
            ],
        )

        comment = st.text_area(
            "Reviewer comment",
            value=receipt.get(
                "reviewer_comment"
            )
            or "",
            placeholder=(
                "Explain the reason for the final decision."
            ),
        )

        submitted = st.form_submit_button(
            "Save decision",
            use_container_width=True,
        )

    if submitted:
        if len(comment.strip()) < 3:
            st.error(
                "Add a meaningful reviewer comment."
            )
            return

        try:
            result = review_receipt(
                token=st.session_state.token,
                receipt_id=receipt["id"],
                final_status=decision,
                reviewer_comment=comment.strip(),
            )

            st.success(
                f"Receipt marked as "
                f"{result['final_status']}."
            )
            st.rerun()

        except APIError as exc:
            st.error(str(exc))

def render_delete_receipt(receipt: dict):
    st.divider()
    st.subheader("Delete receipt")

    st.warning(
        "This permanently deletes the receipt record and its Cloudinary image."
    )

    confirm_delete = st.checkbox(
        "I understand this action cannot be undone.",
        key=f"confirm_delete_{receipt['id']}",
    )

    if st.button(
        "Delete receipt permanently",
        type="primary",
        use_container_width=True,
        disabled=not confirm_delete,
        key=f"delete_receipt_{receipt['id']}",
    ):
        try:
            result = delete_receipt(
                token=st.session_state.token,
                receipt_id=receipt["id"],
            )

            st.success(result["message"])

            # Remove stale receipt selection and refresh dashboard
            st.rerun()

        except APIError as exc:
            st.error(str(exc))

        except Exception:
            st.error(
                "The receipt could not be deleted."
            )

def render_admin_dashboard():
    st.title("Admin Dashboard")

    try:
        receipts = get_all_receipts(
            st.session_state.token
        )
    except APIError as exc:
        st.error(str(exc))
        return

    if not receipts:
        st.info("No receipts are available.")
        return

    total = len(receipts)

    approved = sum(
        1
        for receipt in receipts
        if (
            receipt.get("final_status")
            or receipt.get("verification_status")
        )
        == "APPROVED"
    )

    needs_review = sum(
        1
        for receipt in receipts
        if receipt.get("verification_status")
        == "NEEDS_REVIEW"
        and not receipt.get("final_status")
    )

    rejected = sum(
        1
        for receipt in receipts
        if (
            receipt.get("final_status")
            or receipt.get("verification_status")
        )
        == "REJECTED"
    )

    col1, col2, col3, col4 = st.columns(4)

    col1.metric("Total receipts", total)
    col2.metric("Approved", approved)
    col3.metric("Awaiting review", needs_review)
    col4.metric("Rejected", rejected)

    st.subheader("Receipt queue")

    status_filter = st.selectbox(
        "Filter",
        [
            "ALL",
            "AWAITING_REVIEW",
            "APPROVED",
            "REJECTED",
            "NEEDS_MORE_INFORMATION",
        ],
    )

    filtered = receipts

    if status_filter == "AWAITING_REVIEW":
        filtered = [
            receipt
            for receipt in receipts
            if receipt.get("verification_status")
            == "NEEDS_REVIEW"
            and not receipt.get("final_status")
        ]

    elif status_filter != "ALL":
        filtered = [
            receipt
            for receipt in receipts
            if (
                receipt.get("final_status")
                or receipt.get(
                    "verification_status"
                )
            )
            == status_filter
        ]

    rows = []

    for receipt in filtered:
        rows.append(
            {
                "ID": receipt["id"],
                "Employee": receipt[
                    "employee_name"
                ],
                "Vendor": receipt.get("vendor"),
                "Claim": receipt[
                    "claim_amount"
                ],
                "Extracted": receipt.get(
                    "extracted_total"
                ),
                "Date": receipt.get(
                    "receipt_date"
                ),
                "System status": receipt.get(
                    "verification_status"
                ),
                "Final status": receipt.get(
                    "final_status"
                ),
            }
        )

    st.dataframe(
        pd.DataFrame(rows),
        use_container_width=True,
        hide_index=True,
    )

    if not filtered:
        st.info(
            "No receipts match this filter."
        )
        return

    selected_id = st.selectbox(
        "Select receipt for review",
        [receipt["id"] for receipt in filtered],
    )

    render_receipt_detail(
        selected_id,
        admin=True,
    )


def render_authenticated_app():
    render_sidebar()

    role = st.session_state.role

    if role == "ADMIN":
        page = st.sidebar.radio(
            "Navigation",
            [
                "Admin Dashboard",
                "Submit Receipt",
            ],
        )

        if page == "Admin Dashboard":
            render_admin_dashboard()
        else:
            render_upload_page()

    else:
        page = st.sidebar.radio(
            "Navigation",
            [
                "Submit Receipt",
                "My Receipts",
            ],
        )

        if page == "Submit Receipt":
            render_upload_page()
        else:
            render_employee_history()


initialize_session()

if not st.session_state.authenticated:
    render_login()
else:
    render_authenticated_app()