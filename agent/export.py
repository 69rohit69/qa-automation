import csv
import io
from pathlib import Path

from agent.models import TestCase, TestCaseResponse

# Primary columns (user-facing)
COLUMNS = [
    "Test Case ID",
    "Feature",
    "Scenario",
    "Preconditions",
    "Steps",
    "Expected Result",
]

# Optional execution columns
EXECUTION_COLUMNS = [
    "Actual Result",
    "Screenshot",
    "Status",
]

ALL_COLUMNS = COLUMNS + EXECUTION_COLUMNS

SHEET_ER_COLUMN = "ER"


def sheet_headers(*, include_execution: bool = True) -> list[str]:
    headers = [COLUMNS[0], SHEET_ER_COLUMN, *COLUMNS[1:]]
    if include_execution:
        headers.extend(EXECUTION_COLUMNS)
    return headers


def _sheet_row(tc: TestCase, *, include_execution: bool = True) -> list[str]:
    row = [
        tc.test_case_id,
        tc.er_number,
        tc.feature,
        tc.scenario,
        tc.preconditions,
        tc.steps,
        tc.expected_result,
    ]
    if include_execution:
        row.extend([tc.actual_result, tc.screenshot, tc.status])
    return row


def sheet_rows(
    response: TestCaseResponse, *, include_execution: bool = True
) -> list[list[str]]:
    return [_sheet_row(tc, include_execution=include_execution) for tc in response.test_cases]


def _row(tc: TestCase, *, include_execution: bool = True) -> list[str]:
    base = [
        tc.test_case_id,
        tc.feature,
        tc.scenario,
        tc.preconditions,
        tc.steps,
        tc.expected_result,
    ]
    if include_execution:
        base.extend([tc.actual_result, tc.screenshot, tc.status])
    return base


def to_csv_string(response: TestCaseResponse, *, include_execution: bool = True) -> str:
    buf = io.StringIO()
    writer = csv.writer(buf)
    cols = ALL_COLUMNS if include_execution else COLUMNS
    writer.writerow(cols)
    for tc in response.test_cases:
        writer.writerow(_row(tc, include_execution=include_execution))
    return buf.getvalue()


def save_csv(
    response: TestCaseResponse,
    path: str | Path,
    *,
    include_execution: bool = True,
) -> Path:
    out = Path(path)
    out.write_text(to_csv_string(response, include_execution=include_execution), encoding="utf-8")
    return out


def print_table(response: TestCaseResponse) -> None:
    if response.expected_results:
        print("Expected results identified:")
        for er in response.expected_results:
            print(f"  {er.er_number}: {er.description}")
        print()

    rows = [_row(tc) for tc in response.test_cases]
    widths = [len(h) for h in COLUMNS]
    for row in rows:
        for i, cell in enumerate(row):
            widths[i] = min(max(widths[i], len(cell)), 50)

    def fmt_row(cells: list[str]) -> str:
        parts = []
        for i, cell in enumerate(cells):
            text = cell.replace("\n", " ")
            if len(text) > widths[i]:
                text = text[: widths[i] - 3] + "..."
            parts.append(text.ljust(widths[i]))
        return " | ".join(parts)

    print(fmt_row(COLUMNS))
    print("-+-".join("-" * w for w in widths))
    for row in rows:
        print(fmt_row(row))

    print("\nCoverage:")
    for item in response.coverage:
        ids = ", ".join(item.test_case_ids)
        print(f"  - {item.ac_line} -> {ids}")

    if response.coverage_notes:
        print("\nCoverage checklist:")
        for note in response.coverage_notes:
            print(f"  - {note}")
