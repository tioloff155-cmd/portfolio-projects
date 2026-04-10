"""
Order Matching Engine
A price-time priority matching engine for limit orders.
Supports LIMIT and MARKET order types with a sorted order book.
"""

import time
import uuid
import heapq
from enum import Enum
from dataclasses import dataclass, field
from typing import Optional


class Side(Enum):
    BUY = "BUY"
    SELL = "SELL"


class OrderType(Enum):
    LIMIT = "LIMIT"
    MARKET = "MARKET"


class OrderStatus(Enum):
    OPEN = "OPEN"
    PARTIAL = "PARTIAL"
    FILLED = "FILLED"
    CANCELLED = "CANCELLED"


@dataclass
class Order:
    side: Side
    price: float
    quantity: float
    order_type: OrderType = OrderType.LIMIT
    order_id: str = field(default_factory=lambda: uuid.uuid4().hex[:12])
    timestamp: float = field(default_factory=time.time)
    filled_qty: float = 0.0
    status: OrderStatus = OrderStatus.OPEN

    @property
    def remaining(self) -> float:
        return self.quantity - self.filled_qty

    def fill(self, qty: float):
        self.filled_qty += qty
        if self.remaining <= 0:
            self.status = OrderStatus.FILLED
        else:
            self.status = OrderStatus.PARTIAL


@dataclass
class Trade:
    buy_order_id: str
    sell_order_id: str
    price: float
    quantity: float
    timestamp: float = field(default_factory=time.time)

    def __repr__(self):
        return f"Trade({self.quantity:.4f} @ {self.price:.2f})"


