"""
Algorithmic Backtesting Framework
A vectorized strategy testing environment operating on
historical OHLCV data. Computes PnL, drawdown, Sharpe,
and win rate metrics for any signal-based strategy.
"""

import random
import math
from dataclasses import dataclass, field
from typing import Callable, Optional


@dataclass
class Bar:
    timestamp: int
    open: float
    high: float
    low: float
    close: float
    volume: float


@dataclass
class TradeRecord:
    entry_bar: int
    exit_bar: int
    side: str
    entry_price: float
    exit_price: float
    quantity: float
    pnl: float

    @property
    def pnl_pct(self) -> float:
        if self.entry_price == 0:
            return 0.0
        return (self.pnl / (self.entry_price * self.quantity)) * 100


@dataclass
class BacktestResult:
    total_trades: int
    winners: int
    losers: int
    total_pnl: float
    max_drawdown_pct: float
    sharpe_ratio: float
    win_rate: float
    profit_factor: float
    trades: list[TradeRecord]

    def __repr__(self):
        return (
            f"Result(trades={self.total_trades}, win_rate={self.win_rate:.1f}%, "
            f"PnL={self.total_pnl:.2f}, max_dd={self.max_drawdown_pct:.2f}%, "
            f"sharpe={self.sharpe_ratio:.3f}, pf={self.profit_factor:.2f})"
        )


class DataGenerator:
    """Generates synthetic OHLCV bars for backtesting without external data."""

    @staticmethod
    def generate(bars: int = 500, start_price: float = 100.0, volatility: float = 0.02) -> list[Bar]:
        data = []
        price = start_price
        for i in range(bars):
            change = random.gauss(0, volatility) * price
            o = price
            c = price + change
            h = max(o, c) * (1 + random.uniform(0, volatility * 0.5))
            l = min(o, c) * (1 - random.uniform(0, volatility * 0.5))
            v = random.uniform(100, 10000)
            data.append(Bar(timestamp=i, open=round(o, 4), high=round(h, 4),
                            low=round(l, 4), close=round(c, 4), volume=round(v, 2)))
            price = c
        return data


class Indicators:
    """Vectorized technical indicator calculations."""

    @staticmethod
    def sma(closes: list[float], period: int) -> list[Optional[float]]:
        result = [None] * len(closes)
        for i in range(period - 1, len(closes)):
            result[i] = sum(closes[i - period + 1 : i + 1]) / period
        return result

    @staticmethod
    def ema(closes: list[float], period: int) -> list[Optional[float]]:
        result = [None] * len(closes)
        k = 2 / (period + 1)
        result[period - 1] = sum(closes[:period]) / period
        for i in range(period, len(closes)):
            result[i] = closes[i] * k + result[i - 1] * (1 - k)
        return result

    @staticmethod
    def rsi(closes: list[float], period: int = 14) -> list[Optional[float]]:
        result = [None] * len(closes)
        if len(closes) < period + 1:
            return result

        gains, losses = [], []
        for i in range(1, period + 1):
            delta = closes[i] - closes[i - 1]
            gains.append(max(delta, 0))
            losses.append(max(-delta, 0))

        avg_gain = sum(gains) / period
        avg_loss = sum(losses) / period

        for i in range(period, len(closes)):
            if i > period:
                delta = closes[i] - closes[i - 1]
                avg_gain = (avg_gain * (period - 1) + max(delta, 0)) / period
                avg_loss = (avg_loss * (period - 1) + max(-delta, 0)) / period

            if avg_loss == 0:
                result[i] = 100.0
            else:
                rs = avg_gain / avg_loss
                result[i] = 100 - (100 / (1 + rs))

        return result


