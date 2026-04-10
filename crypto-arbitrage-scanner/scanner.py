"""
Crypto Arbitrage Scanner
Asynchronous scanner that monitors price feeds across multiple
exchanges and detects spatial arbitrage opportunities.
"""

import asyncio
import random
import time
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class PriceTick:
    exchange: str
    symbol: str
    bid: float
    ask: float
    timestamp: float = field(default_factory=time.time)

    @property
    def mid(self) -> float:
        return (self.bid + self.ask) / 2

    @property
    def spread_pct(self) -> float:
        return ((self.ask - self.bid) / self.mid) * 100


@dataclass
class Opportunity:
    symbol: str
    buy_exchange: str
    sell_exchange: str
    buy_price: float
    sell_price: float
    spread_pct: float
    timestamp: float = field(default_factory=time.time)

    def __repr__(self):
        return (
            f"Arb({self.symbol}: BUY@{self.buy_exchange} {self.buy_price:.2f} "
            f"-> SELL@{self.sell_exchange} {self.sell_price:.2f} | "
            f"edge={self.spread_pct:.3f}%)"
        )


class ExchangeSimulator:
    """
    Simulates a live exchange price feed.
    In production, each instance would wrap a real WebSocket client.
    """

    def __init__(self, name: str, base_price: float, volatility: float = 0.002):
        self.name = name
        self.base_price = base_price
        self.volatility = volatility
        self._current_mid = base_price
        self._spread_bps = random.uniform(5, 20)  # basis points

    async def fetch_price(self, symbol: str) -> PriceTick:
        """Simulate network latency and return a noisy price."""
        await asyncio.sleep(random.uniform(0.01, 0.08))
        drift = random.gauss(0, self.volatility) * self._current_mid
        self._current_mid += drift
        half_spread = (self._spread_bps / 10000) * self._current_mid
        return PriceTick(
            exchange=self.name,
            symbol=symbol,
            bid=round(self._current_mid - half_spread, 4),
            ask=round(self._current_mid + half_spread, 4),
        )


class ArbitrageScanner:
    """
    Core scanner. Polls N exchanges concurrently and evaluates
    cross-exchange spreads for profitable opportunities.
    """

    def __init__(self, exchanges: list[ExchangeSimulator], min_edge: float = 0.05):
        self.exchanges = exchanges
        self.min_edge = min_edge  # minimum profit % to flag
        self.opportunities: list[Opportunity] = []
        self._scan_count = 0

    async def scan_once(self, symbol: str) -> list[Opportunity]:
        """Fetch prices from all exchanges concurrently and compare."""
        tasks = [ex.fetch_price(symbol) for ex in self.exchanges]
        ticks = await asyncio.gather(*tasks)
        self._scan_count += 1

        found = []
        for i, buy_tick in enumerate(ticks):
            for j, sell_tick in enumerate(ticks):
                if i == j:
                    continue
                # Buy at exchange i's ask, sell at exchange j's bid
                if sell_tick.bid > buy_tick.ask:
                    edge = ((sell_tick.bid - buy_tick.ask) / buy_tick.ask) * 100
                    if edge >= self.min_edge:
                        opp = Opportunity(
                            symbol=symbol,
                            buy_exchange=buy_tick.exchange,
                            sell_exchange=sell_tick.exchange,
                            buy_price=buy_tick.ask,
                            sell_price=sell_tick.bid,
                            spread_pct=round(edge, 4),
                        )
                        found.append(opp)
                        self.opportunities.append(opp)

        return found

    async def run(self, symbol: str, cycles: int = 50, interval: float = 0.2):
        """Continuously scan for a given number of cycles."""
        print(f"Scanner started | Symbol: {symbol} | Exchanges: {len(self.exchanges)} | Min edge: {self.min_edge}%")
        for cycle in range(cycles):
            hits = await self.scan_once(symbol)
            if hits:
                for h in hits:
                    print(f"  [{cycle+1:03d}] {h}")
            await asyncio.sleep(interval)

        print(f"\nScan complete. {self._scan_count} cycles | {len(self.opportunities)} opportunities found.")

    def best_opportunity(self) -> Optional[Opportunity]:
        if not self.opportunities:
            return None
        return max(self.opportunities, key=lambda o: o.spread_pct)


if __name__ == "__main__":
    # Create simulated exchanges with slight price drift
    exchanges = [
        ExchangeSimulator("Binance", 67450.0, volatility=0.0015),
        ExchangeSimulator("Kraken", 67455.0, volatility=0.0018),
        ExchangeSimulator("Coinbase", 67440.0, volatility=0.0012),
        ExchangeSimulator("Bybit", 67460.0, volatility=0.0020),
    ]

    scanner = ArbitrageScanner(exchanges, min_edge=0.01)
    asyncio.run(scanner.run("BTC-USD", cycles=30, interval=0.1))

    best = scanner.best_opportunity()
    if best:
        print(f"\nBest opportunity: {best}")
