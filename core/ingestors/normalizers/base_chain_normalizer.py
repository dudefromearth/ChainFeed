#!/usr/bin/env python3
# ===============================================================
# 🌿 Base Chain Normalizer (Interface)
# ===============================================================
# Defines the common interface for all provider-specific
# chain normalizers (Polygon, Tradier, InteractiveBrokers, etc.)
# ===============================================================

from abc import ABC, abstractmethod
from typing import Dict, Any, List
from core.models.chain_models import OptionContract


class ChainNormalizer(ABC):
    """Abstract base class for all chain normalizers."""

    @staticmethod
    @abstractmethod
    def normalize(vendor_payload: Dict[str, Any]) -> List[OptionContract]:
        """Convert a vendor-specific payload into a list of OptionContract models."""
        pass