"""
Temporal Event Expander.
Expands one-time and recurring cash flow events into a day-by-day sequence over the 90-day horizon.
"""

from __future__ import annotations
import datetime
import calendar
import logging
from typing import List, Dict, Any, Tuple
from code.state.financial_twin import FinancialTwin, FinancialEvent
from code.simulation.fx import FXEngine

logger = logging.getLogger(__name__)


class EventExpander:
    """
    Projects financial events onto a daily timeline [start_date, start_date + horizon_days].
    """

    def __init__(self, fx_engine: FXEngine):
        self.fx = fx_engine

    def _add_months(self, sourcedate: datetime.date, months: int) -> datetime.date:
        month = sourcedate.month - 1 + months
        year = sourcedate.year + month // 12
        month = month % 12 + 1
        day = min(sourcedate.day, calendar.monthrange(year, month)[1])
        return datetime.date(year, month, day)

    def expand(self, twin: FinancialTwin, start_date: datetime.date, horizon_days: int = 90) -> Dict[datetime.date, Tuple[float, float, List[Dict[str, Any]]]]:
        """
        Returns:
            Dictionary mapping each date in horizon to (inflows, outflows, event_details_list)
        """
        end_horizon = start_date + datetime.timedelta(days=horizon_days)
        daily_cashflow: Dict[datetime.date, Tuple[float, float, List[Dict[str, Any]]]] = {
            start_date + datetime.timedelta(days=d): (0.0, 0.0, [])
            for d in range(horizon_days + 1)
        }

        all_events = (
            twin.confirmed_income +
            twin.protected_expenses +
            twin.flexible_recurring_expenses +
            twin.confirmed_future_outflows +
            twin.debt_commitments +
            twin.investment_contributions
        )

        for ev in all_events:
            if ev.status == "cancelled":
                continue

            amount_home = self.fx.convert(ev.amount, ev.currency, twin.home_currency)
            is_inflow = (ev.category == "income")
            
            # Determine occurrence dates
            occurrences: List[datetime.date] = []
            ev_start = ev.start_date or start_date
            ev_end = ev.end_date or end_horizon

            if not ev.is_recurring:
                if start_date <= ev_start <= end_horizon:
                    occurrences.append(ev_start)
            else:
                curr = ev_start
                # Advance curr up to start_date if needed
                interval = (ev.recurrence_interval or "monthly").lower()
                
                while curr <= end_horizon and curr <= ev_end:
                    if curr >= start_date:
                        occurrences.append(curr)

                    if interval == "daily":
                        curr += datetime.timedelta(days=1)
                    elif interval == "weekly":
                        curr += datetime.timedelta(days=7)
                    elif interval == "biweekly":
                        curr += datetime.timedelta(days=14)
                    elif interval == "monthly":
                        curr = self._add_months(curr, 1)
                    elif interval == "quarterly":
                        curr = self._add_months(curr, 3)
                    else:
                        break

            for dt in occurrences:
                if dt in daily_cashflow:
                    cur_in, cur_out, details = daily_cashflow[dt]
                    if is_inflow:
                        cur_in += amount_home
                    else:
                        cur_out += amount_home
                    details.append({
                        "event_id": ev.event_id,
                        "name": ev.name,
                        "category": ev.category,
                        "amount": amount_home,
                        "is_inflow": is_inflow,
                        "is_flexible": ev.is_flexible
                    })
                    daily_cashflow[dt] = (cur_in, cur_out, details)

        return daily_cashflow
