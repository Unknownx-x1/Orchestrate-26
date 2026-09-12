"""
Foreign Exchange (FX) Engine.
Converts multi-currency cash flows into user's home currency.
"""

from __future__ import annotations
import logging
from typing import Dict, Optional

logger = logging.getLogger(__name__)


class FXEngine:
    """
    Provides deterministic currency conversion against home currency.
    """

    # Baseline generic rates relative to 1 USD
    DEFAULT_RATES_TO_USD: Dict[str, float] = {
        "USD": 1.0,
        "EUR": 1.08,
        "GBP": 1.28,
        "CAD": 0.74,
        "AUD": 0.65,
        "INR": 0.012,
        "JPY": 0.0067,
    }

    def __init__(self, custom_rates: Optional[Dict[str, float]] = None):
        self.rates_to_usd = dict(self.DEFAULT_RATES_TO_USD)
        if custom_rates:
            for cur, r in custom_rates.items():
                self.rates_to_usd[cur.upper()] = float(r)

    def convert(self, amount: float, from_currency: str, to_currency: str) -> float:
        """Converts amount from one currency to target home currency."""
        from_cur = from_currency.upper().strip()
        to_cur = to_currency.upper().strip()
        
        if from_cur == to_cur:
            return float(amount)

        rate_from = self.rates_to_usd.get(from_cur, 1.0)
        rate_to = self.rates_to_usd.get(to_cur, 1.0)
        
        # Convert to USD first, then to target
        amount_usd = float(amount) * rate_from
        converted = amount_usd / rate_to
        logger.debug(f"FX converted {amount} {from_cur} -> {converted:.2f} {to_cur}")
        return converted
