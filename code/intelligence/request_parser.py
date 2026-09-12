"""
Request Semantic Parser.
Extracts normalized intent, amount, deadline, and partial payment semantics.
Combines structured CSV data with Gemma 4:2B extraction over natural language notes.
"""

from __future__ import annotations
import json
import re
import logging
from typing import Dict, Any, Optional
from code.intelligence.ollama_gemma import OllamaGemmaAdapter
from code.intelligence.evidence_firewall import EvidenceFirewall

logger = logging.getLogger(__name__)


class RequestParser:
    """
    Parses request records and extracts intent semantics via strict JSON schema.
    """

    def __init__(self, adapter: OllamaGemmaAdapter, firewall: Optional[EvidenceFirewall] = None):
        self.adapter = adapter
        self.firewall = firewall or EvidenceFirewall()

    def parse_request(self, raw_record: Dict[str, Any]) -> Dict[str, Any]:
        """
        Extracts normalized request semantics. Structured CSV fields take precedence
        while unstructured notes/text are parsed through the evidence firewall and Gemma.
        """
        clean_record = self.firewall.inspect_and_filter(raw_record)
        
        request_id = str(clean_record.get("request_id", clean_record.get("id", "unknown")))
        user_id = str(clean_record.get("user_id", clean_record.get("userid", "unknown")))
        
        # Base structured fields
        amount = 0.0
        for amt_key in ["amount", "requested_amount", "total", "price"]:
            if amt_key in clean_record and clean_record[amt_key] is not None:
                try:
                    amount = float(clean_record[amt_key])
                    break
                except (ValueError, TypeError):
                    pass

        deadline = str(clean_record.get("deadline", clean_record.get("due_date", "")))
        request_date = str(clean_record.get("request_date", clean_record.get("date", "")))
        allow_partial = bool(clean_record.get("allow_partial", clean_record.get("can_partial", False)))
        notes = str(clean_record.get("notes", clean_record.get("description", clean_record.get("text", ""))))

        # If notes exist, ask Gemma to disambiguate intent and partial payment flexibility
        if notes and len(notes.strip()) > 3:
            prompt = (
                f"Analyze this financial request note and output ONLY valid JSON:\n"
                f"Note: {notes}\n\n"
                f"Required JSON Contract:\n"
                f'{{"intent": "purchase|bill|loan|rent", "allow_partial": true|false, "clarified_deadline": "YYYY-MM-DD or null"}}'
            )
            response = self.adapter.generate(prompt=prompt, system="You are a strict financial semantic parser. Output ONLY valid JSON.")
            try:
                # Extract json substring
                json_match = re.search(r"\{.*\}", response, re.DOTALL)
                if json_match:
                    parsed_json = json.loads(json_match.group(0))
                    if not allow_partial and parsed_json.get("allow_partial") is True:
                        allow_partial = True
                    if not deadline and parsed_json.get("clarified_deadline"):
                        deadline = str(parsed_json["clarified_deadline"])
            except Exception as e:
                logger.debug(f"JSON parse fallback on request {request_id}: {e}")

        return {
            "request_id": request_id,
            "user_id": user_id,
            "amount": amount,
            "request_date": request_date,
            "deadline": deadline,
            "allow_partial": allow_partial,
            "notes": notes
        }
