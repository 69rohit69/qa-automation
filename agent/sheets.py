"""Upload test cases to Google Sheets via service account."""

from __future__ import annotations

import os
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

import gspread
from google.oauth2.service_account import Credentials

from agent.env import PROJECT_ROOT, ensure_env_loaded
from agent.export import sheet_headers, sheet_rows
from agent.models import TestCaseResponse

SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive",
]


@dataclass
class SheetsConfig:
    spreadsheet_id: str
    worksheet_name: str
    credentials_path: Path

    @property
    def spreadsheet_url(self) -> str:
        return f"https://docs.google.com/spreadsheets/d/{self.spreadsheet_id}"


def get_sheets_config_issues() -> list[str]:
    """Return human-readable list of what is still missing (empty = ready)."""
    ensure_env_loaded()
    issues: list[str] = []

    spreadsheet_id = (os.environ.get("GOOGLE_SPREADSHEET_ID") or "").strip()
    if not spreadsheet_id:
        issues.append("Add GOOGLE_SPREADSHEET_ID to .env (spreadsheet ID from the URL).")

    creds_raw = (os.environ.get("GOOGLE_CREDENTIALS_PATH") or "").strip()
    if not creds_raw:
        issues.append(
            "Add GOOGLE_CREDENTIALS_PATH to .env "
            "(e.g. credentials/google-service-account.json)."
        )
    else:
        cred_path = Path(creds_raw)
        if not cred_path.is_absolute():
            cred_path = PROJECT_ROOT / cred_path
        if not cred_path.is_file():
            issues.append(
                f"Service account JSON not found at: {cred_path}\n"
                "Download the key from Google Cloud Console → Service Accounts → Keys → "
                "Add key → JSON, and save it to that path."
            )

    return issues


def is_sheets_configured() -> bool:
    return len(get_sheets_config_issues()) == 0


def load_sheets_config() -> SheetsConfig:
    ensure_env_loaded()
    spreadsheet_id = (os.environ.get("GOOGLE_SPREADSHEET_ID") or "").strip()
    if not spreadsheet_id:
        raise RuntimeError(
            "GOOGLE_SPREADSHEET_ID is not set in .env (ID from the sheet URL)."
        )

    worksheet_name = (os.environ.get("GOOGLE_SHEET_TAB") or "Test Cases").strip()
    creds_raw = (os.environ.get("GOOGLE_CREDENTIALS_PATH") or "").strip()
    if not creds_raw:
        raise RuntimeError(
            "GOOGLE_CREDENTIALS_PATH is not set in .env "
            "(path to service account JSON file)."
        )

    cred_path = Path(creds_raw)
    if not cred_path.is_absolute():
        cred_path = PROJECT_ROOT / cred_path
    if not cred_path.is_file():
        raise FileNotFoundError(f"Google credentials file not found: {cred_path}")

    return SheetsConfig(
        spreadsheet_id=spreadsheet_id,
        worksheet_name=worksheet_name,
        credentials_path=cred_path,
    )


def _client(config: SheetsConfig) -> gspread.Client:
    creds = Credentials.from_service_account_file(
        str(config.credentials_path),
        scopes=SCOPES,
    )
    return gspread.authorize(creds)


def _worksheet(client: gspread.Client, config: SheetsConfig) -> gspread.Worksheet:
    spreadsheet = client.open_by_key(config.spreadsheet_id)
    try:
        return spreadsheet.worksheet(config.worksheet_name)
    except gspread.WorksheetNotFound:
        return spreadsheet.add_worksheet(
            title=config.worksheet_name,
            rows=1000,
            cols=20,
        )


def upload_test_cases(
    response: TestCaseResponse,
    *,
    mode: str = "append",
    include_execution: bool = True,
) -> str:
    """
    Upload test cases to Google Sheets.

    mode:
      - append: add rows below existing data (writes header if sheet is empty)
      - replace: clear the tab and write only this run

    Returns the spreadsheet URL.
    """
    if mode not in ("append", "replace"):
        raise ValueError("mode must be 'append' or 'replace'")

    config = load_sheets_config()
    client = _client(config)
    ws = _worksheet(client, config)

    headers = sheet_headers(include_execution=include_execution)
    data = sheet_rows(response, include_execution=include_execution)

    if mode == "replace":
        ws.clear()
        block = [headers, *data]
        ws.update(block, "A1", value_input_option="USER_ENTERED")
        return config.spreadsheet_url

    if not data:
        raise RuntimeError("No test cases to upload.")

    existing = ws.get_all_values()
    if not existing:
        ws.update([headers, *data], "A1", value_input_option="USER_ENTERED")
        return config.spreadsheet_url

    stamp = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    separator = [f"--- Generated {stamp} ---"] + [""] * (len(headers) - 1)
    # Append after last row (do not use table_range — it can misplace rows)
    ws.append_rows(
        [separator, headers, *data],
        value_input_option="USER_ENTERED",
    )
    return config.spreadsheet_url
