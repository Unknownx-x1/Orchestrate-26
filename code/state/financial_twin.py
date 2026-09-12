"""
Financial Digital Twin Module.
Reconstructs and holds the canonical, evidence-backed financial state of a user.
Every material field retains full provenance.
"""

from __future__ import annotations
import copy
import datetime
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional
from code.state.provenance import EvidenceFact, ProvenanceRecord


@dataclass
class FinancialEvent:
    """Represents a scheduled, recurring, or confirmed cash flow event."""
    event_id: str
    name: str = ""
    category: str = "expense"  # 'income', 'protected_expense', 'flexible_expense', 'debt', 'investment'
    amount: float = 0.0
    currency: str = "USD"
    is_recurring: bool = False
    recurrence_interval: str = "none"  # 'daily', 'weekly', 'biweekly', 'monthly', 'none'
    start_date: datetime.date = field(default_factory=datetime.date.today)
    end_date: Optional[datetime.date] = None
    is_flexible: bool = False
    status: str = "active"  # 'active', 'cancelled', 'modified'
    provenance: Optional[ProvenanceRecord] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "event_id": self.event_id,
            "name": self.name,
            "category": self.category,
            "amount": self.amount,
            "currency": self.currency,
            "is_recurring": self.is_recurring,
            "recurrence_interval": self.recurrence_interval,
            "start_date": self.start_date.isoformat() if self.start_date else None,
            "end_date": self.end_date.isoformat() if self.end_date else None,
            "is_flexible": self.is_flexible,
            "status": self.status,
            "provenance": self.provenance.to_dict() if self.provenance else None
        }


@dataclass
class FinancialTwin:
    """
    Complete Financial Digital Twin for a single user.
    """
    user_id: str
    home_currency: str = "USD"
    current_balance: float = 0.0
    minimum_balance_to_keep: float = 0.0
    
    confirmed_income: List[FinancialEvent] = field(default_factory=list)
    protected_expenses: List[FinancialEvent] = field(default_factory=list)
    flexible_recurring_expenses: List[FinancialEvent] = field(default_factory=list)
    confirmed_future_outflows: List[FinancialEvent] = field(default_factory=list)
    debt_commitments: List[FinancialEvent] = field(default_factory=list)
    investment_contributions: List[FinancialEvent] = field(default_factory=list)
    
    payment_preferences: List[str] = field(default_factory=list)
    priorities: List[str] = field(default_factory=list)
    evidence: List[EvidenceFact] = field(default_factory=list)

    def clone(self) -> FinancialTwin:
        """Deep clones the financial twin to isolate counterfactual mutations."""
        return copy.deepcopy(self)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "user_id": self.user_id,
            "home_currency": self.home_currency,
            "current_balance": self.current_balance,
            "minimum_balance_to_keep": self.minimum_balance_to_keep,
            "confirmed_income": [e.to_dict() for e in self.confirmed_income],
            "protected_expenses": [e.to_dict() for e in self.protected_expenses],
            "flexible_recurring_expenses": [e.to_dict() for e in self.flexible_recurring_expenses],
            "confirmed_future_outflows": [e.to_dict() for e in self.confirmed_future_outflows],
            "debt_commitments": [e.to_dict() for e in self.debt_commitments],
            "investment_contributions": [e.to_dict() for e in self.investment_contributions],
            "payment_preferences": self.payment_preferences,
            "priorities": self.priorities,
            "evidence": [ev.to_dict() for ev in self.evidence]
        }
