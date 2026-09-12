"""
Dynamic Join Engine.
Constructs relational links purely from supplied runtime identifiers:
user_id, request_id, event_id, related_event_id, and image_id.
"""

from __future__ import annotations
import logging
from typing import Dict, List, Any, Optional, Set
import pandas as pd

logger = logging.getLogger(__name__)


class DynamicJoinEngine:
    """
    Connects records across disparate runtime CSV tables based on standard relational keys.
    Operates without hardcoded table structures or schema assumptions.
    """

    PRIMARY_KEYS = ["user_id", "request_id", "event_id", "payment_option_id", "image_id"]
    FOREIGN_KEYS = ["user_id", "request_id", "event_id", "related_event_id", "image_id"]

    def __init__(self, tables: Dict[str, pd.DataFrame]):
        self.tables = tables
        self._normalize_column_names()

    def _normalize_column_names(self):
        """Ensures common variations map to standard identifier names."""
        column_aliases = {
            "userid": "user_id",
            "requestid": "request_id",
            "eventid": "event_id",
            "related_event": "related_event_id",
            "relatedeventid": "related_event_id",
            "imageid": "image_id",
            "img_id": "image_id",
            "payment_option": "payment_option_id",
            "option_id": "payment_option_id"
        }
        for name, df in self.tables.items():
            rename_map = {}
            for col in df.columns:
                lower_col = str(col).strip().lower()
                if lower_col in column_aliases:
                    rename_map[col] = column_aliases[lower_col]
            if rename_map:
                df.rename(columns=rename_map, inplace=True)

    def find_table_with_column(self, col_name: str) -> List[str]:
        """Finds all table names that have the requested column."""
        return [
            name for name, df in self.tables.items() 
            if col_name in df.columns
        ]

    def get_user_records(self, user_id: str) -> Dict[str, List[Dict[str, Any]]]:
        """
        Gathers all records associated with a specific user_id across all loaded tables.
        """
        user_records: Dict[str, List[Dict[str, Any]]] = {}
        for name, df in self.tables.items():
            if "user_id" in df.columns:
                matches = df[df["user_id"].astype(str) == str(user_id)]
                if not matches.empty:
                    user_records[name] = matches.to_dict(orient="records")
        return user_records

    def get_request_records(self, request_id: str) -> Dict[str, List[Dict[str, Any]]]:
        """
        Gathers all records associated with a specific request_id across tables.
        """
        req_records: Dict[str, List[Dict[str, Any]]] = {}
        for name, df in self.tables.items():
            if "request_id" in df.columns:
                matches = df[df["request_id"].astype(str) == str(request_id)]
                if not matches.empty:
                    req_records[name] = matches.to_dict(orient="records")
        return req_records

    def get_related_events(self, event_id: str) -> List[Dict[str, Any]]:
        """
        Finds any event that points to event_id via related_event_id across tables.
        """
        related = []
        for name, df in self.tables.items():
            if "related_event_id" in df.columns:
                matches = df[df["related_event_id"].astype(str) == str(event_id)]
                if not matches.empty:
                    related.extend(matches.to_dict(orient="records"))
        return related
