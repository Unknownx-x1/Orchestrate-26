"""
Hard Invariant Definitions.
Formal mathematical and structural checks for financial plan safety and integrity.
"""

from __future__ import annotations
import datetime
from typing import List, Dict, Any, Optional
from code.state.financial_twin import FinancialTwin
from code.planning.candidate_generator import CandidatePlan


class InvariantViolation(Exception):
    """Raised when an independent verification check fails."""
    def __init__(self, code: str, message: str):
        super().__init__(f"[{code}] {message}")
        self.code = code
        self.message = message


class InvariantChecker:
    """
    Independent validator for hard business and safety constraints.
    """

    @classmethod
    def check_amount_range(cls, amount_safe_to_pay: float, requested_amount: float):
        if amount_safe_to_pay < -1e-6:
            raise InvariantViolation("INV_AMOUNT_NEGATIVE", f"amount_safe_to_pay {amount_safe_to_pay} cannot be negative.")
        if amount_safe_to_pay > requested_amount + 1e-6:
            raise InvariantViolation(
                "INV_AMOUNT_EXCEEDS_REQUEST", 
                f"amount_safe_to_pay {amount_safe_to_pay} exceeds requested {requested_amount}."
            )

    @classmethod
    def check_chronology(cls, schedule: Dict[datetime.date, float]):
        dates = list(schedule.keys())
        for i in range(len(dates) - 1):
            if dates[i] > dates[i + 1]:
                raise InvariantViolation(
                    "INV_CHRONOLOGY", 
                    f"Payment dates must be chronological: {dates[i]} > {dates[i+1]}"
                )

    @classmethod
    def check_payment_arithmetic(cls, schedule: Dict[datetime.date, float], total_declared: float):
        sum_schedule = sum(schedule.values())
        if abs(sum_schedule - total_declared) > 0.05:
            raise InvariantViolation(
                "INV_ARITHMETIC_MISMATCH", 
                f"Sum of payments ({sum_schedule:.2f}) does not match declared total ({total_declared:.2f})"
            )

    @classmethod
    def check_deadline(cls, completion_date: datetime.date, deadline: Optional[datetime.date]):
        if deadline and completion_date > deadline:
            raise InvariantViolation(
                "INV_DEADLINE_EXCEEDED", 
                f"Completion date {completion_date} exceeds deadline {deadline}"
            )

    @classmethod
    def check_minimum_balance_safety(cls, min_observed: float, required_min: float):
        if min_observed < required_min - 1e-6:
            raise InvariantViolation(
                "INV_MINIMUM_BALANCE_BREACH", 
                f"Balance fell to {min_observed:.2f}, breaching minimum reserve {required_min:.2f}"
            )

    @classmethod
    def check_spending_interventions(cls, interventions: List[str]):
        if len(interventions) > 3:
            raise InvariantViolation(
                "INV_INTERVENTIONS_EXCEEDED", 
                f"Exceeded max 3 spending interventions: got {len(interventions)}"
            )
        
        # Check syntax & mutual exclusion
        seen_events = set()
        for item in interventions:
            parts = item.split(":")
            if len(parts) < 2 or parts[0] not in {"stop", "reduce_to"}:
                raise InvariantViolation("INV_SYNTAX_ERROR", f"Invalid intervention syntax: '{item}'")
            event_id = parts[1]
            if event_id in seen_events:
                raise InvariantViolation(
                    "INV_MUTUAL_EXCLUSION", 
                    f"Event '{event_id}' has multiple conflicting interventions."
                )
            seen_events.add(event_id)
