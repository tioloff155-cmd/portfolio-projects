"""
Payment Webhook Processor
Asynchronous webhook handler for decoupled payment validation,
idempotency enforcement, and transaction reconciliation.
"""

import hashlib
import hmac
import json
import time
import uuid
from dataclasses import dataclass, field
from enum import Enum
from typing import Optional


class PaymentStatus(Enum):
    PENDING = "PENDING"
    CONFIRMED = "CONFIRMED"
    FAILED = "FAILED"
    REFUNDED = "REFUNDED"
    DUPLICATE = "DUPLICATE"


@dataclass
class WebhookEvent:
    event_id: str
    event_type: str
    payload: dict
    signature: str
    received_at: float = field(default_factory=time.time)


@dataclass
class PaymentRecord:
    payment_id: str
    amount: float
    currency: str
    status: PaymentStatus
    gateway_ref: str
    user_id: str
    created_at: float = field(default_factory=time.time)
    updated_at: float = field(default_factory=time.time)
    attempts: int = 1


class WebhookProcessor:
    """
    Core payment webhook handler.
    - Validates HMAC signatures from payment gateway.
    - Enforces idempotency via event_id deduplication.
    - Routes events to appropriate handlers.
    - Maintains a ledger for reconciliation.
    """

    def __init__(self, webhook_secret: str = "whsec_test_key"):
        self._secret = webhook_secret.encode()
        self._processed_events: set[str] = set()
        self._ledger: dict[str, PaymentRecord] = {}
        self._event_log: list[dict] = []
        self._stats = {"received": 0, "verified": 0, "rejected": 0, "duplicates": 0}

    def receive(self, raw_body: str, signature: str) -> dict:
        """
        Main entrypoint. Receives raw webhook body and signature.
        Returns a processing result dict.
        """
        self._stats["received"] += 1

        # 1. Verify signature
        if not self._verify_signature(raw_body, signature):
            self._stats["rejected"] += 1
            return {"status": "rejected", "reason": "invalid_signature"}

        self._stats["verified"] += 1

        # 2. Parse event
        try:
            data = json.loads(raw_body)
        except json.JSONDecodeError:
            return {"status": "rejected", "reason": "malformed_json"}

        event = WebhookEvent(
            event_id=data.get("event_id", uuid.uuid4().hex),
            event_type=data.get("type", "unknown"),
            payload=data.get("data", {}),
            signature=signature,
        )

        # 3. Idempotency check
        if event.event_id in self._processed_events:
            self._stats["duplicates"] += 1
            return {"status": "duplicate", "event_id": event.event_id}

        self._processed_events.add(event.event_id)

        # 4. Route to handler
        result = self._route(event)
        self._event_log.append({
            "event_id": event.event_id,
            "type": event.event_type,
            "result": result,
            "timestamp": time.time(),
        })

        return result

    def _verify_signature(self, body: str, signature: str) -> bool:
        expected = hmac.new(self._secret, body.encode(), hashlib.sha256).hexdigest()
        return hmac.compare_digest(expected, signature)

    def _route(self, event: WebhookEvent) -> dict:
        handlers = {
            "payment.completed": self._handle_completed,
            "payment.failed": self._handle_failed,
            "payment.refunded": self._handle_refund,
        }
        handler = handlers.get(event.event_type, self._handle_unknown)
        return handler(event)

    def _handle_completed(self, event: WebhookEvent) -> dict:
        p = event.payload
        pid = p.get("payment_id", uuid.uuid4().hex[:10])

        record = PaymentRecord(
            payment_id=pid,
            amount=p.get("amount", 0),
            currency=p.get("currency", "USD"),
            status=PaymentStatus.CONFIRMED,
            gateway_ref=p.get("gateway_ref", ""),
            user_id=p.get("user_id", "unknown"),
        )
        self._ledger[pid] = record
        return {"status": "processed", "payment_id": pid, "action": "confirmed"}

    def _handle_failed(self, event: WebhookEvent) -> dict:
        p = event.payload
        pid = p.get("payment_id", "")

        if pid in self._ledger:
            self._ledger[pid].status = PaymentStatus.FAILED
            self._ledger[pid].updated_at = time.time()
        else:
            self._ledger[pid] = PaymentRecord(
                payment_id=pid, amount=p.get("amount", 0),
                currency=p.get("currency", "USD"),
                status=PaymentStatus.FAILED,
                gateway_ref=p.get("gateway_ref", ""),
                user_id=p.get("user_id", "unknown"),
            )
        return {"status": "processed", "payment_id": pid, "action": "marked_failed"}

    def _handle_refund(self, event: WebhookEvent) -> dict:
        p = event.payload
        pid = p.get("payment_id", "")

        if pid in self._ledger:
            self._ledger[pid].status = PaymentStatus.REFUNDED
            self._ledger[pid].updated_at = time.time()
            return {"status": "processed", "payment_id": pid, "action": "refunded"}

        return {"status": "warning", "payment_id": pid, "action": "refund_orphan"}

    def _handle_unknown(self, event: WebhookEvent) -> dict:
        return {"status": "ignored", "type": event.event_type}

    def reconcile(self) -> dict:
        """Generate a reconciliation report."""
        confirmed = [r for r in self._ledger.values() if r.status == PaymentStatus.CONFIRMED]
        failed = [r for r in self._ledger.values() if r.status == PaymentStatus.FAILED]
        refunded = [r for r in self._ledger.values() if r.status == PaymentStatus.REFUNDED]

        return {
            "total_payments": len(self._ledger),
            "confirmed": len(confirmed),
            "confirmed_volume": round(sum(r.amount for r in confirmed), 2),
            "failed": len(failed),
            "refunded": len(refunded),
            "net_revenue": round(sum(r.amount for r in confirmed) - sum(r.amount for r in refunded), 2),
        }

    @property
    def stats(self) -> dict:
        return dict(self._stats)

    def sign_payload(self, body: str) -> str:
        """Utility: generate a valid signature for testing."""
        return hmac.new(self._secret, body.encode(), hashlib.sha256).hexdigest()


if __name__ == "__main__":
    processor = WebhookProcessor(webhook_secret="my-gateway-secret")

    events = [
        {"event_id": "evt_001", "type": "payment.completed",
         "data": {"payment_id": "pay_100", "amount": 299.99, "currency": "USD",
                  "user_id": "u_42", "gateway_ref": "gw_abc123"}},
        {"event_id": "evt_002", "type": "payment.completed",
         "data": {"payment_id": "pay_101", "amount": 59.90, "currency": "USD",
                  "user_id": "u_77", "gateway_ref": "gw_def456"}},
        {"event_id": "evt_003", "type": "payment.failed",
         "data": {"payment_id": "pay_102", "amount": 150.00, "currency": "USD",
                  "user_id": "u_13", "gateway_ref": "gw_ghi789"}},
        {"event_id": "evt_004", "type": "payment.refunded",
         "data": {"payment_id": "pay_100", "amount": 299.99, "currency": "USD"}},
        # Duplicate test
        {"event_id": "evt_001", "type": "payment.completed",
         "data": {"payment_id": "pay_100", "amount": 299.99}},
    ]

    for evt in events:
        body = json.dumps(evt)
        sig = processor.sign_payload(body)
        result = processor.receive(body, sig)
        print(f"  {evt['event_id']} ({evt['type']}): {result}")

    # Bad signature test
    bad_result = processor.receive('{"type":"hack"}', "invalidsignature")
    print(f"  Bad sig: {bad_result}")

    print(f"\nStats: {processor.stats}")
    print(f"Reconciliation: {processor.reconcile()}")
