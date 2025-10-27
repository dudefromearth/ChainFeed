#!/usr/bin/env python3
# ===============================================================
# 🌿 ChainFeed – Canonical Chain Data Models (v2)
# ===============================================================
# Objects that know how to represent, serialize, and reconstitute
# themselves.  No external JSON handling required.
# ===============================================================

from datetime import datetime, timezone
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from typing import Union

# ---------------------------------------------------------------
# 🧩 OptionContract — atomic, self-serializing contract
# ---------------------------------------------------------------
class OptionContract(BaseModel):
    """Normalized option contract snapshot."""

    contract_type: str                # "call" | "put"
    strike: float
    expiry: str                       # ISO format date (YYYY-MM-DD)
    bid: Optional[float] = None
    ask: Optional[float] = None
    mark: Optional[float] = None
    iv: Optional[float] = None
    delta: Optional[float] = None
    gamma: Optional[float] = None
    theta: Optional[float] = None
    vega: Optional[float] = None
    oi: Optional[int] = None
    volume: Optional[int] = None
    updated: Optional[str] = Field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )

    # -----------------------------------------------------------
    # 🧠 Object behavior
    # -----------------------------------------------------------
    def serialize(self) -> Dict[str, Any]:
        """Return a pure dict representation."""
        return self.model_dump()

    @classmethod
    def deserialize(cls, data: Dict[str, Any]) -> "OptionContract":
        """Instantiate from dict representation."""
        return cls(**data)

    def __str__(self):
        return f"{self.contract_type.upper()} {self.strike} exp {self.expiry}"


# ---------------------------------------------------------------
# 🌿 ChainFeed — canonical, self-aware chain feed object
# ---------------------------------------------------------------
class ChainFeed(BaseModel):
    """Canonical representation of an option chain feed."""

    symbol: str
    source: str = "unknown"
    frame_ts: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    count: int = 0
    contracts: List[OptionContract] = Field(default_factory=list)
    metadata: Optional[dict] = Field(default_factory=dict)

    # -----------------------------------------------------------
    # 🔄 Domain Logic
    # -----------------------------------------------------------
    @property
    def atm_strike(self) -> Optional[float]:
        """Approximate ATM strike from median strike."""
        if not self.contracts:
            return None
        strikes = sorted([c.strike for c in self.contracts])
        return strikes[len(strikes) // 2]

    @property
    def greeks_summary(self) -> dict:
        """Aggregate simple Greek totals."""
        totals = {"gamma": 0.0, "vega": 0.0, "theta": 0.0, "delta": 0.0}
        for c in self.contracts:
            for k in totals.keys():
                if getattr(c, k) is not None:
                    totals[k] += getattr(c, k)
        return totals

    # -----------------------------------------------------------
    # 🧠 Object Behavior
    # -----------------------------------------------------------
    def serialize(self) -> dict:
        """Return a Python dict representation."""
        return self.model_dump()

    def persistable(self) -> str:
        """Return JSON string representation (for Redis, transport, etc.)."""
        return self.model_dump_json()

    @classmethod
    def deserialize(cls, data: Union[dict, str]) -> "ChainFeed":
        """Rehydrate from dict or JSON string."""
        if isinstance(data, str):
            return cls.model_validate_json(data)
        return cls(**data)

    def __str__(self):
        return (
            f"<ChainFeed symbol={self.symbol} count={self.count} "
            f"source={self.source} frame={self.frame_ts}>"
        )

    def summary(self) -> str:
        """Human-readable summary for logs."""
        greeks = self.greeks_summary
        return (
            f"[{self.symbol}] {self.count} contracts | "
            f"Δ={greeks['delta']:.2f}, Γ={greeks['gamma']:.2f}, "
            f"Θ={greeks['theta']:.2f}, ν={greeks['vega']:.2f}"
        )