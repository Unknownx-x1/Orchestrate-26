"""
Image & OCR Evidence Interpreter.
Extracts amounts, dates, and vendor details from receipts, invoices, and bank screenshots.
Enforces rule: when event amount is blank, resolve from linked image; never convert blank to zero.
"""

from __future__ import annotations
import re
import logging
from typing import Optional, Dict, Any
from code.ingest.media_loader import MediaItem
from code.intelligence.evidence_firewall import EvidenceFirewall
from code.state.provenance import EvidenceFact, ProvenanceRecord

logger = logging.getLogger(__name__)

# Check pytesseract availability
try:
    import pytesseract
    PYTESSERACT_AVAILABLE = True
except ImportError:
    PYTESSERACT_AVAILABLE = False


class ImageInterpreter:
    """
    Interprets receipt and statement images to extract missing transaction values.
    """

    def __init__(self, firewall: Optional[EvidenceFirewall] = None):
        self.firewall = firewall or EvidenceFirewall()

    def extract_text_from_media(self, media_item: MediaItem) -> str:
        """Runs OCR or image text parsing."""
        if not PYTESSERACT_AVAILABLE:
            logger.debug("Pytesseract not installed; fallback to image metadata parsing.")
            return ""

        img = media_item.open_image()
        if img is None:
            return ""

        try:
            raw_text = pytesseract.image_to_string(img)
            sanitized, _ = self.firewall.sanitize_untrusted_text(raw_text, source_id=media_item.filename)
            return sanitized
        except Exception as e:
            logger.warning(f"OCR failed for {media_item.filename}: {e}")
            return ""

    def extract_amount_from_image(self, media_item: MediaItem, event_id: str) -> Optional[EvidenceFact]:
        """
        Parses image text for transaction amount and returns an EvidenceFact.
        """
        ocr_text = self.extract_text_from_media(media_item)
        if not ocr_text:
            return None

        # Look for amounts (e.g. Total: $123.45, Amount: 45.00, $500.00)
        amount = None
        patterns = [
            r"(?:total|amount|due|balance|paid)\s*[:=]?\s*[\$€£₹]?\s*(\d+(?:\.\d{2})?)",
            r"[\$€£₹]\s*(\d+(?:\.\d{2})?)",
            r"\b(\d+\.\d{2})\b"
        ]

        for pat in patterns:
            match = re.search(pat, ocr_text, re.IGNORECASE)
            if match:
                try:
                    amount = float(match.group(1))
                    break
                except ValueError:
                    continue

        if amount is not None:
            return EvidenceFact(
                entity_type="event",
                entity_id=event_id,
                field_name="amount",
                value=amount,
                status="active",
                provenance=ProvenanceRecord(
                    source_type="image_ocr",
                    source_id=media_item.filename,
                    confidence=0.92,
                    rationale=f"Resolved blank amount from linked image {media_item.filename}"
                )
            )

        return None
