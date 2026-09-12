"""
Cashflow Timeline Data Structures.
Captures discrete daily financial physics trajectory across the forecast horizon.
"""

from __future__ import annotations
import datetime
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any


@dataclass
class DailyCashflowPoint:
    date: datetime.date
    opening_balance: float
    inflows: float
    outflows: float
    candidate_payment: float
    closing_balance: float
    minimum_balance_required: float
    is_below_minimum: bool = False
    margin: float = 0.0
    event_details: List[Dict[str, Any]] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "date": self.date.isoformat(),
            "opening_balance": round(self.opening_balance, 2),
            "inflows": round(self.inflows, 2),
            "outflows": round(self.outflows, 2),
            "candidate_payment": round(self.candidate_payment, 2),
            "closing_balance": round(self.closing_balance, 2),
            "minimum_balance_required": round(self.minimum_balance_required, 2),
            "is_below_minimum": self.is_below_minimum,
            "margin": round(self.margin, 2)
        }


@dataclass
class CashflowTimeline:
    points: List[DailyCashflowPoint]
    minimum_balance_required: float
    min_balance: float
    min_balance_date: datetime.date
    is_safe: bool
    violations: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "is_safe": self.is_safe,
            "min_balance": round(self.min_balance, 2),
            "min_balance_date": self.min_balance_date.isoformat() if self.min_balance_date else None,
            "minimum_balance_required": round(self.minimum_balance_required, 2),
            "violations_count": len(self.violations),
            "violations": self.violations[:5],
            "total_days": len(self.points)
        }