class OrderBook:
    """
    Core matching engine using two heaps:
    - Max-heap for bids (buy orders), keyed by (-price, timestamp)
    - Min-heap for asks (sell orders), keyed by (price, timestamp)
    Price-time priority: best price first, then earliest timestamp.
    """

    def __init__(self, symbol: str = "ASSET"):
        self.symbol = symbol
        self.bids: list = []  # max-heap via negative price
        self.asks: list = []  # min-heap
        self.orders: dict[str, Order] = {}
        self.trades: list[Trade] = []
        self._trade_count = 0

    def submit(self, order: Order) -> list[Trade]:
        """Submit an order to the book. Returns list of resulting trades."""
        self.orders[order.order_id] = order

        if order.order_type == OrderType.MARKET:
            return self._match_market(order)
        return self._match_limit(order)

    def cancel(self, order_id: str) -> bool:
        """Cancel an open order by ID. Returns True if cancelled."""
        if order_id not in self.orders:
            return False
        order = self.orders[order_id]
        if order.status in (OrderStatus.FILLED, OrderStatus.CANCELLED):
            return False
        order.status = OrderStatus.CANCELLED
        return True

    def _match_market(self, order: Order) -> list[Trade]:
        """Match a market order against the opposite side of the book."""
        fills = []
        book = self.asks if order.side == Side.BUY else self.bids

        while order.remaining > 0 and book:
            best = book[0]
            resting = self.orders.get(best[2])

            if resting is None or resting.status in (OrderStatus.FILLED, OrderStatus.CANCELLED):
                heapq.heappop(book)
                continue

            fill_qty = min(order.remaining, resting.remaining)
            trade = Trade(
                buy_order_id=order.order_id if order.side == Side.BUY else resting.order_id,
                sell_order_id=resting.order_id if order.side == Side.BUY else order.order_id,
                price=resting.price,
                quantity=fill_qty,
            )
            order.fill(fill_qty)
            resting.fill(fill_qty)
            fills.append(trade)
            self.trades.append(trade)
            self._trade_count += 1

            if resting.status == OrderStatus.FILLED:
                heapq.heappop(book)

        if order.remaining > 0:
            order.status = OrderStatus.CANCELLED  # unfilled market remainder is killed

        return fills

    def _match_limit(self, order: Order) -> list[Trade]:
        """Match a limit order. Partial fills rest on the book."""
        fills = []

        if order.side == Side.BUY:
            while order.remaining > 0 and self.asks:
                best_ask = self.asks[0]
                ask_price = best_ask[0]

                if ask_price > order.price:
                    break

                resting = self.orders.get(best_ask[2])
                if resting is None or resting.status in (OrderStatus.FILLED, OrderStatus.CANCELLED):
                    heapq.heappop(self.asks)
                    continue

                fill_qty = min(order.remaining, resting.remaining)
                trade = Trade(
                    buy_order_id=order.order_id,
                    sell_order_id=resting.order_id,
                    price=resting.price,
                    quantity=fill_qty,
                )
                order.fill(fill_qty)
                resting.fill(fill_qty)
                fills.append(trade)
                self.trades.append(trade)
                self._trade_count += 1

                if resting.status == OrderStatus.FILLED:
                    heapq.heappop(self.asks)

            if order.remaining > 0:
                heapq.heappush(self.bids, (-order.price, order.timestamp, order.order_id))

        else:  # SELL
            while order.remaining > 0 and self.bids:
                best_bid = self.bids[0]
                bid_price = -best_bid[0]

                if bid_price < order.price:
                    break

                resting = self.orders.get(best_bid[2])
                if resting is None or resting.status in (OrderStatus.FILLED, OrderStatus.CANCELLED):
                    heapq.heappop(self.bids)
                    continue

                fill_qty = min(order.remaining, resting.remaining)
                trade = Trade(
                    buy_order_id=resting.order_id,
                    sell_order_id=order.order_id,
                    price=resting.price,
                    quantity=fill_qty,
                )
                order.fill(fill_qty)
                resting.fill(fill_qty)
                fills.append(trade)
                self.trades.append(trade)
                self._trade_count += 1

                if resting.status == OrderStatus.FILLED:
                    heapq.heappop(self.bids)

            if order.remaining > 0:
                heapq.heappush(self.asks, (order.price, order.timestamp, order.order_id))

        return fills

    def spread(self) -> Optional[float]:
        """Return the current bid-ask spread, or None if one side is empty."""
        best_bid = self._best_bid()
        best_ask = self._best_ask()
        if best_bid is None or best_ask is None:
            return None
        return best_ask - best_bid

    def _best_bid(self) -> Optional[float]:
        while self.bids:
            o = self.orders.get(self.bids[0][2])
            if o and o.status not in (OrderStatus.FILLED, OrderStatus.CANCELLED):
                return -self.bids[0][0]
            heapq.heappop(self.bids)
        return None

    def _best_ask(self) -> Optional[float]:
        while self.asks:
            o = self.orders.get(self.asks[0][2])
            if o and o.status not in (OrderStatus.FILLED, OrderStatus.CANCELLED):
                return self.asks[0][0]
            heapq.heappop(self.asks)
        return None

    def depth(self, levels: int = 5) -> dict:
        """Return top N levels of the book for both sides."""
        bid_levels, ask_levels = {}, {}
        seen = 0
        for entry in sorted(self.bids):
            o = self.orders.get(entry[2])
            if o and o.status not in (OrderStatus.FILLED, OrderStatus.CANCELLED):
                p = -entry[0]
                bid_levels[p] = bid_levels.get(p, 0) + o.remaining
                if len(bid_levels) > levels:
                    break
        seen = 0
        for entry in sorted(self.asks):
            o = self.orders.get(entry[2])
            if o and o.status not in (OrderStatus.FILLED, OrderStatus.CANCELLED):
                p = entry[0]
                ask_levels[p] = ask_levels.get(p, 0) + o.remaining
                if len(ask_levels) > levels:
                    break
        return {"bids": bid_levels, "asks": ask_levels}

    def __repr__(self):
        bb = self._best_bid()
        ba = self._best_ask()
        return f"OrderBook({self.symbol} | Bid: {bb} | Ask: {ba} | Trades: {self._trade_count})"


if __name__ == "__main__":
    book = OrderBook("BTC-USD")

    # Seed the book with resting limit orders
    book.submit(Order(Side.BUY, 100.00, 5.0))
    book.submit(Order(Side.BUY, 99.50, 10.0))
    book.submit(Order(Side.BUY, 99.00, 3.0))
    book.submit(Order(Side.SELL, 101.00, 4.0))
    book.submit(Order(Side.SELL, 101.50, 8.0))
    book.submit(Order(Side.SELL, 102.00, 2.0))

    print(f"Book state: {book}")
    print(f"Spread: {book.spread():.2f}")
    print(f"Depth: {book.depth(3)}")

    # Incoming aggressive buy sweeps the ask
    trades = book.submit(Order(Side.BUY, 101.50, 7.0))
    print(f"\nAggressive BUY 7 @ 101.50 -> {len(trades)} fills:")
    for t in trades:
        print(f"  {t}")

    # Market sell
    trades = book.submit(Order(Side.SELL, 0, 3.0, OrderType.MARKET))
    print(f"\nMARKET SELL 3 -> {len(trades)} fills:")
    for t in trades:
        print(f"  {t}")

    print(f"\nFinal state: {book}")
