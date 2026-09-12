"""
Output Schema & Invariant Validator.
Verifies output.csv rows against all hard submission invariants before writing to disk.
"""

from __future__ import annotations
import datetime
import logging
from typing import List, Dict, Any

logger = logging.getLogger(__name__)


class OutputValidationError(Exception):
    """Raised when an output invariant fails."""
    pass


class OutputValidator:
    """
    Validates output records against required schema and domain invariants.
    """

    REQUIRED_COLUMNS = [
        "request_id",
        "status",
        "recommended_payment_option_id",
        "recommended_payment_method",
        "amount_safe_to_pay",
        "earliest_safe_full_payment_date",
        "payment_schedule",
        "spending_interventions",
        "explanation"
    ]

    ALLOWED_STATUSES = {"APPROVED", "PARTIALLY_APPROVED", "REJECTED", "MODIFIED"}

    @classmethod
    def validate_rows(cls, rows: List[Dict[str, Any]]) -> bool:
        if not rows:
            raise OutputValidationError("Output row list cannot be empty.")

        seen_req_ids = set()
        for idx, row in enumerate(rows):
            # 1. Column presence
            for col in cls.REQUIRED_COLUMNS:
                if col not in row:
                    raise OutputValidationError(f"Row {idx} missing required column '{col}'.")

            # 2. Exactly one row per request
            req_id = str(row["request_id"])
            if req_id in seen_req_ids:
                raise OutputValidationError(f"Duplicate row detected for request_id '{req_id}'.")
            seen_req_ids.add(req_id)

            # 3. Valid status
            status = str(row["status"]).upper()
            if status not in cls.ALLOWED_STATUSES:
                raise OutputValidationError(f"Invalid status '{status}' in row {idx}.")

            # 4. Valid amount_safe_to_pay
            try:
                amt = float(row["amount_safe_to_pay"])
                if amt < 0:
                    raise OutputValidationError(f"Negative amount_safe_to_pay {amt} in row {idx}.")
            except (ValueError, TypeError):
                raise OutputValidationError(f"Non-numeric amount_safe_to_pay in row {idx}.")

        logger.info(f"Successfully validated {len(rows)} output rows against all invariants.")
        return True
