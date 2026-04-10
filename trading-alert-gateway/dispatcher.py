"""
Trading Alert Gateway
A multi-channel alert dispatcher that delivers execution
telemetry and risk notifications to stakeholders.
"""

import time
import uuid
import threading
import queue
from dataclasses import dataclass, field
from enum import Enum
from typing import Callable, Optional


class AlertSeverity(Enum):
    INFO = "INFO"
    WARNING = "WARNING"
    CRITICAL = "CRITICAL"
    EMERGENCY = "EMERGENCY"


class Channel(Enum):
    CONSOLE = "CONSOLE"
    WEBHOOK = "WEBHOOK"
    EMAIL = "EMAIL"
    TELEGRAM = "TELEGRAM"


@dataclass
class Alert:
    title: str
    message: str
    severity: AlertSeverity
    source: str = "system"
    alert_id: str = field(default_factory=lambda: uuid.uuid4().hex[:10])
    timestamp: float = field(default_factory=time.time)
    metadata: dict = field(default_factory=dict)
    channels: list[Channel] = field(default_factory=lambda: [Channel.CONSOLE])
    delivered: bool = False
    delivery_attempts: int = 0


@dataclass
class DeliveryResult:
    alert_id: str
    channel: Channel
    success: bool
    latency_ms: float
    error: Optional[str] = None


class ChannelHandler:
    """Base class for channel-specific delivery logic."""

    def deliver(self, alert: Alert) -> DeliveryResult:
        raise NotImplementedError


class ConsoleHandler(ChannelHandler):
    """Prints alerts to stdout with severity-based formatting."""

    ICONS = {
        AlertSeverity.INFO: "ℹ️",
        AlertSeverity.WARNING: "⚠️",
        AlertSeverity.CRITICAL: "🔴",
        AlertSeverity.EMERGENCY: "🚨",
    }

    def deliver(self, alert: Alert) -> DeliveryResult:
        start = time.perf_counter()
        icon = self.ICONS.get(alert.severity, "•")
        ts = time.strftime("%H:%M:%S", time.localtime(alert.timestamp))
        print(f"  {icon} [{ts}] [{alert.severity.value}] {alert.title}: {alert.message}")
        elapsed = (time.perf_counter() - start) * 1000
        return DeliveryResult(alert.alert_id, Channel.CONSOLE, True, round(elapsed, 2))


class WebhookHandler(ChannelHandler):
    """Simulates HTTP POST delivery to a webhook endpoint."""

    def __init__(self, url: str = "https://hooks.example.com/alerts"):
        self.url = url

    def deliver(self, alert: Alert) -> DeliveryResult:
        start = time.perf_counter()
        # In production: requests.post(self.url, json=payload)
        time.sleep(0.01)  # simulate network round-trip
        elapsed = (time.perf_counter() - start) * 1000
        return DeliveryResult(alert.alert_id, Channel.WEBHOOK, True, round(elapsed, 2))


