"""
SQL Audit Engine
A middleware profiler that intercepts database queries, logs execution
time, detects slow queries, and suggests indexing improvements.
"""

import sqlite3
import time
import os
from dataclasses import dataclass, field
from typing import Optional
from collections import defaultdict


@dataclass
class QueryLog:
    query: str
    params: tuple
    execution_time_ms: float
    rows_affected: int
    timestamp: float = field(default_factory=time.time)
    is_slow: bool = False
    explain_plan: Optional[str] = None


class AuditEngine:
    """
    Wraps a SQLite connection and intercepts all queries to:
    1. Log execution time
    2. Flag slow queries above threshold
    3. Run EXPLAIN QUERY PLAN on flagged queries
    4. Track query frequency for indexing suggestions
    """

    SLOW_THRESHOLD_MS = 50.0

    def __init__(self, db_path: str = ":memory:"):
        self.db_path = db_path
        self._conn = sqlite3.connect(db_path, check_same_thread=False)
        self._conn.execute("PRAGMA journal_mode=WAL")
        self._conn.execute("PRAGMA synchronous=NORMAL")
        self._logs: list[QueryLog] = []
        self._query_freq: dict[str, int] = defaultdict(int)
        self._slow_queries: list[QueryLog] = []

    def execute(self, query: str, params: tuple = ()) -> list:
        """Execute a query through the audit layer."""
        normalized = self._normalize(query)
        self._query_freq[normalized] += 1

        start = time.perf_counter()
        cursor = self._conn.execute(query, params)
        rows = cursor.fetchall()
        elapsed = (time.perf_counter() - start) * 1000

        log = QueryLog(
            query=query,
            params=params,
            execution_time_ms=round(elapsed, 3),
            rows_affected=len(rows),
        )

        if elapsed > self.SLOW_THRESHOLD_MS:
            log.is_slow = True
            log.explain_plan = self._explain(query, params)
            self._slow_queries.append(log)

        self._logs.append(log)
        return rows

    def execute_write(self, query: str, params: tuple = ()) -> int:
        """Execute a write query (INSERT/UPDATE/DELETE) through the audit layer."""
        start = time.perf_counter()
        cursor = self._conn.execute(query, params)
        self._conn.commit()
        elapsed = (time.perf_counter() - start) * 1000

        log = QueryLog(
            query=query,
            params=params,
            execution_time_ms=round(elapsed, 3),
            rows_affected=cursor.rowcount,
        )

        normalized = self._normalize(query)
        self._query_freq[normalized] += 1

        if elapsed > self.SLOW_THRESHOLD_MS:
            log.is_slow = True
            self._slow_queries.append(log)

        self._logs.append(log)
        return cursor.rowcount

    def _explain(self, query: str, params: tuple) -> str:
        try:
            cursor = self._conn.execute(f"EXPLAIN QUERY PLAN {query}", params)
            rows = cursor.fetchall()
            return " | ".join(str(r) for r in rows)
        except Exception as e:
            return f"EXPLAIN failed: {e}"

    def _normalize(self, query: str) -> str:
        """Strip specific values to create a query fingerprint."""
        import re
        q = " ".join(query.split()).upper()
        q = re.sub(r"'[^']*'", "?", q)
        q = re.sub(r"\b\d+\b", "?", q)
        return q

    def suggest_indexes(self) -> list[str]:
        """Analyze slow queries and suggest indexes based on WHERE clauses."""
        suggestions = []
        import re
        for log in self._slow_queries:
            tables = re.findall(r"FROM\s+(\w+)", log.query, re.IGNORECASE)
            where_cols = re.findall(r"WHERE\s+.*?(\w+)\s*[=<>]", log.query, re.IGNORECASE)
            order_cols = re.findall(r"ORDER\s+BY\s+(\w+)", log.query, re.IGNORECASE)

            target_cols = set(where_cols + order_cols)
            for table in tables:
                for col in target_cols:
                    idx = f"CREATE INDEX IF NOT EXISTS idx_{table}_{col} ON {table}({col});"
                    if idx not in suggestions:
                        suggestions.append(idx)
        return suggestions

    def top_queries(self, n: int = 10) -> list[tuple[str, int]]:
        """Return the N most frequently executed query patterns."""
        sorted_q = sorted(self._query_freq.items(), key=lambda x: x[1], reverse=True)
        return sorted_q[:n]

    def report(self) -> dict:
        total = len(self._logs)
        avg_time = sum(l.execution_time_ms for l in self._logs) / total if total else 0
        return {
            "total_queries": total,
            "slow_queries": len(self._slow_queries),
            "avg_execution_ms": round(avg_time, 3),
            "unique_patterns": len(self._query_freq),
            "suggested_indexes": self.suggest_indexes(),
        }

    def close(self):
        self._conn.close()


if __name__ == "__main__":
    engine = AuditEngine()

    # Setup: create a test table with 10k rows
    engine.execute_write("""
        CREATE TABLE IF NOT EXISTS transactions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id TEXT NOT NULL,
            amount REAL NOT NULL,
            currency TEXT DEFAULT 'USD',
            status TEXT DEFAULT 'pending',
            created_at REAL NOT NULL
        )
    """)

    import random
    users = [f"user_{i:03d}" for i in range(50)]
    statuses = ["pending", "confirmed", "failed", "refunded"]

    print("Inserting 10,000 rows...")
    for i in range(10000):
        engine.execute_write(
            "INSERT INTO transactions (user_id, amount, currency, status, created_at) VALUES (?, ?, ?, ?, ?)",
            (random.choice(users), round(random.uniform(1, 500), 2), "USD",
             random.choice(statuses), time.time() - random.uniform(0, 86400 * 30))
        )

    # Run various queries
    print("\nRunning queries through audit layer...")

    engine.execute("SELECT * FROM transactions WHERE user_id = ? AND status = ?", ("user_007", "confirmed"))
    engine.execute("SELECT user_id, SUM(amount) FROM transactions GROUP BY user_id ORDER BY SUM(amount) DESC")
    engine.execute("SELECT * FROM transactions WHERE amount > ? ORDER BY created_at DESC", (200,))
    engine.execute("SELECT COUNT(*) FROM transactions WHERE status = ?", ("failed",))

    # Run same pattern multiple times
    for u in users[:10]:
        engine.execute("SELECT * FROM transactions WHERE user_id = ?", (u,))

    # Report
    report = engine.report()
    print(f"\nAudit Report:")
    for k, v in report.items():
        print(f"  {k}: {v}")

    print(f"\nTop query patterns:")
    for pattern, count in engine.top_queries(5):
        print(f"  [{count}x] {pattern[:80]}...")

    engine.close()
