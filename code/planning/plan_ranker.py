"""
Deterministic Plan Ranker and Optimizer.
Implements the exact 6-tier lexicographical comparator specified in Section 12.
"""

from __future__ import annotations
import logging
from typing import List, Optional
from code.planning.candidate_generator import CandidatePlan

logger = logging.getLogger(__name__)


class PlanRanker:
    """
    Ranks safe candidate plans using a strict deterministic comparator.
    Criterion order:
    1. Complete by desired completion date
    2. Require no spending changes (fewer changes preferred)
    3. Minimize total amount paid
    4. Start payment earlier
    5. Use fewer payments
    6. Lowest payment_option_id tie-breaker
    """

    @classmethod
    def ranking_key(cls, plan: CandidatePlan):
        # 1. Complete by desired deadline (True=0, False=1)
        tier1 = 0 if plan.completes_before_deadline else 1
        
        # 2. Spending changes (0 changes preferred, then count ascending)
        tier2 = len(plan.spending_interventions)
        
        # 3. Minimize total amount paid
        tier3 = float(plan.total_paid)
        
        # 4. Start payment earlier
        tier4 = plan.start_date
        
        # 5. Fewer payments
        tier5 = len(plan.schedule)
        
        # 6. Lowest payment_option_id tie-breaker (empty strings sorted last if comparing with IDs)
        tier6 = str(plan.payment_option_id or "zzzzzz")

        return (tier1, tier2, tier3, tier4, tier5, tier6)

    @classmethod
    def rank_plans(cls, safe_plans: List[CandidatePlan]) -> List[CandidatePlan]:
        """
        Sorts the list of candidate plans by the deterministic comparator.
        Returns the sorted list with the best plan at index 0.
        """
        if not safe_plans:
            return []
        
        return sorted(safe_plans, key=cls.ranking_key)
