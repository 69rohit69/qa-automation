"""Enforce test case order: TC-00N-POS, TC-00N-NEG-*, then next ER."""

from __future__ import annotations

import re

from agent.models import TestCase, TestCaseResponse

_ER_RE = re.compile(r"ER-(\d+)", re.I)
_TC_ER_RE = re.compile(r"TC-(\d+)", re.I)
_NEG_RE = re.compile(r"NEG-(\d+)", re.I)


def _er_index(tc: TestCase) -> int:
    for pattern, text in ((_ER_RE, tc.er_number), (_TC_ER_RE, tc.test_case_id)):
        m = pattern.search(text or "")
        if m:
            return int(m.group(1))
    return 9999


def _case_rank(tc: TestCase) -> int:
    """POS=0, NEG-01=1, NEG-02=2, …"""
    tid = tc.test_case_id.upper()
    if "POS" in tid and "NEG" not in tid:
        return 0
    m = _NEG_RE.search(tid)
    return int(m.group(1)) if m else 50


def sort_test_cases(test_cases: list[TestCase]) -> list[TestCase]:
    return sorted(test_cases, key=lambda tc: (_er_index(tc), _case_rank(tc)))


def enforce_response_order(response: TestCaseResponse) -> TestCaseResponse:
    """Reorder test_cases so output is always POS → NEGs per ER, never all POS then all NEG."""
    ordered = sort_test_cases(response.test_cases)
    if ordered == response.test_cases:
        return response
    return response.model_copy(update={"test_cases": ordered})
