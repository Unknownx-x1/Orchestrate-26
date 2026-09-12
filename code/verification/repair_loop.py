"""
Repair Loop Engine.
Diagnoses verification violations, explores spending interventions or alternate plans,
resimulates, and re-verifies until a certified safe plan is reached.
"""

from __future__ import annotations
import logging
from typing import List, Dict, Any, Optional, Tuple
from code.state.financial_twin import FinancialTwin
from code.planning.candidate_generator import CandidatePlan
from code.planning.intervention_optimizer import InterventionOptimizer
from code.planning.plan_ranker import PlanRanker
from code.verification.verifier import IndependentVerifier, VerificationResult

logger = logging.getLogger(__name__)


class RepairLoop:
    """
    Coordinates candidate diagnosis and iterative repair.
    """

    def __init__(self, verifier: IndependentVerifier, optimizer: InterventionOptimizer):
        self.verifier = verifier
        self.optimizer = optimizer

    def repair_and_verify(
        self,
        twin: FinancialTwin,
        ranked_candidates: List[CandidatePlan],
        request_data: Dict[str, Any],
        amount_safe_to_pay: float
    ) -> Tuple[Optional[CandidatePlan], VerificationResult]:
        """
        Iterates through candidate plans, attempts repair if needed, and returns the first certified plan.
        """
        # 1. First pass: try candidates directly
        for plan in ranked_candidates:
            res = self.verifier.verify_plan(twin, plan, request_data, amount_safe_to_pay)
            if res.passed:
                logger.info(f"Plan {plan.plan_id} ({plan.plan_type}) passed verification directly.")
                return plan, res

        # 2. If all direct candidates failed, attempt spending intervention repairs
        logger.info("Direct candidates failed. Exploring flexible spending intervention repairs...")
        intervention_combos = self.optimizer.generate_intervention_combinations(twin)

        repaired_candidates: List[CandidatePlan] = []
        for plan in ranked_candidates:
            if plan.completes_before_deadline:
                for combo in intervention_combos:
                    if not combo:
                        continue
                    modified_twin, str_interventions = self.optimizer.apply_interventions_to_twin(twin, combo)
                    repaired_plan = CandidatePlan(
                        plan_type=plan.plan_type,
                        payment_option_id=plan.payment_option_id,
                        payment_method=plan.payment_method,
                        schedule=dict(plan.schedule),
                        total_paid=plan.total_paid,
                        start_date=plan.start_date,
                        completion_date=plan.completion_date,
                        spending_interventions=str_interventions,
                        completes_before_deadline=plan.completes_before_deadline
                    )
                    v_res = self.verifier.verify_plan(modified_twin, repaired_plan, request_data, amount_safe_to_pay)
                    if v_res.passed:
                        repaired_candidates.append(repaired_plan)
                        break

        if repaired_candidates:
            ranked_repaired = PlanRanker.rank_plans(repaired_candidates)
            winner = ranked_repaired[0]
            # Final verification pass
            final_res = self.verifier.verify_plan(twin, winner, request_data, amount_safe_to_pay)
            return winner, final_res

        # 3. If everything fails, produce certified REJECT/WAIT plan
        fallback_plan = CandidatePlan(
            plan_type="rejected",
            payment_option_id=None,
            payment_method="none",
            schedule={},
            total_paid=0.0,
            start_date=ranked_candidates[0].start_date if ranked_candidates else request_data.get("request_date"),
            completion_date=ranked_candidates[0].start_date if ranked_candidates else request_data.get("request_date"),
            spending_interventions=[],
            is_safe=True
        )
        final_res = self.verifier.verify_plan(twin, fallback_plan, request_data, amount_safe_to_pay=0.0)
        return fallback_plan, final_res
