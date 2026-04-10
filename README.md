# Nazaro Firme | Software Engineer

![Python](https://img.shields.io/badge/Python-3776AB?style=for-the-badge&logo=python&logoColor=white)
![Flask](https://img.shields.io/badge/flask-%23000.svg?style=for-the-badge&logo=flask&logoColor=white)
![SQLite](https://img.shields.io/badge/sqlite-%2307405e.svg?style=for-the-badge&logo=sqlite&logoColor=white)
![JavaScript](https://img.shields.io/badge/javascript-%23323330.svg?style=for-the-badge&logo=javascript&logoColor=%23F7DF1E)
![Docker](https://img.shields.io/badge/docker-%230db7ed.svg?style=for-the-badge&logo=docker&logoColor=white)

Software & Backend Engineer | Python & Data Architecture. Focado em sistemas de baixa latência e purismo técnico (JWT, Heaps, Idempotência).
*Computer Science student @ Estácio. Building high-performance backend systems with Python. Exploring concurrency, quantitative finance engines, and data engineering.*

---

## Technical Scope

- **Core**: Python (FastAPI/Flask), Asynchronous I/O, Concurrency, Multithreading
- **Data & Trading**: Pandas, NumPy, Min-Heaps/Max-Heaps, Kelly Sizing, Time-series
- **Ops & DB**: SQLite (WAL mode), Redis, Docker, Git

---

## Main Projects

### [HFT Trading Engine](./hft-trading-engine)
An algorithmic trading engine built for digital options execution, managing live financial exposure and continuous market data.
- **Challenge**: Processing high-frequency WebSocket telemetry streams without blocking trade execution threads.
- **Stack**: Python, Flask-SocketIO, SQLite WAL.
- **Mechanics**: Implemented a core matching engine using **Min/Max Heaps** for price-time priority and automated risk locking via the proportional Kelly Criterion.

### [ETL Data Pipeline Engine](./etl-pipeline-engine)
A data processing pipeline designed to ingest, clean, and map chaotic spreadsheet data into standardized schemas.
- **Challenge**: Handling inconsistent column formats and large memory footprints during ingestion.
- **Stack**: Python, Pandas, Openpyxl.
- **Mechanics**: Built a functional pipeline utilizing vectorized Pandas operations to reduce processing time and enforce strict data validations.

---

## Selected Enterprise Micro-Architectures & Tooling

High-impact technical implementations focused on architectural purity:

1. **Distributed Task Queue**: Built a producer-consumer background worker system using threads, **Exponential Retry**, and **Dead-lettering** to offload blocking API calls.
2. **Order Matching Engine**: Implemented a memory-optimized limit order book in Python using **Min/Max Heaps** for efficient bid/ask matching.
3. **Algorithmic Fraud Detection**: Developed a **Pandas-based screening microservice** utilizing statistical **Z-Score analysis** and velocity checks to flag anomalies.
4. **Custom JWT Auth Provider**: Set up a centralized Identity Provider using a **pure Python JWT implementation** (no external security frameworks) for maximum control and idempotency.
5. **Real-time Data Aggregator**: Wrote a high-concurrency ingestion script that normalizes chaotic WebSocket streams into a single downstream schema.

---

📫 **Contact**: firmenetto@gmail.com
🔗 **GitHub**: [@tioloff155-cmd](https://github.com/tioloff155-cmd)
