"""
Regression and Determinism Test Suite.
Verifies that the entire pipeline executes deterministically and adheres to all schema contracts.
"""

import unittest
import tempfile
import shutil
from pathlib import Path
import pandas as pd
from code.app import AntigravityPipeline
from code.output.schema_validator import OutputValidator


class TestRegressionAndDeterminism(unittest.TestCase):

    def setUp(self):
        self.temp_dir = Path(tempfile.mkdtemp())
        self.data_dir = self.temp_dir / "data"
        self.data_dir.mkdir()

        # Create minimal synthetic dataset fixture
        users_df = pd.DataFrame([{
            "user_id": "u_test_101",
            "current_balance": 1500.0,
            "minimum_balance_to_keep": 300.0,
            "home_currency": "USD"
        }])
        users_df.to_csv(self.data_dir / "users.csv", index=False)

        requests_df = pd.DataFrame([{
            "request_id": "req_test_001",
            "user_id": "u_test_101",
            "amount": 400.0,
            "request_date": "2026-02-01",
            "deadline": "2026-03-01",
            "notes": "Flight ticket purchase"
        }])
        requests_df.to_csv(self.data_dir / "requests.csv", index=False)

        options_df = pd.DataFrame([{
            "payment_option_id": "opt_bnpl_3x",
            "request_id": "req_test_001",
            "payment_method": "installment",
            "num_installments": 3,
            "installment_amount": 135.0,
            "interval_days": 14
        }])
        options_df.to_csv(self.data_dir / "payment_options.csv", index=False)

    def tearDown(self):
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_pipeline_end_to_end_determinism(self):
        """Runs pipeline twice and asserts bit-for-bit consistency in numerical decisions."""
        out_csv1 = self.temp_dir / "out1.csv"
        cards1 = self.temp_dir / "cards1.json"
        pipeline1 = AntigravityPipeline(data_dir=self.data_dir)
        res1 = pipeline1.run(output_csv_path=out_csv1, decision_cards_path=cards1)

        out_csv2 = self.temp_dir / "out2.csv"
        cards2 = self.temp_dir / "cards2.json"
        pipeline2 = AntigravityPipeline(data_dir=self.data_dir)
        res2 = pipeline2.run(output_csv_path=out_csv2, decision_cards_path=cards2)

        df1 = pd.read_csv(out_csv1)
        df2 = pd.read_csv(out_csv2)

        self.assertEqual(len(df1), 1)
        self.assertEqual(df1["status"].iloc[0], df2["status"].iloc[0])
        self.assertEqual(df1["amount_safe_to_pay"].iloc[0], df2["amount_safe_to_pay"].iloc[0])
        self.assertEqual(df1["recommended_payment_method"].iloc[0], df2["recommended_payment_method"].iloc[0])

        # Validate schema
        self.assertTrue(OutputValidator.validate_rows(df1.to_dict(orient="records")))


if __name__ == "__main__":
    unittest.main()
