"""
Fraud Detection Service
Transaction anomaly detection using statistical Z-score analysis.
Exposes a FastAPI interface for real-time screening of payment flows.
"""

import statistics
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from typing import Optional
from enum import Enum


class RiskLevel(Enum):
    CLEAR = "CLEAR"
    WATCH = "WATCH"
    ALERT = "ALERT"
    BLOCK = "BLOCK"


@dataclass
class Transaction:
    tx_id: str
    user_id: str
    amount: float
    currency: str = "USD"
    timestamp: datetime = field(default_factory=datetime.utcnow)
    merchant: str = ""
    country: str = ""


@dataclass
class ScreeningResult:
    tx_id: str
    risk: RiskLevel
    z_score: float
    velocity_flag: bool
    geo_flag: bool
    reason: str


class FraudDetector:
    """
    Core detection engine. Evaluates transactions against:
    1. Z-score deviation from user spending baseline
    2. Velocity checks (too many txns in short window)
    3. Geographic anomaly (country mismatch from profile)
    """

    VELOCITY_WINDOW = timedelta(minutes=10)
    VELOCITY_LIMIT = 5
    Z_WATCH = 2.0
    Z_ALERT = 3.0
    Z_BLOCK = 4.0

    def __init__(self):
        self.user_history: dict[str, list[Transaction]] = {}
        self.user_profile: dict[str, dict] = {}
        self.blocked: list[ScreeningResult] = []

    def register_profile(self, user_id: str, home_country: str = "BR"):
        self.user_profile[user_id] = {"country": home_country}

    def screen(self, tx: Transaction) -> ScreeningResult:
        """Run all detection rules against a single transaction."""
        history = self.user_history.get(tx.user_id, [])

        z = self._z_score(tx, history)
        vel = self._velocity_check(tx, history)
        geo = self._geo_check(tx)

        risk = self._classify(z, vel, geo)
        reason = self._build_reason(z, vel, geo, tx)

        result = ScreeningResult(
            tx_id=tx.tx_id,
            risk=risk,
            z_score=round(z, 3),
            velocity_flag=vel,
            geo_flag=geo,
            reason=reason,
        )

        # persist
        if tx.user_id not in self.user_history:
            self.user_history[tx.user_id] = []
        self.user_history[tx.user_id].append(tx)

        if risk == RiskLevel.BLOCK:
            self.blocked.append(result)

        return result

    def _z_score(self, tx: Transaction, history: list[Transaction]) -> float:
        if len(history) < 3:
            return 0.0
        amounts = [h.amount for h in history]
        mean = statistics.mean(amounts)
        stdev = statistics.stdev(amounts)
        if stdev == 0:
            return 0.0 if tx.amount == mean else 5.0
        return (tx.amount - mean) / stdev

    def _velocity_check(self, tx: Transaction, history: list[Transaction]) -> bool:
        cutoff = tx.timestamp - self.VELOCITY_WINDOW
        recent = [h for h in history if h.timestamp >= cutoff]
        return len(recent) >= self.VELOCITY_LIMIT

    def _geo_check(self, tx: Transaction) -> bool:
        profile = self.user_profile.get(tx.user_id)
        if not profile or not tx.country:
            return False
        return tx.country != profile["country"]

    def _classify(self, z: float, vel: bool, geo: bool) -> RiskLevel:
        score = 0
        if abs(z) >= self.Z_BLOCK:
            return RiskLevel.BLOCK
        if abs(z) >= self.Z_ALERT:
            score += 3
        elif abs(z) >= self.Z_WATCH:
            score += 1
        if vel:
            score += 2
        if geo:
            score += 1

        if score >= 4:
            return RiskLevel.BLOCK
        elif score >= 2:
            return RiskLevel.ALERT
        elif score >= 1:
            return RiskLevel.WATCH
        return RiskLevel.CLEAR

    def _build_reason(self, z: float, vel: bool, geo: bool, tx: Transaction) -> str:
        parts = []
        if abs(z) >= self.Z_WATCH:
            parts.append(f"Z-score {z:.2f} (amount={tx.amount:.2f})")
        if vel:
            parts.append(f"Velocity breach (>{self.VELOCITY_LIMIT} txns in {self.VELOCITY_WINDOW})")
        if geo:
            profile_country = self.user_profile.get(tx.user_id, {}).get("country", "?")
            parts.append(f"Geo mismatch: tx={tx.country}, profile={profile_country}")
        return "; ".join(parts) if parts else "No anomalies detected."

    def summary(self) -> dict:
        total = sum(len(v) for v in self.user_history.values())
        return {
            "total_screened": total,
            "blocked_count": len(self.blocked),
            "users_tracked": len(self.user_history),
        }


if __name__ == "__main__":
    detector = FraudDetector()
    detector.register_profile("user_001", home_country="BR")

    # Build baseline history
    baseline = [
        Transaction("tx01", "user_001", 50.0, timestamp=datetime(2026, 1, 1, 10, 0)),
        Transaction("tx02", "user_001", 45.0, timestamp=datetime(2026, 1, 1, 11, 0)),
        Transaction("tx03", "user_001", 55.0, timestamp=datetime(2026, 1, 1, 12, 0)),
        Transaction("tx04", "user_001", 48.0, timestamp=datetime(2026, 1, 1, 13, 0)),
        Transaction("tx05", "user_001", 52.0, timestamp=datetime(2026, 1, 1, 14, 0)),
    ]
    for tx in baseline:
        r = detector.screen(tx)
        print(f"  {r.tx_id}: {r.risk.value}")

    # Suspicious transaction: large amount
    suspicious = Transaction("tx06", "user_001", 950.0, timestamp=datetime(2026, 1, 1, 15, 0))
    result = detector.screen(suspicious)
    print(f"\nSuspicious TX: {result.risk.value} | Z={result.z_score} | Reason: {result.reason}")

    # Geo mismatch
    foreign = Transaction("tx07", "user_001", 60.0, country="NG", timestamp=datetime(2026, 1, 1, 15, 1))
    result = detector.screen(foreign)
    print(f"Foreign TX:    {result.risk.value} | Reason: {result.reason}")

    print(f"\nSummary: {detector.summary()}")
