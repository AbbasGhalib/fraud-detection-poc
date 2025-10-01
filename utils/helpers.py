"""
Helper utilities for the Tax Document Fraud Detection POC.
"""
from __future__ import annotations

from typing import Dict, Any, List, Optional
import logging

# Thresholds and constants
BLUR_THRESHOLD: float = 100.0
HIGH_INSTALLMENT_THRESHOLD: float = 10000.0

logger = logging.getLogger(__name__)


def safe_get(d: Dict[str, Any], key: str, default: Any = None) -> Any:
	"""Safely get a key from a dict, returning default if missing or falsy."""
	val = d.get(key)
	return val if val not in (None, "") else default


def coerce_float(value: Any) -> Optional[float]:
	"""Try to coerce a value to float, returning None on failure."""
	if value is None:
		return None
	try:
		return float(str(value).replace(",", "").replace("$", "").strip())
	except Exception:
		return None


def compare_last4_sin(t1_sin: Optional[str], noa_sin: Optional[str]) -> bool:
	"""Compare last 4 digits of SIN when available."""
	if not t1_sin or not noa_sin:
		return False
	return str(t1_sin)[-4:] == str(noa_sin)[-4:]


def calc_confidence(match: bool, base: int = 85, penalty: int = 30) -> int:
	"""Simple confidence heuristic."""
	return max(0, min(100, base if match else base - penalty))
