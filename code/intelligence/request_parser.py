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

        # Extract deadline across aliases
        deadline = ""
        for d_key in ["deadline", "desired_completion_date", "due_date", "due", "completion_date"]:
            if d_key in clean_record and clean_record[d_key] is not None and str(clean_record[d_key]).strip():
                deadline = str(clean_record[d_key]).strip()
                break

        request_date = ""
        for rd_key in ["request_date", "date", "created_at"]:
            if rd_key in clean_record and clean_record[rd_key] is not None and str(clean_record[rd_key]).strip():
                request_date = str(clean_record[rd_key]).strip()
                break

        # Extract allow_partial across aliases
        allow_partial = False
        for p_key in ["allow_partial", "allows_partial_payment", "can_partial", "partial_allowed"]:
            if p_key in clean_record and clean_record[p_key] is not None:
                val = clean_record[p_key]
                if isinstance(val, bool):
                    allow_partial = val
                elif str(val).strip().lower() in {"true", "1", "yes"}:
                    allow_partial = True
                break

        # Extract notes/text across aliases
        notes = ""
        for n_key in ["notes", "request_text", "description", "text", "prompt", "query"]:
            if n_key in clean_record and clean_record[n_key] is not None and str(clean_record[n_key]).strip():
                notes = str(clean_record[n_key]).strip()
                break

        # Extract currency
        currency = str(clean_record.get("currency", "")).strip().upper()
        if not currency and notes:
            for cur_candidate in ["IDR", "ZAR", "EUR", "USD", "INR", "GBP", "JPY", "CAD", "AUD"]:
                if cur_candidate in notes.upper():
                    currency = cur_candidate
                    break
        if not currency:
            currency = "USD"

        # If deadline or allow_partial is missing, or intent needs disambiguation, query Gemma
        if (not deadline or not allow_partial) and notes and len(notes.strip()) > 3:
            prompt = (
                f"Analyze this financial request note and output ONLY valid JSON:\n"
                f"Note: {notes}\n\n"
                f"Required JSON Contract:\n"
                f'{{"intent": "purchase|bill|loan|rent|investment|travel|housing", "allow_partial": true|false, "clarified_deadline": "YYYY-MM-DD or null"}}'
            )
            response = self.adapter.generate(prompt=prompt, system="You are a strict financial semantic parser. Output ONLY valid JSON.")
            try:
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
            "notes": notes,
            "currency": currency
        }
