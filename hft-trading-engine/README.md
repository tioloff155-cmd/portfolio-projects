# OmniQuant // HFT Digital Options Logic Engine

![License](https://img.shields.io/badge/license-MIT-blue.svg)
![Python](https://img.shields.io/badge/python-3.8%2B-green.svg)

OmniQuant is an institutional-grade high-frequency trading (HFT) system designed for automated digital and binary options execution. It leverages a multi-layered technical filtering system combined with dynamic risk management via the Kelly Criterion and a robust capital preservation "Kill Switch".

## 🏗️ Architecture

The system is built on a concurrent asynchronous model to process real-time market telemetry with minimal latency:

-   **HFT Engine (`strategy.py`)**: Consumes WebSocket streams from brokers, maintaining an in-memory rolling state of technical indicators (EMA Crossovers, RSI Momentum, Volatility).
-   **Quant Memory Layer**: A non-blocking thread-safe cache that calculates historical win rates and variance to feed the Kelly sizing algorithm.
-   **Risk Controller**: Implements a dual-layer protection mechanism:
    -   **Stop-Loss/Stop-Win**: Daily percentage-based capital locks persisted in SQLite.
    -   **Payout Filter**: Real-time evaluation of broker spreads to prevent execution in low-payout environments.
-   **Telemetry Dashboard**: A Flask-SocketIO glassmorphism interface for real-time monitoring and parameter hot-swapping.

## 🚀 Key Features

-   **Dynamic Position Sizing**: Full Kelly Criterion scaling based on historical performance and current balance.
-   **EMA 200 Macro Filter**: Strict trend-following execution to avoid counter-trend traps.
-   **Daily Lockout**: Persistent hardware/DB level lockout upon hitting daily risk limits (Kill Switch).
-   **Multi-Asset Scaling**: Capability to monitor and trade up to 10+ concurrent digital assets.

## 🛠️ Installation & Setup

1.  **Environment Setup**:
    ```bash
    python -m venv .venv
    source .venv/bin/activate  # or .venv\Scripts\activate
    pip install -r requirements.txt
    ```

2.  **Configuration**:
    Copy `.env.example` to `.env` and fill in your credentials:
    ```bash
    cp .env.example .env
    ```

3.  **Run**:
    ```bash
    python app.py
    ```
    Access the dashboard at `http://127.0.0.1:8080`.

## 📈 Risk Management Philosophy

OmniQuant operates on the principle that **Capital Preservation > Profit Generation**. The system is designed to run autonomously 24/7 with a focus on high-probability setups.

-   **Max Drawdown Control**: Hard disconnect of WebSocket streams if the $loss\_target$ is breached.
-   **Compounding**: Sizing scales proportionally with balance using initial risk percentages (e.g., 0.5% base).

## 📄 Disclaimer

Trading digital options involves significant risk. This engine is designed for research and algorithmic experimentation. Past performance does not guarantee future results.

---
*Maintained by tioloff155 — Engineered for Precision.*
