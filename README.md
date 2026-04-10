# Nazaro Firme | Software Engineer

![Python](https://img.shields.io/badge/Python-3776AB?style=for-the-badge&logo=python&logoColor=white)
![Flask](https://img.shields.io/badge/flask-%23000.svg?style=for-the-badge&logo=flask&logoColor=white)
![SQLite](https://img.shields.io/badge/sqlite-%2307405e.svg?style=for-the-badge&logo=sqlite&logoColor=white)
![JavaScript](https://img.shields.io/badge/javascript-%23323330.svg?style=for-the-badge&logo=javascript&logoColor=%23F7DF1E)
![Docker](https://img.shields.io/badge/docker-%230db7ed.svg?style=for-the-badge&logo=docker&logoColor=white)

Backend engineer focused on data-intensive applications and low-latency systems. I build reliable infrastructure, APIs, and trading engines in Python, emphasizing concurrency and pragmatic problem-solving.

---

## Technical Scope

- **Core**: Python, REST APIs, WebSocket/SocketIO, Flask
- **Data & Trading**: Pandas, NumPy, Kelly Sizing, Time-series analysis
- **Ops & DB**: Threads, Asynchronous I/O, SQLite (WAL mode), Git

---

## Main Projects

### [HFT Trading Engine](./hft-trading-engine)
An algorithmic trading engine built for digital options execution, managing live financial exposure and continuous market data.
- **Challenge**: Processing high-frequency WebSocket telemetry streams without blocking trade execution threads.
- **Stack**: Python, Flask-SocketIO, SQLite WAL.
- **Mechanics**: Implemented a concurrent worker model with isolated I/O loops and automated risk locking via the proportional Kelly Criterion.

### [ETL Data Pipeline Engine](./etl-pipeline-engine)
A data processing pipeline designed to ingest, clean, and map chaotic spreadsheet data into standardized schemas.
- **Challenge**: Handling inconsistent column formats and large memory footprints during ingestion.
- **Stack**: Python, Pandas, Openpyxl.
- **Mechanics**: Built a functional pipeline utilizing vectorized Pandas operations to reduce processing time and enforce strict data validations.

### [Recruitment Data API](./recruit-data-api)
A centralized web backend for tracking candidate lifecycle events and storing applicant states.
- **Challenge**: Designing a maintainable MVC structure with decoupled presentation logic.
- **Stack**: Python, Flask, SQLite, Vanilla JS.
- **Mechanics**: Delivered a RESTful application separating routing, database transactions, and frontend rendering for clear testability.

### [Stateless Edge Portfolio](./edge-portfolio-app)
A high-performance personal portfolio deployment avoiding heavy front-end frameworks. 
- **Challenge**: Achieving sub-50ms Time-To-First-Byte (TTFB) and perfect Lighthouse scores.
- **Stack**: Python, Flask, CSS Grid.
- **Mechanics**: Used pure server-side rendering and zero external JS dependencies to deliver a 100% lightweight edge application.

---

## Private & NDA Work

Selected contract work and internal tooling built under NDA:

1. **Distributed Task Queue Manager**: Built a producer-consumer background worker system using Redis to offload blocking API calls.
2. **Order Matching Engine Shell**: Drafted a memory-optimized limit order book in Python to match fast transactions.
3. **Fraud Detection Service**: Developed a Pandas-based screening microservice that flags transactional anomalies based on historical velocity.
4. **Auth Provider Component**: Set up a centralized JWT Identity Provider (OAuth2 pattern) for multi-tenant backend security.
5. **Real-time Data Aggregator**: Wrote an ingestion script that normalizes chaotic WebSocket streams into a single downstream schema.

---

📫 **Contact**: firmenetto@gmail.com
🔗 **GitHub**: [@tioloff155-cmd](https://github.com/tioloff155-cmd)