class Backtester:
    """
    Core backtesting engine. Runs a signal function against historical
    data and tracks equity, trades, and performance metrics.
    """

    def __init__(self, data: list[Bar], initial_capital: float = 10000.0):
        self.data = data
        self.capital = initial_capital
        self.initial_capital = initial_capital

    def run(self, signal_fn: Callable[[list[Bar], int], Optional[str]],
            position_size: float = 0.1) -> BacktestResult:
        """
        Run the backtest.
        signal_fn(data, current_index) -> 'LONG', 'SHORT', 'EXIT', or None
        """
        trades: list[TradeRecord] = []
        equity_curve: list[float] = []
        position = None  # (side, entry_bar, entry_price, qty)
        capital = self.capital

        for i in range(len(self.data)):
            bar = self.data[i]
            signal = signal_fn(self.data, i)

            # Close position
            if position and signal == "EXIT":
                side, entry_bar, entry_price, qty = position
                if side == "LONG":
                    pnl = (bar.close - entry_price) * qty
                else:
                    pnl = (entry_price - bar.close) * qty
                capital += pnl
                trades.append(TradeRecord(entry_bar, i, side, entry_price, bar.close, qty, round(pnl, 4)))
                position = None

            # Open position
            if not position and signal in ("LONG", "SHORT"):
                qty = (capital * position_size) / bar.close
                position = (signal, i, bar.close, qty)

            equity_curve.append(capital)

        # Force close any open position at end
        if position:
            side, entry_bar, entry_price, qty = position
            last = self.data[-1].close
            pnl = (last - entry_price) * qty if side == "LONG" else (entry_price - last) * qty
            capital += pnl
            trades.append(TradeRecord(entry_bar, len(self.data) - 1, side, entry_price, last, qty, round(pnl, 4)))

        return self._compute_metrics(trades, equity_curve)

    def _compute_metrics(self, trades: list[TradeRecord], equity: list[float]) -> BacktestResult:
        winners = [t for t in trades if t.pnl > 0]
        losers = [t for t in trades if t.pnl <= 0]
        total_pnl = sum(t.pnl for t in trades)

        # Max drawdown
        peak = equity[0] if equity else 0
        max_dd = 0
        for eq in equity:
            if eq > peak:
                peak = eq
            dd = (peak - eq) / peak * 100 if peak > 0 else 0
            if dd > max_dd:
                max_dd = dd

        # Sharpe (simplified: daily returns, annualized)
        returns = []
        for i in range(1, len(equity)):
            if equity[i - 1] > 0:
                returns.append((equity[i] - equity[i - 1]) / equity[i - 1])
        if returns and len(returns) > 1:
            avg_r = sum(returns) / len(returns)
            std_r = (sum((r - avg_r) ** 2 for r in returns) / (len(returns) - 1)) ** 0.5
            sharpe = (avg_r / std_r) * math.sqrt(252) if std_r > 0 else 0
        else:
            sharpe = 0

        gross_profit = sum(t.pnl for t in winners) if winners else 0
        gross_loss = abs(sum(t.pnl for t in losers)) if losers else 1

        return BacktestResult(
            total_trades=len(trades),
            winners=len(winners),
            losers=len(losers),
            total_pnl=round(total_pnl, 2),
            max_drawdown_pct=round(max_dd, 2),
            sharpe_ratio=round(sharpe, 3),
            win_rate=round(len(winners) / len(trades) * 100, 1) if trades else 0,
            profit_factor=round(gross_profit / gross_loss, 2) if gross_loss > 0 else 0,
            trades=trades,
        )


# --- Example Strategy: EMA Crossover + RSI Filter ---

def ema_crossover_strategy(data: list[Bar], idx: int) -> Optional[str]:
    """
    LONG when EMA9 crosses above EMA21 and RSI < 70.
    EXIT when EMA9 crosses below EMA21 or RSI > 80.
    """
    if idx < 25:
        return None

    closes = [b.close for b in data[: idx + 1]]
    ema9 = Indicators.ema(closes, 9)
    ema21 = Indicators.ema(closes, 21)
    rsi = Indicators.rsi(closes, 14)

    if ema9[idx] is None or ema21[idx] is None or rsi[idx] is None:
        return None

    prev_fast = ema9[idx - 1] if ema9[idx - 1] else 0
    prev_slow = ema21[idx - 1] if ema21[idx - 1] else 0

    # Entry
    if prev_fast <= prev_slow and ema9[idx] > ema21[idx] and rsi[idx] < 70:
        return "LONG"

    # Exit
    if ema9[idx] < ema21[idx] or rsi[idx] > 80:
        return "EXIT"

    return None


if __name__ == "__main__":
    data = DataGenerator.generate(bars=1000, start_price=100.0, volatility=0.015)
    bt = Backtester(data, initial_capital=10000.0)
    result = bt.run(ema_crossover_strategy, position_size=0.2)

    print(f"Backtest: {result}")
    print(f"\nSample trades:")
    for t in result.trades[:5]:
        print(f"  {t.side} entry={t.entry_price:.2f} exit={t.exit_price:.2f} PnL={t.pnl:.2f} ({t.pnl_pct:.1f}%)")
