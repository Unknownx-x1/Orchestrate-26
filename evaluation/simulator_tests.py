"""
Simulator and Temporal Physics Unit Tests.
Verifies cash-flow physics, recurrence mathematics, binary search, and FX conversion.
Zero reliance on hardcoded dataset constants.
"""

import unittest
import datetime
from code.state.financial_twin import FinancialTwin, FinancialEvent
from code.simulation.fx import FXEngine
from code.simulation.event_expander import EventExpander
from code.simulation.simulator import CounterfactualSimulator
from code.planning.intervention_optimizer import InterventionOptimizer


class TestSimulatorPhysics(unittest.TestCase):

    def setUp(self):
        self.fx = FXEngine()
        self.simulator = CounterfactualSimulator(self.fx)
        self.optimizer = InterventionOptimizer(self.simulator)
        self.today = datetime.date(2026, 1, 1)

    def test_daily_balance_physics(self):
        """Validates B[t] = B[t-1] + Inflows - Outflows - Payment."""
        twin = FinancialTwin(
            user_id="test_user_generic",
            current_balance=1000.0,
            minimum_balance_to_keep=200.0
        )
        # Add daily expense of 10.0
        twin.protected_expenses.append(
            FinancialEvent(
                event_id="daily_exp",
                amount=10.0,
                is_recurring=True,
                recurrence_interval="daily",
                start_date=self.today
            )
        )
        timeline = self.simulator.simulate(twin, start_date=self.today, horizon_days=10)
        self.assertTrue(timeline.is_safe)
        self.assertEqual(len(timeline.points), 11)
        # Day 1 closing balance: 1000 - 10 = 990
        self.assertAlmostEqual(timeline.points[0].closing_balance, 990.0)
        # Day 10 closing balance: 1000 - 110 = 890
        self.assertAlmostEqual(timeline.points[10].closing_balance, 890.0)

    def test_minimum_balance_breach_detection(self):
        """Asserts that a balance falling below reserve is caught immediately."""
        twin = FinancialTwin(
            user_id="test_user_generic",
            current_balance=500.0,
            minimum_balance_to_keep=300.0
        )
        # Payment of 250 leaves balance at 250 (< 300 reserve)
        schedule = {self.today: 250.0}
        timeline = self.simulator.simulate(twin, start_date=self.today, candidate_schedule=schedule, horizon_days=5)
        self.assertFalse(timeline.is_safe)
        self.assertTrue(len(timeline.violations) > 0)

    def test_binary_search_amount_safe_to_pay(self):
        """Verifies binary search calculates exact maximum safe amount today."""
        twin = FinancialTwin(
            user_id="test_user_generic",
            current_balance=1000.0,
            minimum_balance_to_keep=200.0
        )
        # Max safe to pay should be 1000 - 200 = 800
        safe_amt = self.optimizer.search_amount_safe_to_pay(
            twin,
            request_date=self.today,
            requested_amount=1500.0,
            granularity=1.0
        )
        self.assertAlmostEqual(safe_amt, 800.0)

    def test_earliest_safe_date(self):
        """Tests calculation of earliest date where full payment is feasible after salary."""
        twin = FinancialTwin(
            user_id="test_user_generic",
            current_balance=100.0,
            minimum_balance_to_keep=50.0
        )
        # Salary arrives on day 5
        salary_date = self.today + datetime.timedelta(days=5)
        twin.confirmed_income.append(
            FinancialEvent(
                event_id="salary_event",
                category="income",
                amount=1000.0,
                is_recurring=False,
                start_date=salary_date
            )
        )
        # Attempting to pay 500
        earliest = self.simulator.find_earliest_safe_date(twin, amount=500.0, start_date=self.today)
        self.assertEqual(earliest, salary_date)

    def test_fx_conversion_in_simulation(self):
        """Tests multi-currency normalization in 90-day simulation."""
        twin = FinancialTwin(
            user_id="test_user_generic",
            home_currency="USD",
            current_balance=1000.0,
            minimum_balance_to_keep=100.0
        )
        # Foreign EUR expense (1 EUR = ~1.08 USD)
        twin.protected_expenses.append(
            FinancialEvent(
                event_id="eur_exp",
                amount=100.0,
                currency="EUR",
                is_recurring=False,
                start_date=self.today
            )
        )
        timeline = self.simulator.simulate(twin, start_date=self.today, horizon_days=1)
        expected_deduction = 100.0 * 1.08
        self.assertAlmostEqual(timeline.points[0].closing_balance, 1000.0 - expected_deduction, places=2)


if __name__ == "__main__":
    unittest.main()
