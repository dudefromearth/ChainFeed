#!/usr/bin/env python3
# ===============================================================
# 🌿 Polygon Chain Normalizer
# ===============================================================
# Converts Polygon.io snapshot payloads → List[OptionContract]
# ===============================================================

from typing import Dict, Any, List
from core.models.chain_models import OptionContract
from core.ingestors.normalizers.base_chain_normalizer import ChainNormalizer


class PolygonChainNormalizer(ChainNormalizer):
    """Maps Polygon snapshot/options API payload → List[OptionContract]."""

    @staticmethod
    def normalize(vendor_payload: Dict[str, Any]) -> List[OptionContract]:
        """Normalize Polygon snapshot payload into OptionContract models."""
        opts = vendor_payload.get("options", []) or []
        contracts: List[OptionContract] = []

        for o in opts:
            d = o.get("details", {}) or {}
            g = o.get("greeks", {}) or {}
            q = o.get("last_quote", {}) or {}
            day = o.get("day", {}) or {}

            contracts.append(
                OptionContract(
                    contract_type=d.get("contract_type", "").lower(),
                    strike=float(d.get("strike_price", 0)),
                    expiry=d.get("expiration_date"),
                    bid=q.get("bid"),
                    ask=q.get("ask"),
                    mark=q.get("mark") or q.get("midpoint"),
                    iv=g.get("implied_volatility"),
                    delta=g.get("delta"),
                    gamma=g.get("gamma"),
                    theta=g.get("theta"),
                    vega=g.get("vega"),
                    oi=day.get("open_interest"),
                    volume=day.get("volume"),
                    updated=o.get("updated"),
                )
            )

        return contracts