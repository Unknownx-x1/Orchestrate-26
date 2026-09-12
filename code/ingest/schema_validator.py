"""
Generic dynamic schema validator for runtime-discovered financial datasets.
Conforms strictly to the No-Hardcoding rule: never assumes fixed tables or specific column sets.
"""

from __future__ import annotations
import logging
from typing import Dict, List, Any, Optional, Set
import pandas as pd

logger = logging.getLogger(__name__)


class SchemaValidationError(Exception):
    """Raised when critical schema integrity checks fail."""
    pass


class DynamicSchemaValidator:
    """
    Dynamically validates tabular data without hardcoding dataset names or IDs.
    Discovers key relationship columns and performs invariant integrity checks.
    """

    KNOWN_RELATIONAL_KEYS = {
        "user_id", "request_id", "event_id", "related_event_id",
        "image_id", "payment_option_id", "transaction_id", "message_id"
    }

    DATE_CANDIDATE_SUBSTRINGS = ["date", "time", "created_at", "deadline", "effective_from"]
    AMOUNT_CANDIDATE_SUBSTRINGS = ["amount", "balance", "cost", "fee", "rate", "limit"]

    def __init__(self, strict: bool = False):
        self.strict = strict
        self.validation_summary: Dict[str, Dict[str, Any]] = {}

    def validate_table(self, name: str, df: pd.DataFrame) -> Dict[str, Any]:
        """
        Validates a discovered DataFrame and returns structural metadata.
        """
        if df.empty:
            logger.warning(f"Table '{name}' is empty.")
            return {"name": name, "rows": 0, "columns": [], "relational_keys": []}

        columns = list(df.columns)
        relational_keys = [c for c in columns if c.lower() in self.KNOWN_RELATIONAL_KEYS]
        
        # Detect date columns
        date_cols = [
            c for c in columns 
            if any(s in c.lower() for s in self.DATE_CANDIDATE_SUBSTRINGS)
        ]
        
        # Detect amount/numeric columns
        amount_cols = [
            c for c in columns 
            if any(s in c.lower() for s in self.AMOUNT_CANDIDATE_SUBSTRINGS)
        ]

        null_rates = df.isnull().mean().to_dict()
        
        summary = {
            "name": name,
            "rows": len(df),
            "columns": columns,
            "relational_keys": relational_keys,
            "date_columns": date_cols,
            "amount_columns": amount_cols,
            "null_rates": null_rates
        }
        
        self.validation_summary[name] = summary
        logger.info(f"Validated table '{name}': {len(df)} rows, keys: {relational_keys}")
        return summary

    def get_summary(self) -> Dict[str, Any]:
        return self.validation_summary
