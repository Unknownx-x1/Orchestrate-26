"""
Counterfactual Candidate Plan Generator.
Enumerates plausible payment options dynamically at runtime.
Never assumes a fixed number of offers or hardcoded plan shapes.
"""

from __future__ import annotations
import uuid
import datetime
import logging
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional
from code.state.financial_twin import FinancialTwin
from code.simulation.simulator import CounterfactualSimulator
from code.simulation.cashflow import CashflowTimeline

logger = logging.getLogger(__name__)


@dataclass
class CandidatePlan:
    plan_id: str = field(default_factory=lambda: f"plan_{uuid.uuid4().hex[:8]}")
    plan_type: str = "full"  # 'full', 'partial', 'installment', 'wait', 'intervention'
    payment_option_id: Optional[str] = None
    payment_method: str = "standard"
    schedule: Dict[datetime.date, float] = field(default_factory=dict)
    total_paid: float = 0.0
    start_date: datetime.date = field(default_factory=datetime.date.today)
    completion_date: datetime.date = field(default_factory=datetime.date.today)
    spending_interventions: List[str] = field(default_factory=list)
    
    is_safe: bool = False
    completes_before_deadline: bool = True
    timeline: Optional[CashflowTimeline] = None
    rejection_reasons: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "plan_id": self.plan_id,
            "plan_type": self.plan_type,
            "payment_option_id": self.payment_option_id,
            "payment_method": self.payment_method,
            "total_paid": round(self.total_paid, 2),
            "start_date": self.start_date.isoformat(),
            "completion_date": self.completion_date.isoformat(),
            "spending_interventions": self.spending_interventions,
            "is_safe": self.is_safe,
            "completes_before_deadline": self.completes_before_deadline,
            "schedule": {dt.isoformat(): round(amt, 2) for dt, amt in self.schedule.items()},
            "rejection_reasons": self.rejection_reasons
        }


class CandidateGenerator:
    """
    Generates all candidate payment futures for a given request and financial twin.
    """

    def __init__(self, simulator: CounterfactualSimulator):
        self.simulator = simulator

    def generate_candidates(
        self,
        twin: FinancialTwin,
        request_data: Dict[str, Any],
        payment_options: List[Dict[str, Any]],
        amount_safe_to_pay: float = 0.0
    ) -> List[CandidatePlan]:
        candidates: List[CandidatePlan] = []
        
        amount = float(request_data.get("amount", 0.0))
        req_date = request_data.get("request_date")
        if isinstance(req_date, str) and req_date.strip():
            try:
                req_date = datetime.date.fromisoformat(req_date.strip())
            except Exception:
                req_date = datetime.date.today()
        elif not isinstance(req_date, datetime.date):
            req_date = datetime.date.today()

        deadline = request_data.get("deadline")
        if isinstance(deadline, str) and deadline.strip():
            try:
                deadline = datetime.date.fromisoformat(deadline.strip())
            except Exception:
                deadline = req_date + datetime.timedelta(days=90)
        elif not isinstance(deadline, datetime.date):
            deadline = req_date + datetime.timedelta(days=90)

        allow_partial = bool(request_data.get("allow_partial", False) or request_data.get("can_partial", False))

        # 1. Full payment today
        full_plan = CandidatePlan(
            plan_type="full",
            payment_option_id=None,
            payment_method="full_upfront",
            schedule={req_date: amount},
            total_paid=amount,
            start_date=req_date,
            completion_date=req_date,
            completes_before_deadline=(req_date <= deadline)
        )
        candidates.append(full_plan)

        # 2. Supplied installment options (dynamically discovered from payment_options)
        for opt in payment_options:
            opt_id = str(opt.get("payment_option_id", opt.get("id", "")))
            method = str(opt.get("payment_method", opt.get("method", "installment")))
            num_installments = int(opt.get("num_installments", opt.get("installments", opt.get("count", 1))))
            inst_amount = float(opt.get("installment_amount", opt.get("amount_per_installment", amount / max(num_installments, 1))))
            interval_days = int(opt.get("interval_days", 30 if "month" in str(opt).lower() else 14))

            inst_schedule: Dict[datetime.date, float] = {}
            for i in range(num_installments):
                p_date = req_date + datetime.timedelta(days=i * interval_days)
                inst_schedule[p_date] = inst_amount

            comp_date = max(inst_schedule.keys()) if inst_schedule else req_date
            total_paid = sum(inst_schedule.values())

            inst_plan = CandidatePlan(
                plan_type="installment",
                payment_option_id=opt_id,
                payment_method=method,
                schedule=inst_schedule,
                total_paid=total_paid,
                start_date=req_date,
                completion_date=comp_date,
                completes_before_deadline=(comp_date <= deadline)
            )
            candidates.append(inst_plan)

        # 3. Wait candidate (earliest liquidity arrival date)
        earliest_safe_date = self.simulator.find_earliest_safe_date(twin, amount, req_date, deadline=deadline)
        if earliest_safe_date and earliest_safe_date > req_date:
            wait_plan = CandidatePlan(
                plan_type="wait",
                payment_option_id=None,
                payment_method="delayed_full",
                schedule={earliest_safe_date: amount},
                total_paid=amount,
                start_date=earliest_safe_date,
                completion_date=earliest_safe_date,
                completes_before_deadline=(earliest_safe_date <= deadline)
            )
            candidates.append(wait_plan)

        # 4. Partial payment plan (if allowed and amount_safe_to_pay > 0)
        if allow_partial and amount_safe_to_pay > 0 and amount_safe_to_pay < amount:
            partial_plan = CandidatePlan(
                plan_type="partial",
                payment_option_id=None,
                payment_method="partial_payment",
                schedule={req_date: amount_safe_to_pay},
                total_paid=amount_safe_to_pay,
                start_date=req_date,
                completion_date=req_date,
                completes_before_deadline=(req_date <= deadline)
            )
            candidates.append(partial_plan)

        return candidates
