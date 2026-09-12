"""
Deterministic Financial Physics Simulator.
Evaluates 90-day cash flow feasibility and verifies minimum balance safety.
"""

from __future__ import annotations
import datetime
import logging
from typing import Dict, List, Optional
from code.state.financial_twin import FinancialTwin
from code.simulation.fx import FXEngine
from code.simulation.event_expander import EventExpander
from code.simulation.cashflow import DailyCashflowPoint, CashflowTimeline

logger = logging.getLogger(__name__)


class CounterfactualSimulator:
    """
    Simulates cash flows and asserts:
    min(balance[t]) >= minimum_balance for all t in [0, 90].
    """

    def __init__(self, fx_engine: Optional[FXEngine] = None):
        self.fx = fx_engine or FXEngine()
        self.expander = EventExpander(self.fx)

    def simulate(
        self,
        twin: FinancialTwin,
        start_date: datetime.date,
        candidate_schedule: Optional[Dict[datetime.date, float]] = None,
        horizon_days: int = 90
    ) -> CashflowTimeline:
        """
        Simulates the financial trajectory over the horizon.
        candidate_schedule maps dates to payment amounts to be paid on those dates.
        """
        schedule = candidate_schedule or {}
        daily_events = self.expander.expand(twin, start_date=start_date, horizon_days=horizon_days)

        current_balance = float(twin.current_balance)
        min_balance_req = float(twin.minimum_balance_to_keep)

        points: List[DailyCashflowPoint] = []
        violations: List[str] = []
        min_observed_balance = float("inf")
        min_observed_date = start_date

        sorted_dates = sorted(daily_events.keys())

        for dt in sorted_dates:
            opening = current_balance
            inflows, outflows, details = daily_events[dt]
            candidate_pay = float(schedule.get(dt, 0.0))

            closing = opening + inflows - outflows - candidate_pay
            current_balance = closing

            is_below = closing < min_balance_req
            margin = closing - min_balance_req

            if closing < min_observed_balance:
                min_observed_balance = closing
                min_observed_date = dt

            if is_below:
                violations.append(
                    f"Date {dt.isoformat()}: closing balance {closing:.2f} is below minimum {min_balance_req:.2f} (deficit: {abs(margin):.2f})"
                )

            point = DailyCashflowPoint(
                date=dt,
                opening_balance=opening,
                inflows=inflows,
                outflows=outflows,
                candidate_payment=candidate_pay,
                closing_balance=closing,
                minimum_balance_required=min_balance_req,
                is_below_minimum=is_below,
                margin=margin,
                event_details=details
            )
            points.append(point)

        is_safe = len(violations) == 0
        return CashflowTimeline(
            points=points,
            minimum_balance_required=min_balance_req,
            min_balance=min_observed_balance if points else current_balance,
            min_balance_date=min_observed_date,
            is_safe=is_safe,
            violations=violations
        )

    def is_safe(
        self,
        twin: FinancialTwin,
        start_date: datetime.date,
        candidate_schedule: Optional[Dict[datetime.date, float]] = None,
        horizon_days: int = 90
    ) -> bool:
        """Fast oracle check returning True iff the candidate trajectory is 100% safe."""
        timeline = self.simulate(twin, start_date, candidate_schedule, horizon_days=horizon_days)
        return timeline.is_safe

    def find_earliest_safe_date(
        self,
        twin: FinancialTwin,
        amount: float,
        start_date: datetime.date,
        deadline: Optional[datetime.date] = None,
        max_search_days: int = 90
    ) -> Optional[datetime.date]:
        """
        Calculates the earliest date on which paying `amount` in full satisfies the 90-day safety check.
        Independent of payment method or preferences.
        """
        search_limit = min(
            max_search_days,
            (deadline - start_date).days if deadline else max_search_days
        )
        if search_limit < 0:
            return None

        for d in range(search_limit + 1):
            target_date = start_date + datetime.timedelta(days=d)
            schedule = {target_date: float(amount)}
            if self.is_safe(twin, start_date=start_date, candidate_schedule=schedule):
                return target_date
        return None
