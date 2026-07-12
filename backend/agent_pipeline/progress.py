"""Progress tracker for the Mizan agent pipeline.

Provides an in-memory store that the pipeline nodes write to and the
SSE endpoint reads from.  Each report_id gets its own progress buffer
that tracks which agent nodes have completed.

Thread-safe via a per-report Lock.
"""

from __future__ import annotations

import json
import threading
import time
from collections import OrderedDict
from typing import Any


class ProgressTracker:
    """In-memory progress tracking for pipeline runs.

    Each report_id maps to an ordered dict of agent_steps, where each
    step tracks the agent name, status (pending/running/done/error),
    and a short summary of the output.

    Entries expire after ``TTL`` seconds since the last write to avoid
    unbounded memory growth.
    """

    TTL = 600  # 10 minutes — plenty for pipeline monitoring

    def __init__(self):
        self._lock = threading.Lock()
        # report_id -> (last_write_timestamp, OrderedDict of steps)
        self._store: dict[int, tuple[float, OrderedDict[str, Any]]] = {}

    # ── Write API (called from pipeline nodes) ─────────────────────────

    def agent_started(self, report_id: int, agent_name: str) -> None:
        """Mark an agent node as started."""
        with self._lock:
            self._evict_locked()
            ts, steps = self._store.get(report_id, (time.time(), OrderedDict()))
            if agent_name not in steps:
                steps[agent_name] = {
                    "agent": agent_name,
                    "status": "running",
                    "started_at": time.time(),
                    "summary": "",
                }
                self._store[report_id] = (time.time(), steps)

    def agent_completed(
        self, report_id: int, agent_name: str, summary: str = ""
    ) -> None:
        """Mark an agent node as completed with an optional summary."""
        with self._lock:
            self._evict_locked()
            ts, steps = self._store.get(report_id, (time.time(), OrderedDict()))
            steps[agent_name] = {
                "agent": agent_name,
                "status": "done",
                "started_at": steps.get(agent_name, {}).get("started_at", time.time()),
                "completed_at": time.time(),
                "summary": summary[:200] if summary else "",
            }
            self._store[report_id] = (time.time(), steps)

    def agent_error(
        self, report_id: int, agent_name: str, error: str = ""
    ) -> None:
        """Mark an agent node as errored."""
        with self._lock:
            self._evict_locked()
            ts, steps = self._store.get(report_id, (time.time(), OrderedDict()))
            steps[agent_name] = {
                "agent": agent_name,
                "status": "error",
                "started_at": steps.get(agent_name, {}).get("started_at", time.time()),
                "completed_at": time.time(),
                "summary": f"Error: {error[:200]}" if error else "Error",
            }
            self._store[report_id] = (time.time(), steps)

    def all_completed(self, report_id: int) -> None:
        """Mark the entire pipeline as complete."""
        with self._lock:
            self._evict_locked()
            ts, steps = self._store.get(report_id, (time.time(), OrderedDict()))
            steps["__pipeline__"] = {
                "agent": "__pipeline__",
                "status": "done",
                "completed_at": time.time(),
                "summary": "Research report generated.",
            }
            self._store[report_id] = (time.time(), steps)

    # ── Read API (called from SSE endpoint) ────────────────────────────

    def get_progress(self, report_id: int) -> list[dict[str, Any]]:
        """Return the ordered list of agent steps for a report.

        Returns an empty list if the report_id is unknown.
        """
        with self._lock:
            self._evict_locked()
            ts, steps = self._store.get(report_id, (0, OrderedDict()))
            return list(steps.values())

    def has_report(self, report_id: int) -> bool:
        """Return True if we have any progress for this report_id."""
        with self._lock:
            self._evict_locked()
            return report_id in self._store

    def is_complete(self, report_id: int) -> bool:
        """Return True if the pipeline has completed for this report."""
        with self._lock:
            self._evict_locked()
            ts, steps = self._store.get(report_id, (0, OrderedDict()))
            pipeline_step = steps.get("__pipeline__", {})
            return pipeline_step.get("status") == "done"

    # ── Internal ──────────────────────────────────────────────────────

    def _evict_locked(self) -> None:
        """Remove expired entries (caller must hold _lock)."""
        now = time.time()
        stale = [
            rid
            for rid, (last_ts, _) in self._store.items()
            if now - last_ts > self.TTL
        ]
        for rid in stale:
            del self._store[rid]


# ── Singleton ──────────────────────────────────────────────────────────────

_tracker: ProgressTracker | None = None


def get_tracker() -> ProgressTracker:
    """Return the singleton ProgressTracker instance."""
    global _tracker
    if _tracker is None:
        _tracker = ProgressTracker()
    return _tracker
