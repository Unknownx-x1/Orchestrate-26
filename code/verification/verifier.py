"""
Independent Financial Plan Verifier.
Reconstructs the financial forecast from scratch on an isolated clone,
independent of any generator or model assertions.
"""

from __future__ import annotations
import datetime
import logging
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional
from code.state.financial_twin import FinancialTwin
from code.simulation.simulator import CounterfactualSimulator
from code.planning.candidate_generator import CandidatePlan
from code.verification.invariants import InvariantChecker, InvariantViolation

logger = logging.getLogger(__name__)


@dataclass
class VerificationResult:
    passed: bool
    violations: List[str] = field(default_factory=list)
    min_balance_observed: float = 0.0
    isolated_simulation_safe: bool = False
    binding_constraints: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "passed": self.passed,
            "violations": self.violations,
            "min_balance_observed": round(self.min_balance_observed, 2),
            "isolated_simulation_safe": self.isolated_simulation_safe,
            "binding_constraints": self.binding_constraints
        }


class IndependentVerifier:
    """
    Independent certifying authority.
    Does not trust candidate labels or generator claims.
    """

    def __init__(self):
        # Isolated simulator
        self.simulator = CounterfactualSimulator()

    def verify_plan(
        self,
        twin: FinancialTwin,
        plan: CandidatePlan,
        request_data: Dict[str, Any],
        amount_safe_to_pay: float
    ) -> VerificationResult:
        violations: List[str] = []
        binding: List[str] = []

        requested_amount = float(request_data.get("amount", 0.0))
        deadline_raw = request_data.get("deadline")
        deadline = datetime.date.fromisoformat(deadline_raw) if isinstance(deadline_raw, str) else deadline_raw

        # 1. Invariant: Amount range
        try:
            InvariantChecker.check_amount_range(amount_safe_to_pay, requested_amount)
        except InvariantViolation as e:
            violations.append(str(e))

        # 2. Invariant: Chronology
        try:
            InvariantChecker.check_chronology(plan.schedule)
        except InvariantViolation as e:
            violations.append(str(e))

        # 3. Invariant: Arithmetic
        try:
            InvariantChecker.check_payment_arithmetic(plan.schedule, plan.total_paid)
        except InvariantViolation as e:
            violations.append(str(e))

        # 4. Invariant: Deadline
        try:
            InvariantChecker.check_deadline(plan.completion_date, deadline)
        except InvariantViolation as e:
            violations.append(str(e))
            binding.append("DEADLINE_EXCEEDED")

        # 5. Invariant: Spending interventions
        try:
            InvariantChecker.check_spending_interventions(plan.spending_interventions)
        except InvariantViolation as e:
            violations.append(str(e))

        # 6. Invariant: Independent 90-day Simulation
        isolated_twin = twin.clone()
        # If plan had spending changes, apply them to isolated twin
        if plan.spending_interventions:
            for item in plan.spending_interventions:
                parts = item.split(":")
                act_type = parts[0]
                eid = parts[1]
                for exp in isolated_twin.flexible_recurring_expenses:
                    if exp.event_id == eid:
                        if act_type == "stop":
                            exp.status = "cancelled"
                        elif act_type == "reduce_to":
                            exp.amount = float(parts[2])

        start_date = plan.start_date
        timeline = self.simulator.simulate(isolated_twin, start_date=start_date, candidate_schedule=plan.schedule)

        try:
            InvariantChecker.check_minimum_balance_safety(
                timeline.min_balance, 
                isolated_twin.minimum_balance_to_keep
            )
        except InvariantViolation as e:
            violations.append(str(e))
            binding.append("MINIMUM_BALANCE_BREACH")

        if timeline.min_balance - isolated_twin.minimum_balance_to_keep < 50.0:
            binding.append("LIQUIDITY_BUFFER_TIGHT")

        passed = (len(violations) == 0) and timeline.is_safe

        return VerificationResult(
            passed=passed,
            violations=violations,
            min_balance_observed=timeline.min_balance,
            isolated_simulation_safe=timeline.is_safe,
            binding_constraints=binding
        )
