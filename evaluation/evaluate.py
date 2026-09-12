"""
Master Evaluation Suite Runner.
Executes simulator unit tests, adversarial security tests, regression tests,
and the anti-hardcoding static audit.
Outputs a unified test scorecard.
"""

from __future__ import annotations
import sys
import unittest
from pathlib import Path

# Ensure root directory is in sys.path
BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

from audit.static_audit import audit_code_directory


def run_all_evaluations():
    print("\n" + "=" * 70)
    print("      ANTIGRAVITY — MASTER EVALUATION & VERIFICATION SUITE")
    print("=" * 70)

    # 1. Anti-hardcoding static audit
    print("\n[SUITE 1/4] Running Anti-Hardcoding Static Audit...")
    code_dir = BASE_DIR / "code"
    violations = audit_code_directory(code_dir)
    if violations:
        print(f"FAILED: Found {len(violations)} hardcoding violations in code/!")
        for v in violations:
            print(f"  {v}")
        return False
    print("PASSED: Zero hardcoded dataset literals detected in code/.")

    # 2. Simulator Physics Unit Tests
    print("\n[SUITE 2/4] Running Simulator & Temporal Physics Unit Tests...")
    loader = unittest.TestLoader()
    suite2 = loader.discover(str(BASE_DIR / "evaluation"), pattern="simulator_tests.py")
    runner = unittest.TextTestRunner(verbosity=2)
    res2 = runner.run(suite2)
    if not res2.wasSuccessful():
        print("FAILED: Simulator physics tests failed!")
        return False

    # 3. Adversarial Robustness Tests
    print("\n[SUITE 3/4] Running Adversarial Robustness & Firewall Tests...")
    suite3 = loader.discover(str(BASE_DIR / "evaluation"), pattern="adversarial_tests.py")
    res3 = runner.run(suite3)
    if not res3.wasSuccessful():
        print("FAILED: Adversarial tests failed!")
        return False

    # 4. Regression & Determinism Tests
    print("\n[SUITE 4/4] Running Regression & Determinism Tests...")
    suite4 = loader.discover(str(BASE_DIR / "evaluation"), pattern="regression_tests.py")
    res4 = runner.run(suite4)
    if not res4.wasSuccessful():
        print("FAILED: Regression tests failed!")
        return False

    print("\n" + "=" * 70)
    print("      ALL EVALUATION SUITES PASSED (100% INVARIANT COMPLIANCE)")
    print("=" * 70 + "\n")
    return True


if __name__ == "__main__":
    success = run_all_evaluations()
    sys.exit(0 if success else 1)
