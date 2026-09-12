"""
Evaluation Validators.
Validates outputs and plans against all hard problem invariants.
"""

from __future__ import annotations
import datetime
from typing import List, Dict, Any, Tuple
from code.output.schema_validator import OutputValidator, OutputValidationError
from code.verification.invariants import InvariantChecker, InvariantViolation


class EvaluationSuiteValidators:
    """
    Validation checks used across unit, regression, and adversarial test suites.
    """

    @classmethod
    def validate_submission_file(cls, csv_path: str) -> Tuple[bool, List[str]]:
        import pandas as pd
        errors = []
        try:
            df = pd.read_csv(csv_path)
            rows = df.to_dict(orient="records")
            OutputValidator.validate_rows(rows)
        except Exception as e:
            errors.append(str(e))
        return (len(errors) == 0, errors)

    @classmethod
    def validate_decision_properties(cls, row: Dict[str, Any], requested_amount: float, deadline: datetime.date) -> List[str]:
        violations = []
        # Amount bounds
        amt_safe = float(row.get("amount_safe_to_pay", 0.0))
        if amt_safe < 0 or amt_safe > requested_amount + 1e-4:
            violations.append(f"amount_safe_to_pay {amt_safe} outside [0, {requested_amount}]")

        # Earliest date syntax
        earliest = str(row.get("earliest_safe_full_payment_date", ""))
        if earliest != "none":
            try:
                datetime.date.fromisoformat(earliest)
            except ValueError:
                violations.append(f"Invalid date format for earliest_safe_full_payment_date: '{earliest}'")

        # Spending interventions syntax
        interventions_str = str(row.get("spending_interventions", ""))
        if interventions_str != "none" and interventions_str.strip():
            items = [i.strip() for i in interventions_str.split(";")]
            try:
                InvariantChecker.check_spending_interventions(items)
            except InvariantViolation as iv:
                violations.append(str(iv))

        return violations
