"""Append-only markdown decision log for the Mizan agent pipeline.

Ported and adapted from TradingAgents' TradingMemoryLog. Key change: works
with Mizan's config module instead of the TradingAgents config dict.

The memory log:
- Stores each pipeline run's decision + outcome (pending → resolved)
- Before each new run, loads relevant past context (same-ticker + cross-ticker)
- Feeds "lessons learned" into the Portfolio Manager prompt
- Uses atomic writes (temp file + os.replace) to prevent corruption

Stored as a markdown file (not DB) for simplicity and append-only safety.
"""

from __future__ import annotations

import logging
import os
import re
from pathlib import Path

logger = logging.getLogger(__name__)

_SEPARATOR = "\n\n<!-- ENTRY_END -->\n\n"
_DECISION_RE = re.compile(r"DECISION:\n(.*?)(?=\nREFLECTION:|\Z)", re.DOTALL)
_REFLECTION_RE = re.compile(r"REFLECTION:\n(.*?)$", re.DOTALL)


class MizanMemoryLog:
    """Append-only markdown log of Mizan agent decisions and reflections."""

    def __init__(self, log_path: str | None = None, max_entries: int | None = None):
        self._log_path: Path | None = None
        if log_path:
            self._log_path = Path(log_path).expanduser()
            self._log_path.parent.mkdir(parents=True, exist_ok=True)
        self._max_entries = max_entries

    # ── Write path ──────────────────────────────────────────────────────

    def store_decision(
        self,
        ticker: str,
        trade_date: str,
        final_trade_decision: str,
        rating: str = "",
    ) -> None:
        """Append a pending entry. Called after each pipeline run."""
        if not self._log_path:
            return

        # Idempotency guard
        if self._log_path.exists():
            raw = self._log_path.read_text(encoding="utf-8")
            for line in raw.splitlines():
                if line.startswith(f"[{trade_date} | {ticker} |") and line.endswith("| pending]"):
                    return

        tag = f"[{trade_date} | {ticker} | {rating} | pending]"
        entry = f"{tag}\n\nDECISION:\n{final_trade_decision}{_SEPARATOR}"
        with open(self._log_path, "a", encoding="utf-8") as f:
            f.write(entry)

    # ── Read path ───────────────────────────────────────────────────────

    def load_entries(self) -> list[dict]:
        """Parse all entries from the log."""
        if not self._log_path or not self._log_path.exists():
            return []

        text = self._log_path.read_text(encoding="utf-8")
        raw_entries = [e.strip() for e in text.split(_SEPARATOR) if e.strip()]
        entries = []
        for raw in raw_entries:
            parsed = self._parse_entry(raw)
            if parsed:
                entries.append(parsed)
        return entries

    def get_past_context(self, ticker: str, n_same: int = 5, n_cross: int = 3) -> str:
        """Return formatted past context for prompt injection."""
        entries = [e for e in self.load_entries() if not e.get("pending")]
        if not entries:
            return ""

        same, cross = [], []
        for e in reversed(entries):
            if len(same) >= n_same and len(cross) >= n_cross:
                break
            if e["ticker"] == ticker and len(same) < n_same:
                same.append(e)
            elif e["ticker"] != ticker and len(cross) < n_cross:
                cross.append(e)

        if not same and not cross:
            return ""

        parts = []
        if same:
            parts.append(f"Past analyses of {ticker} (most recent first):")
            for e in same:
                parts.append(self._format_entry(e))
        if cross:
            parts.append("Recent cross-ticker lessons:")
            for e in cross:
                parts.append(self._format_reflection(e))
        return "\n\n".join(parts)

    # ── Update path (outcome resolution) ────────────────────────────────

    def update_with_outcome(
        self,
        ticker: str,
        trade_date: str,
        raw_return: float,
        alpha_return: float,
        holding_days: int,
        reflection: str,
    ) -> None:
        """Replace pending tag and append REFLECTION section via atomic write."""
        if not self._log_path or not self._log_path.exists():
            return

        text = self._log_path.read_text(encoding="utf-8")
        blocks = text.split(_SEPARATOR)

        pending_prefix = f"[{trade_date} | {ticker} |"
        raw_pct = f"{raw_return:+.1%}"
        alpha_pct = f"{alpha_return:+.1%}"

        updated = False
        new_blocks = []
        for block in blocks:
            stripped = block.strip()
            if not stripped:
                new_blocks.append(block)
                continue

            lines = stripped.splitlines()
            tag_line = lines[0].strip()

            if (
                not updated
                and tag_line.startswith(pending_prefix)
                and tag_line.endswith("| pending]")
            ):
                fields = [f.strip() for f in tag_line[1:-1].split("|")]
                rating = fields[2] if len(fields) > 2 else ""
                new_tag = (
                    f"[{trade_date} | {ticker} | {rating}"
                    f" | {raw_pct} | {alpha_pct} | {holding_days}d]"
                )
                rest = "\n".join(lines[1:])
                new_blocks.append(
                    f"{new_tag}\n\n{rest.lstrip()}\n\nREFLECTION:\n{reflection}"
                )
                updated = True
            else:
                new_blocks.append(block)

        if not updated:
            return

        new_text = _SEPARATOR.join(new_blocks)
        tmp_path = self._log_path.with_suffix(".tmp")
        tmp_path.write_text(new_text, encoding="utf-8")
        tmp_path.replace(self._log_path)

    # ── Internal helpers ────────────────────────────────────────────────

    def _parse_entry(self, raw: str) -> dict | None:
        """Parse a raw entry block into a dict."""
        lines = raw.splitlines()
        if not lines:
            return None

        tag_line = lines[0].strip()
        if not (tag_line.startswith("[") and "]" in tag_line):
            return None

        # Parse tag: [date | ticker | rating | pending] or [date | ticker | rating | ret% | alpha% | days]
        fields = [f.strip() for f in tag_line[1:].split("|")]
        # Remove trailing "]"
        fields[-1] = fields[-1].rstrip("]").strip()

        if len(fields) < 3:
            return None

        entry = {
            "trade_date": fields[0],
            "ticker": fields[1],
            "rating": fields[2],
            "pending": len(fields) <= 4 and fields[-1] == "pending",
        }
        if len(fields) > 4:
            entry["raw_return"] = fields[3] if len(fields) > 3 else ""
            entry["alpha_return"] = fields[4] if len(fields) > 4 else ""
            entry["holding_days"] = fields[5] if len(fields) > 5 else ""

        body = "\n".join(lines[1:]).strip()
        dec_match = _DECISION_RE.search(body)
        if dec_match:
            entry["decision"] = dec_match.group(1).strip()
        ref_match = _REFLECTION_RE.search(body)
        if ref_match:
            entry["reflection"] = ref_match.group(1).strip()

        return entry

    def _format_entry(self, entry: dict) -> str:
        parts = [f"- [{entry['trade_date']}] Rating: {entry['rating']}"]
        if entry.get("raw_return"):
            parts.append(f"  Return: {entry['raw_return']}, Alpha: {entry.get('alpha_return', 'N/A')}")
        if entry.get("reflection"):
            parts.append(f"  Lesson: {entry['reflection'][:200]}")
        return "\n".join(parts)

    def _format_reflection(self, entry: dict) -> str:
        parts = [f"- [{entry['trade_date']}] {entry['ticker']} ({entry['rating']})"]
        if entry.get("reflection"):
            parts.append(f"  Lesson: {entry['reflection'][:200]}")
        return "\n".join(parts)