class AlertGateway:
    """
    Core alert dispatcher.
    - Asynchronous delivery via worker thread
    - Severity-based routing and filtering
    - Rate limiting per source
    - Delivery tracking and retry
    """

    def __init__(self, min_severity: AlertSeverity = AlertSeverity.INFO):
        self._queue: queue.Queue = queue.Queue()
        self._handlers: dict[Channel, ChannelHandler] = {}
        self._results: list[DeliveryResult] = []
        self._running = False
        self._thread: Optional[threading.Thread] = None
        self._min_severity = min_severity
        self._rate_tracker: dict[str, list[float]] = {}
        self._rate_limit = 10  # max alerts per source per minute
        self._lock = threading.Lock()
        self._stats = {"dispatched": 0, "delivered": 0, "rate_limited": 0, "failed": 0}

        # Register default handler
        self.register_handler(Channel.CONSOLE, ConsoleHandler())

    def register_handler(self, channel: Channel, handler: ChannelHandler):
        self._handlers[channel] = handler

    def start(self):
        self._running = True
        self._thread = threading.Thread(target=self._dispatch_loop, daemon=True)
        self._thread.start()

    def stop(self):
        self._running = False
        self._queue.put(None)
        if self._thread:
            self._thread.join(timeout=3)

    def send(self, title: str, message: str, severity: AlertSeverity,
             source: str = "system", channels: Optional[list[Channel]] = None,
             metadata: Optional[dict] = None):
        """Submit an alert for async delivery."""

        severity_order = [AlertSeverity.INFO, AlertSeverity.WARNING,
                          AlertSeverity.CRITICAL, AlertSeverity.EMERGENCY]
        if severity_order.index(severity) < severity_order.index(self._min_severity):
            return

        if self._is_rate_limited(source):
            self._stats["rate_limited"] += 1
            return

        alert = Alert(
            title=title,
            message=message,
            severity=severity,
            source=source,
            channels=channels or [Channel.CONSOLE],
            metadata=metadata or {},
        )
        self._queue.put(alert)
        self._stats["dispatched"] += 1

    def _is_rate_limited(self, source: str) -> bool:
        now = time.time()
        with self._lock:
            if source not in self._rate_tracker:
                self._rate_tracker[source] = []
            # Clean entries older than 60s
            self._rate_tracker[source] = [t for t in self._rate_tracker[source] if now - t < 60]
            if len(self._rate_tracker[source]) >= self._rate_limit:
                return True
            self._rate_tracker[source].append(now)
        return False

    def _dispatch_loop(self):
        while self._running:
            try:
                alert = self._queue.get(timeout=1)
            except queue.Empty:
                continue
            if alert is None:
                break
            self._deliver(alert)

    def _deliver(self, alert: Alert):
        for channel in alert.channels:
            handler = self._handlers.get(channel)
            if not handler:
                continue
            alert.delivery_attempts += 1
            try:
                result = handler.deliver(alert)
                self._results.append(result)
                if result.success:
                    self._stats["delivered"] += 1
                else:
                    self._stats["failed"] += 1
            except Exception as e:
                self._stats["failed"] += 1
                self._results.append(
                    DeliveryResult(alert.alert_id, channel, False, 0, str(e))
                )
        alert.delivered = True

    @property
    def stats(self) -> dict:
        return dict(self._stats)

    def recent_deliveries(self, n: int = 10) -> list[DeliveryResult]:
        return self._results[-n:]


if __name__ == "__main__":
    gateway = AlertGateway(min_severity=AlertSeverity.INFO)
    gateway.register_handler(Channel.WEBHOOK, WebhookHandler())
    gateway.start()

    # Trade execution alerts
    gateway.send(
        "Trade Executed", "BUY 0.5 BTC @ $67,450.00 | PnL Target: +2.3%",
        AlertSeverity.INFO, source="engine",
        channels=[Channel.CONSOLE, Channel.WEBHOOK],
        metadata={"symbol": "BTC-USD", "side": "BUY", "qty": 0.5}
    )

    gateway.send(
        "Kill Switch Triggered", "Daily drawdown limit reached (-5%). All positions closed.",
        AlertSeverity.CRITICAL, source="risk_manager",
        channels=[Channel.CONSOLE, Channel.WEBHOOK]
    )

    gateway.send(
        "Payout Filter", "EURUSD signal aborted: broker paying 68% (min: 80%)",
        AlertSeverity.WARNING, source="strategy",
        channels=[Channel.CONSOLE]
    )

    gateway.send(
        "Connection Lost", "WebSocket feed from Binance disconnected. Reconnecting...",
        AlertSeverity.EMERGENCY, source="connector",
        channels=[Channel.CONSOLE, Channel.WEBHOOK]
    )

    time.sleep(1)

    print(f"\nGateway stats: {gateway.stats}")
    print(f"\nRecent deliveries:")
    for d in gateway.recent_deliveries():
        print(f"  {d.alert_id} via {d.channel.value}: {'OK' if d.success else 'FAIL'} ({d.latency_ms:.1f}ms)")

    gateway.stop()
