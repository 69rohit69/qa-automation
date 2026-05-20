from pydantic import BaseModel, Field, field_validator


class ExpectedResultPlan(BaseModel):
    """One expected result extracted from AC, in order."""

    er_number: str = Field(description="ER-01, ER-02, ... in the order they appear in AC")
    description: str = Field(description="Short description of what this expected result verifies")


class TestCase(BaseModel):
    test_case_id: str = Field(
        description=(
            "TC-001-POS for first ER positive; TC-001-NEG-01, TC-001-NEG-02 for its negatives; "
            "TC-002-POS for second ER, etc. Number prefix MUST match ER number."
        )
    )
    er_number: str = Field(
        description="ER-01, ER-02, ... — which expected result this case belongs to"
    )
    feature: str = Field(description="Short feature or object name from AC")
    scenario: str = Field(
        description=(
            "One-line Scenario summary. NEG: state requirement-backed violation "
            "(e.g. gift after end date), not invented logic."
        )
    )
    preconditions: str = Field(
        description=(
            "TC-001-POS: full base setup (user, test data, dates). "
            "Later: 'Same base setup as TC-001-POS' plus deltas only."
        )
    )
    steps: str = Field(
        description=(
            "Numbered Steps. Direct navigation to named records. "
            "No repeated App Launcher chains when base setup applies."
        )
    )
    expected_result: str = Field(
        description="Observable Expected Result for this scenario per AC"
    )
    actual_result: str = ""
    screenshot: str = ""
    status: str = "Not Run"


class CoverageItem(BaseModel):
    ac_line: str
    test_case_ids: list[str]


class TestCaseResponse(BaseModel):
    expected_results: list[ExpectedResultPlan] = Field(
        description=(
            "List EVERY expected result from AC first (ER-01, ER-02, ...), "
            "before test case details"
        )
    )
    test_cases: list[TestCase] = Field(
        description=(
            "STRICT ARRAY ORDER (mandatory): "
            "TC-001-POS, TC-001-NEG-01, TC-001-NEG-02, …, "
            "TC-002-POS, TC-002-NEG-01, … "
            "FORBIDDEN: grouping all POS first then all NEG at the end."
        )
    )
    coverage: list[CoverageItem]
    coverage_notes: list[str] = Field(
        default_factory=list,
        description="Checklist: dates, archival, personas, dedup — covered or N/A",
    )

    @field_validator("coverage_notes", "expected_results", mode="before")
    @classmethod
    def _coerce_lists(cls, v):  # noqa: N805
        return v if v is not None else []
