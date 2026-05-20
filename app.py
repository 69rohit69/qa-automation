#!/usr/bin/env python3
"""Web UI: paste AC, generate test cases, download CSV, upload to Google Sheets."""

import os

import streamlit as st

from agent.env import ensure_env_loaded
from agent.export import to_csv_string
from agent.generator import generate_test_cases
from agent.models import TestCaseResponse
from agent.sheets import (
    get_sheets_config_issues,
    is_sheets_configured,
    load_sheets_config,
    upload_test_cases,
)

ensure_env_loaded()

provider = os.environ.get("PROVIDER", "gemini").lower()
_key_ok = bool(os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY"))


def _get_last_response() -> TestCaseResponse | None:
    raw = st.session_state.get("last_response")
    if raw is None:
        return None
    if isinstance(raw, TestCaseResponse):
        return raw
    return TestCaseResponse.model_validate(raw)


def _save_response(response: TestCaseResponse) -> None:
    st.session_state["last_response"] = response.model_dump()


def _render_results(response: TestCaseResponse) -> None:
    if response.expected_results:
        st.subheader("Expected results (from AC)")
        er_rows = [
            {"ER": er.er_number, "Description": er.description}
            for er in response.expected_results
        ]
        st.dataframe(er_rows, use_container_width=True, hide_index=True)

    st.subheader("Test cases")
    rows = [
        {
            "Test Case ID": tc.test_case_id,
            "ER": tc.er_number,
            "Feature": tc.feature,
            "Scenario": tc.scenario,
            "Preconditions": tc.preconditions,
            "Steps": tc.steps,
            "Expected Result": tc.expected_result,
        }
        for tc in response.test_cases
    ]
    st.dataframe(rows, use_container_width=True)

    st.subheader("Coverage")
    for item in response.coverage:
        st.markdown(f"- **{item.ac_line}** → `{', '.join(item.test_case_ids)}`")

    if response.coverage_notes:
        st.subheader("Coverage checklist")
        for note in response.coverage_notes:
            st.markdown(f"- {note}")


def _render_export_actions(response: TestCaseResponse) -> None:
    st.subheader("Export")

    if st.session_state.get("sheet_upload_ok"):
        st.success(st.session_state["sheet_upload_ok"])
    if st.session_state.get("sheet_upload_err"):
        st.error(st.session_state["sheet_upload_err"])

    col1, col2, col3 = st.columns(3)

    with col1:
        st.download_button(
            "Download CSV (6 columns)",
            data=to_csv_string(response, include_execution=False),
            file_name="test_cases.csv",
            mime="text/csv",
        )
    with col2:
        st.download_button(
            "Download CSV (full)",
            data=to_csv_string(response, include_execution=True),
            file_name="test_cases_full.csv",
            mime="text/csv",
        )
    with col3:
        sheet_issues = get_sheets_config_issues()
        if sheet_issues:
            st.button("Upload to Google Sheets", disabled=True, key="upload_sheets_disabled")
            for issue in sheet_issues:
                st.caption(issue)
        else:
            sheet_mode = st.radio(
                "Sheet upload mode",
                ["append", "replace"],
                horizontal=True,
                format_func=lambda x: "Append rows" if x == "append" else "Replace tab",
                key="sheet_upload_mode",
            )
            if st.button("Upload to Google Sheets", type="secondary", key="upload_sheets_btn"):
                st.session_state["sheet_upload_ok"] = None
                st.session_state["sheet_upload_err"] = None
                with st.spinner("Uploading to Google Sheets…"):
                    try:
                        url = upload_test_cases(
                            response,
                            mode=sheet_mode,
                            include_execution=True,
                        )
                        n = len(response.test_cases)
                        st.session_state["sheet_upload_ok"] = (
                            f"Uploaded {n} test cases to Google Sheets."
                        )
                        st.session_state["sheet_upload_url"] = url
                    except Exception as exc:
                        st.session_state["sheet_upload_err"] = str(exc)
                st.rerun()

            if st.session_state.get("sheet_upload_url"):
                st.link_button(
                    "Open Google Sheet",
                    st.session_state["sheet_upload_url"],
                    key="open_sheet_link",
                )


st.set_page_config(page_title="Salesforce QA Test Case Agent", layout="wide")
st.title("Salesforce QA — AC to Test Cases")
st.caption(
    "Each AC → ER list → TC-00N-POS + NEGs per ER | "
    f"Provider: **{provider}**"
)

if provider == "gemini" and not _key_ok:
    st.error(
        "GEMINI_API_KEY is empty. Open `.env`, paste your key after `GEMINI_API_KEY=`, "
        "then save the file (Cmd+S) and refresh this page."
    )

with st.expander("Google Sheets setup (one-time)", expanded=not is_sheets_configured()):
    st.markdown(
        """
1. [Google Cloud Console](https://console.cloud.google.com/) → enable **Google Sheets API**.
2. Create a **Service Account** → download JSON key.
3. Set `GOOGLE_CREDENTIALS_PATH` in `.env` to that JSON file path.
4. Share your spreadsheet with the service account `client_email` (Editor).
5. Create tab **Test Cases** (or set `GOOGLE_SHEET_TAB` in `.env`).
        """
    )
    if is_sheets_configured():
        try:
            cfg = load_sheets_config()
            st.success(f"Configured → tab **{cfg.worksheet_name}**")
            st.link_button("Open spreadsheet", cfg.spreadsheet_url)
        except Exception as exc:
            st.warning(str(exc))
    else:
        for issue in get_sheets_config_issues():
            st.error(issue)

context = st.text_area(
    "Optional context (profile, object, sandbox)",
    placeholder="e.g. Sales User, UAT sandbox",
    height=80,
)
ac = st.text_area(
    "Acceptance criteria (paste here)",
    placeholder="Paste full AC including prerequisites, steps, and expected results…",
    height=320,
)

gen_col1, gen_col2 = st.columns([3, 1])
with gen_col2:
    force_refresh = st.checkbox(
        "Force regenerate",
        help="Ignore cache and call the API again (may differ slightly)",
    )

if gen_col1.button("Generate test cases", type="primary", disabled=not ac.strip()):
    st.session_state["sheet_upload_ok"] = None
    st.session_state["sheet_upload_err"] = None
    st.session_state["sheet_upload_url"] = None
    with st.spinner("Analyzing AC → expected results → POS + negatives per ER…"):
        try:
            response, from_cache = generate_test_cases(
                ac,
                context=context,
                force_refresh=force_refresh,
            )
            _save_response(response)
            st.session_state["from_cache"] = from_cache
        except Exception as exc:
            st.error(str(exc))
            st.stop()

last = _get_last_response()
if last is not None:
    if st.session_state.get("from_cache"):
        st.info(
            "Loaded from cache — same AC + context returns the same test cases. "
            "Check **Force regenerate** for a new API run."
        )
    _render_results(last)
    _render_export_actions(last)


# ===================================================
# ADD THIS TO THE ABSOLUTE BOTTOM OF YOUR APP.PY FILE
# ===================================================
import streamlit.web.cli as stcli
import sys

def handler(request, context):
    """Gives Vercel the explicit handler entrypoint it requires to trigger Streamlit"""
    sys.argv = ["streamlit", "run", "app.py", "--server.port=8501", "--server.address=0.0.0.0"]
    stcli.main()

# This ensures it can still be run locally using 'streamlit run app.py'
if __name__ == "__main__":
    sys.argv = ["streamlit", "run", "app.py"]
    stcli.main()