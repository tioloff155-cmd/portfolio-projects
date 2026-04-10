"""
Realtime Data Aggregator
Normalizes fragmented data feeds from multiple sources into
a unified schema, handling deduplication and late arrivals.
"""

import time
import uuid
import threading
import queue
import random
from dataclasses import dataclass, field
from typing import Optional
from collections import defaultdict


@dataclass
class RawTick:
    source: str
    symbol: str
    price: float
    volume: float
    timestamp: float
    raw_id: str = field(default_factory=lambda: uuid.uuid4().hex[:8])


@dataclass
class NormalizedTick:
    symbol: str
    price: float
    volume: float
    timestamp: float
    source: str
    received_at: float = field(default_factory=time.time)
    latency_ms: float = 0.0

    def __post_init__(self):
        self.latency_ms = round((self.received_at - self.timestamp) * 1000, 2)


class FeedSimulator:
    """Simulates a noisy data source pushing ticks at irregular intervals."""

    def __init__(self, name: str, symbols: list[str], base_prices: dict[str, float]):
        self.name = name
        self.symbols = symbols
        self.base_prices = dict(base_prices)

    def generate_tick(self) -> RawTick:
        sym = random.choice(self.symbols)
        bp = self.base_prices[sym]
        drift = random.gauss(0, bp * 0.001)
        self.base_prices[sym] = bp + drift
        return RawTick(
            source=self.name,
            symbol=sym,
            price=round(self.base_prices[sym], 4),
            volume=round(random.uniform(0.01, 5.0), 4),
            timestamp=time.time() - random.uniform(0, 0.05),
        )


class DataAggregator:
    """
    Core aggregator. Ingests raw ticks from multiple feeds,
    normalizes them, deduplicates by source+timestamp window,
    and stores the latest state per symbol.
    """

    DEDUP_WINDOW = 0.005  # 5ms window for dedup

    def __init__(self):
        self._inbox: queue.Queue = queue.Queue()
        self._latest: dict[str, NormalizedTick] = {}
        self._history: dict[str, list[NormalizedTick]] = defaultdict(list)
        self._seen: set = set()
        self._running = False
        self._thread: Optional[threading.Thread] = None
        self._processed = 0
        self._duplicates = 0
        self._lock = threading.Lock()

    def start(self):
        self._running = True
        self._thread = threading.Thread(target=self._consume_loop, daemon=True)
        self._thread.start()

    def stop(self):
        self._running = False
        if self._thread:
            self._thread.join(timeout=3)

    def ingest(self, tick: RawTick):
        """Push a raw tick into the processing pipeline."""
        self._inbox.put(tick)

    def _consume_loop(self):
        while self._running:
            try:
                raw = self._inbox.get(timeout=0.5)
            except queue.Empty:
                continue
            self._process(raw)

    def _process(self, raw: RawTick):
        # Deduplication key: source + symbol + rounded timestamp
        dedup_key = f"{raw.source}:{raw.symbol}:{round(raw.timestamp / self.DEDUP_WINDOW)}"
        if dedup_key in self._seen:
            self._duplicates += 1
            return
        self._seen.add(dedup_key)

        normalized = NormalizedTick(
            symbol=raw.symbol,
            price=raw.price,
            volume=raw.volume,
            timestamp=raw.timestamp,
            source=raw.source,
        )

        with self._lock:
            self._latest[raw.symbol] = normalized
            self._history[raw.symbol].append(normalized)
            self._processed += 1

    def get_latest(self, symbol: str) -> Optional[NormalizedTick]:
        return self._latest.get(symbol)

    def get_vwap(self, symbol: str, window: int = 50) -> Optional[float]:
        """Calculate volume-weighted average price from recent history."""
        with self._lock:
            ticks = self._history.get(symbol, [])[-window:]
        if not ticks:
            return None
        total_pv = sum(t.price * t.volume for t in ticks)
        total_v = sum(t.volume for t in ticks)
        return round(total_pv / total_v, 4) if total_v > 0 else None

    def summary(self) -> dict:
        return {
            "processed": self._processed,
            "duplicates": self._duplicates,
            "symbols_tracked": len(self._latest),
            "queue_depth": self._inbox.qsize(),
        }


if __name__ == "__main__":
    symbols = ["BTC-USD", "ETH-USD", "SOL-USD"]
    base = {"BTC-USD": 67500.0, "ETH-USD": 3200.0, "SOL-USD": 145.0}

    feeds = [
        FeedSimulator("Binance", symbols, dict(base)),
        FeedSimulator("Kraken", symbols, dict(base)),
        FeedSimulator("Coinbase", symbols, dict(base)),
    ]

    agg = DataAggregator()
    agg.start()

    # Simulate 200 ticks from all feeds
    for _ in range(200):
        for feed in feeds:
            tick = feed.generate_tick()
            agg.ingest(tick)
        time.sleep(0.01)

    time.sleep(1)  # let consumer drain

    for sym in symbols:
        latest = agg.get_latest(sym)
        vwap = agg.get_vwap(sym)
        if latest:
            print(f"{sym}: last={latest.price:.2f} from {latest.source} | VWAP={vwap:.2f} | latency={latest.latency_ms:.1f}ms")

    print(f"\n{agg.summary()}")
    agg.stop()
