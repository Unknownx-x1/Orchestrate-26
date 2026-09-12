"""
Algorithmic Binary Search & Spending Intervention Optimizer.
Implements:
1. Binary search for exact amount_safe_to_pay today.
2. Combinatorial search for flexible recurring spending interventions (max 3).
Zero hardcoded assumptions.
"""

from __future__ import annotations
import itertools
import logging
from typing import List, Tuple, Dict, Optional, Any
from code.state.financial_twin import FinancialTwin, FinancialEvent
from code.simulation.simulator import CounterfactualSimulator
from code.planning.candidate_generator import CandidatePlan

logger = logging.getLogger(__name__)


class InterventionOptimizer:
    """
    Solves for:
    - Maximum safe payment today via binary search.
    - Minimal flexible spending adjustments required to render unsafe plans safe.
    """

    def __init__(self, simulator: CounterfactualSimulator, max_interventions: int = 3):
        self.simulator = simulator
        self.max_interventions = max_interventions

    def search_amount_safe_to_pay(
        self,
        twin: FinancialTwin,
        request_date: Any,
        requested_amount: float,
        granularity: float = 1.0
    ) -> float:
        """
        Binary searches for the maximum safe payment on request_date in [0, requested_amount].
        Algorithm strictly matches Section 10 of the specification.
        """
        if requested_amount <= 0:
            return 0.0

        # Discretize bounds
        lo = 0
        hi = int(requested_amount / granularity)

        # Pre-check if 0 is even safe
        if not self.simulator.is_safe(twin, start_date=request_date, candidate_schedule={}):
            logger.warning("Baseline financial trajectory is already unsafe without payment.")
            return 0.0

        while lo < hi:
            # Upper midpoint: mid = (lo + hi + 1) // 2
            mid = (lo + hi + 1) // 2
            test_val = float(mid * granularity)
            
            schedule = {request_date: test_val}
            if self.simulator.is_safe(twin, start_date=request_date, candidate_schedule=schedule):
                lo = mid
            else:
                hi = mid - 1

        amount_safe = float(lo * granularity)
        # Exact verification pass
        final_check = self.simulator.is_safe(twin, start_date=request_date, candidate_schedule={request_date: amount_safe})
        if not final_check and amount_safe > 0:
            # Step down if border condition fails
            amount_safe = max(0.0, amount_safe - granularity)

        return min(max(0.0, amount_safe), float(requested_amount))

    def generate_intervention_combinations(self, twin: FinancialTwin) -> List[List[Tuple[str, str, float]]]:
        """
        Generates valid candidate spending intervention sets (0, 1, 2, up to max_interventions).
        Only targets flexible recurring expenses.
        Enforces mutual exclusion: stop and reduce cannot target the same event.
        Intervention format: (type, event_id, new_amount)
        """
        # Filter strictly for flexible recurring expenses
        target_events = [
            e for e in twin.flexible_recurring_expenses 
            if e.is_flexible and e.is_recurring and e.status == "active"
        ]

        if not target_events:
            return [[]]

        possible_single_actions: List[Tuple[str, str, float]] = []
        for e in target_events:
            # 1. Stop intervention
            possible_single_actions.append(("stop", e.event_id, 0.0))
            # 2. Reduce interventions: e.g. 50% reduction, or 25% reduction
            if e.amount > 10:
                possible_single_actions.append(("reduce_to", e.event_id, round(e.amount * 0.5, 2)))
                possible_single_actions.append(("reduce_to", e.event_id, round(e.amount * 0.25, 2)))

        combinations: List[List[Tuple[str, str, float]]] = [[]]

        for k in range(1, min(len(target_events), self.max_interventions) + 1):
            for combo in itertools.combinations(possible_single_actions, k):
                # Check mutual exclusion: no event appears more than once in combo
                event_ids = [action[1] for action in combo]
                if len(event_ids) == len(set(event_ids)):
                    combinations.append(list(combo))

        return combinations

    def apply_interventions_to_twin(
        self,
        twin: FinancialTwin,
        interventions: List[Tuple[str, str, float]]
    ) -> Tuple[FinancialTwin, List[str]]:
        """
        Clones twin and modifies flexible expenses according to interventions.
        Returns: (modified_twin, formatted_strings_list)
        """
        modified = twin.clone()
        formatted_strings = []

        action_map = {action[1]: action for action in interventions}

        new_flexible = []
        for e in modified.flexible_recurring_expenses:
            if e.event_id in action_map:
                act_type, eid, new_amt = action_map[e.event_id]
                if act_type == "stop":
                    e.status = "cancelled"
                    formatted_strings.append(f"stop:{eid}")
                elif act_type == "reduce_to":
                    e.amount = new_amt
                    formatted_strings.append(f"reduce_to:{eid}:{new_amt:.2f}")
            new_flexible.append(e)

        modified.flexible_recurring_expenses = new_flexible
        return modified, formatted_strings
