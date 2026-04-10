# Neto Loff | Software & Backend Engineering

![Python](https://img.shields.io/badge/Python-3776AB?style=for-the-badge&logo=python&logoColor=white)
![Flask](https://img.shields.io/badge/flask-%23000.svg?style=for-the-badge&logo=flask&logoColor=white)
![SQLite](https://img.shields.io/badge/sqlite-%2307405e.svg?style=for-the-badge&logo=sqlite&logoColor=white)
![JavaScript](https://img.shields.io/badge/javascript-%23323330.svg?style=for-the-badge&logo=javascript&logoColor=%23F7DF1E)
![Docker](https://img.shields.io/badge/docker-%230db7ed.svg?style=for-the-badge&logo=docker&logoColor=white)

Architecting resilient backend systems, low-latency execution engines, and data pipelines. Focused on delivering production-ready computational solutions with strict risk management, concurrency, and performance optimization.

---

## 🏗️ Architectural Standards

All projects within this repository adhere to institutional-grade software principles:
- **Resiliency**: Built-in circuit breakers, custom exception handling, and persistent state management.
- **Latency Optimization**: Minimal dependency overhead, optimized SQL queries (WAL mode), and efficient WebSocket stream processing.
- **Security**: Environment-based configuration, strict input validation, and secure API routing.
- **Maintainability**: Clean code architecture (MVC/Modular), unified logging, and comprehensive documentation.

---

## 🚀 Flagship Engine

### [HFT Trading Engine](./hft-trading-engine)
An institutional-grade algorithmic trading engine designed for digital options execution. Built to continuously process concurrent WebSocket streams and manage real-time financial exposure.
- **System Architecture**: Multi-threaded Python architecture with non-blocking I/O telemetry via Flask-SocketIO.
- **Quantitative Risk Management**: Dynamic position sizing mathematically enforced by the **Kelly Criterion**, with a hard-coded Daily Peak/Drawdown Kill Switch.
- **Persistence**: High-throughput SQLite implementation using `WAL` (Write-Ahead Logging) mode to guarantee ACID compliance during concurrent order executions.

---

## 🛠️ Software Engineering Capabilities

### [ETL Data Pipeline Engine](./etl-pipeline-engine)
Data automation system designed for reliable extraction, transformation, and loading (ETL) routines.
- **Mechanics**: Implemented robust functional pipelines leveraging `Pandas` for scalable matrix transformations.
- **Core Value**: Enterprise-scale CSV/Excel ingestion with schema validation and error-resilient transformation logic.

### [Recruitment Data Management API](./recruit-data-api)
A modular Web Application built on a custom MVC structure for tracking lifecycle events.
- **Mechanics**: RESTful logic wrapping a local persistence layer, coupled with a decoupled frontend using Vanilla JS.
- **Focus**: Clean separation of concerns, secure routing, and highly-maintainable CRUD API design.

### [Stateless Edge Application](./edge-portfolio-app)
Minimalist, high-performance web deployment optimized for Sub-50ms Time-To-First-Byte (TTFB).
- **Mechanics**: Zero-bloat Flask architecture utilizing server-side rendering and pure CSS Grid layouts.
- **Focus**: Accessibility, SEO readiness, and lightweight edge delivery capabilities.

---

## ⚙️ Core Technical Proficiencies

*   **Backend Engineering**: Python, REST APIs, WebSocket/SocketIO, Flask, Component Architecture.
*   **Data & Quantitative Models**: Pandas, NumPy, Time-Series Analysis, Technical Indicators (EMA/RSI), Kelly Sizing.
*   **Systems & Operations**: Concurrent Threading, SQLite (WAL optimization), Git, Environment Management.

## Contact & Professional Network

📫 **Get in touch**: firmenetto@gmail.com
🔗 **GitHub Profile**: [@tioloff155-cmd](https://github.com/tioloff155-cmd)
