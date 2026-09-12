"""
Evidence Firewall Module.
Strictly isolates untrusted external data (messages, OCR receipts, images)
from executable system instructions.
Facts are extracted as passive data; embedded system instructions are neutralized and ignored.
"""

from __future__ import annotations
import re
import logging
from typing import Dict, Any, Tuple, List

logger = logging.getLogger(__name__)


class EvidenceFirewall:
    """
    Sanitizes raw text and OCR streams to prevent prompt injection,
    instruction hijacking, and policy override attempts.
    """

    INJECTION_PATTERNS = [
        re.compile(r"ignore\s+(all\s+)?(previous|prior|system)\s+instructions", re.IGNORECASE),
        re.compile(r"disregard\s+(the\s+)?(above|rules|constraints)", re.IGNORECASE),
        re.compile(r"you\s+are\s+now\s+(in\s+)?(admin|developer|god)\s+mode", re.IGNORECASE),
        re.compile(r"set\s+(balance|amount|status)\s+to\b", re.IGNORECASE),
        re.compile(r"approve\s+(this\s+)?(plan|request|loan)\s+unconditionally", re.IGNORECASE),
        re.compile(r"bypass\s+(safety|verification|checks)", re.IGNORECASE),
        re.compile(r"<system>.*?</system>", re.IGNORECASE | re.DOTALL),
        re.compile(r"\[system\]", re.IGNORECASE),
    ]

    def __init__(self):
        self.flagged_injections: List[Dict[str, Any]] = []

    def sanitize_untrusted_text(self, text: str, source_id: str = "") -> Tuple[str, bool]:
        """
        Sanitizes untrusted text by stripping out command injection constructs.
        Returns: (sanitized_text, injection_detected_flag)
        """
        if not text or not isinstance(text, str):
            return "", False

        cleaned = text
        detected = False

        for pattern in self.INJECTION_PATTERNS:
            if pattern.search(cleaned):
                detected = True
                cleaned = pattern.sub("[UNTRUSTED_INSTRUCTION_STRIPPED]", cleaned)
                self.flagged_injections.append({
                    "source_id": source_id,
                    "matched_pattern": pattern.pattern,
                    "original_snippet": text[:100]
                })
                logger.warning(f"Firewall intercepted injection attempt from {source_id}!")

        return cleaned, detected

    def inspect_and_filter(self, record: Dict[str, Any], source_id_key: str = "source_id") -> Dict[str, Any]:
        """
        Deep-sanitizes all string fields in a record.
        """
        sanitized_record = {}
        source_id = str(record.get(source_id_key, record.get("event_id", record.get("message_id", "unknown"))))
        
        for k, v in record.items():
            if isinstance(v, str):
                clean_val, _ = self.sanitize_untrusted_text(v, source_id=source_id)
                sanitized_record[k] = clean_val
            else:
                sanitized_record[k] = v
        return sanitized_record
