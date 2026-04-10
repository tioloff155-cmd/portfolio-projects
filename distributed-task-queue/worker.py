"""
Distributed Task Queue
A lightweight producer-consumer task queue with worker pool,
retry logic, and dead-letter tracking.
"""

import time
import uuid
import threading
import queue
from enum import Enum
from dataclasses import dataclass, field
from typing import Callable, Any, Optional


class TaskState(Enum):
    PENDING = "PENDING"
    RUNNING = "RUNNING"
    SUCCESS = "SUCCESS"
    FAILED = "FAILED"
    DEAD = "DEAD"


@dataclass
class Task:
    func: Callable
    args: tuple = ()
    kwargs: dict = field(default_factory=dict)
    task_id: str = field(default_factory=lambda: uuid.uuid4().hex[:10])
    max_retries: int = 3
    attempts: int = 0
    state: TaskState = TaskState.PENDING
    result: Any = None
    error: Optional[str] = None
    created_at: float = field(default_factory=time.time)
    finished_at: Optional[float] = None


class TaskQueue:
    """
    In-memory task queue with configurable worker threads.
    Supports retry with exponential backoff and a dead-letter queue.
    """

    def __init__(self, workers: int = 4):
        self._queue: queue.Queue = queue.Queue()
        self._results: dict[str, Task] = {}
        self._dead_letter: list[Task] = []
        self._workers: list[threading.Thread] = []
        self._running = False
        self._lock = threading.Lock()
        self._worker_count = workers

    def start(self):
        """Spawn worker threads and begin consuming tasks."""
        self._running = True
        for i in range(self._worker_count):
            t = threading.Thread(target=self._worker_loop, name=f"Worker-{i}", daemon=True)
            t.start()
            self._workers.append(t)

    def stop(self):
        """Signal all workers to shut down gracefully."""
        self._running = False
        for _ in self._workers:
            self._queue.put(None)  # poison pill
        for t in self._workers:
            t.join(timeout=5)
        self._workers.clear()

    def enqueue(self, func: Callable, *args, max_retries: int = 3, **kwargs) -> str:
        """Submit a task. Returns the task ID for tracking."""
        task = Task(func=func, args=args, kwargs=kwargs, max_retries=max_retries)
        with self._lock:
            self._results[task.task_id] = task
        self._queue.put(task)
        return task.task_id

    def get_result(self, task_id: str) -> Optional[Task]:
        """Retrieve the current state and result of a task."""
        return self._results.get(task_id)

    def _worker_loop(self):
        while self._running:
            try:
                task = self._queue.get(timeout=1)
            except queue.Empty:
                continue

            if task is None:
                break

            self._execute(task)

    def _execute(self, task: Task):
        task.state = TaskState.RUNNING
        task.attempts += 1

        try:
            result = task.func(*task.args, **task.kwargs)
            task.result = result
            task.state = TaskState.SUCCESS
            task.finished_at = time.time()
        except Exception as e:
            task.error = str(e)
            if task.attempts < task.max_retries:
                backoff = 0.1 * (2 ** task.attempts)
                time.sleep(backoff)
                task.state = TaskState.PENDING
                self._queue.put(task)
            else:
                task.state = TaskState.DEAD
                task.finished_at = time.time()
                with self._lock:
                    self._dead_letter.append(task)

    @property
    def pending_count(self) -> int:
        return self._queue.qsize()

    @property
    def dead_letter_count(self) -> int:
        return len(self._dead_letter)

    def summary(self) -> dict:
        with self._lock:
            states = {}
            for t in self._results.values():
                states[t.state.value] = states.get(t.state.value, 0) + 1
        return {
            "total_submitted": len(self._results),
            "in_queue": self.pending_count,
            "dead_letters": self.dead_letter_count,
            "by_state": states,
        }


# --- Demo tasks ---

def compute_heavy(n: int) -> int:
    """Simulate a CPU-bound computation."""
    total = 0
    for i in range(n):
        total += i * i
    return total


def flaky_task(fail_until: int, attempt_tracker: list) -> str:
    """A task that fails N times before succeeding."""
    attempt_tracker.append(1)
    if len(attempt_tracker) < fail_until:
        raise RuntimeError(f"Simulated failure #{len(attempt_tracker)}")
    return "finally succeeded"


if __name__ == "__main__":
    tq = TaskQueue(workers=3)
    tq.start()

    # Submit compute tasks
    ids = []
    for val in [100_000, 200_000, 500_000, 1_000_000]:
        tid = tq.enqueue(compute_heavy, val)
        ids.append(tid)
        print(f"Submitted compute({val}) -> {tid}")

    # Submit a flaky task that will retry
    tracker = []
    flaky_id = tq.enqueue(flaky_task, 3, tracker, max_retries=5)
    print(f"Submitted flaky task -> {flaky_id}")

    # Wait for completion
    time.sleep(3)

    for tid in ids:
        r = tq.get_result(tid)
        print(f"  {tid}: {r.state.value} | result={r.result}")

    r = tq.get_result(flaky_id)
    print(f"  {flaky_id}: {r.state.value} | result={r.result} | attempts={r.attempts}")

    print(f"\nQueue summary: {tq.summary()}")
    tq.stop()
