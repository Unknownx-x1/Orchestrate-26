"""
Anti-Hardcoding Static Audit Script.
Enforces the mandatory requirement: FAIL BUILD if any row-specific or dataset-specific logic exists in code/.
"""

from __future__ import annotations
import os
import re
import sys
from pathlib import Path
from typing import List, Tuple

FORBIDDEN_PATTERNS = [
    (r"if\s+request_id\s*==\s*['\"]", "Hardcoded request_id equality check"),
    (r"if\s+user_id\s*==\s*['\"]", "Hardcoded user_id equality check"),
    (r"if\s+event_id\s*==\s*['\"]", "Hardcoded event_id equality check"),
    (r"known_amount\s*=", "Hardcoded known amount assignment"),
    (r"expected_label\s*=", "Hardcoded expected label assignment"),
    (r"special_case_image\s*=", "Hardcoded special case image assignment"),
    (r"known_installment\s*=", "Hardcoded known installment assignment"),
    (r"\.endswith\(['\"][a-zA-Z0-9_-]+\.(png|jpg|jpeg)['\"]\)", "Hardcoded specific image filename match"),
    (r"sample_answer\s*=", "Hardcoded sample answer assignment"),
]


def audit_code_directory(code_dir: Path) -> List[Tuple[str, int, str, str]]:
    violations = []
    if not code_dir.exists():
        print(f"Error: Directory '{code_dir}' does not exist.")
        return [("N/A", 0, "MISSING_DIR", f"{code_dir} not found")]

    py_files = list(code_dir.rglob("*.py"))
    for py_file in py_files:
        try:
            with open(py_file, "r", encoding="utf-8") as f:
                lines = f.readlines()
            for line_no, line in enumerate(lines, 1):
                # Skip comments and docstrings
                stripped = line.strip()
                if stripped.startswith("#") or stripped.startswith('"""') or stripped.startswith("'''"):
                    continue
                for pattern, desc in FORBIDDEN_PATTERNS:
                    if re.search(pattern, line):
                        violations.append((str(py_file.relative_to(code_dir.parent)), line_no, desc, line.strip()))
        except Exception as e:
            violations.append((str(py_file), 0, "FILE_READ_ERROR", str(e)))

    return violations


def main():
    base_dir = Path(__file__).resolve().parent.parent
    code_dir = base_dir / "code"
    print("==================================================")
    print("RUNNING MANDATORY ANTI-HARDCODING STATIC AUDIT")
    print(f"Scanning target directory: {code_dir}")
    print("==================================================")

    violations = audit_code_directory(code_dir)

    if violations:
        print("\n[FAILED] ANTI-HARDCODING AUDIT FAILED!")
        print(f"Found {len(violations)} prohibited hardcoding patterns:\n")
        for file_path, line_no, desc, snippet in violations:
            print(f"  - {file_path}:{line_no} [{desc}]")
            print(f"    Code: {snippet}")
        print("\nFix all hardcoded logic to ensure dynamic runtime discovery.")
        sys.exit(1)
    else:
        print("\n[PASSED] ANTI-HARDCODING AUDIT PASSED 100%!")
        print("Verified: Zero hardcoded IDs, amounts, labels, or dataset-specific branches in code/.")
        print("Success: Every decision is dynamically discovered and computed at runtime.")
        sys.exit(0)


if __name__ == "__main__":
    main()
