"""Minimal terminal UI shim for last30days-surf.

Upstream's ui.py was 610 lines of ANSI banners + spinners + status boxes.
The agent that invokes this skill via Bash sees stdout/stderr after the
process exits, not during — so progress animations are pure noise. We
provide the minimum API surface last30days.py uses, with quiet defaults
that emit one stderr line per state change.
"""

from __future__ import annotations

import sys
from typing import Any


class ProgressDisplay:
    def __init__(self, topic: str, show_banner: bool = False) -> None:
        self.topic = topic
        self._started = False
        if show_banner:
            print(f"[last30days-surf] researching: {topic}", file=sys.stderr)

    def start_processing(self) -> None:
        if self._started:
            return
        self._started = True
        print("[last30days-surf] starting research...", file=sys.stderr)

    def end_processing(self) -> None:
        if not self._started:
            return
        self._started = False

    def show_complete(self, *args: Any, **kwargs: Any) -> None:
        print("[last30days-surf] research complete", file=sys.stderr)

    def show_promo(self, source: str, diag: dict | None = None) -> None:
        # Quality nudge for missing sources. We surface one terse line.
        if source == "reddit":
            print(
                "[last30days-surf] tip: set SURF_API_KEY for X / YouTube / "
                "Bluesky / TikTok / Instagram / Threads / Pinterest coverage.",
                file=sys.stderr,
            )

    def show_error(self, msg: str) -> None:
        print(f"[last30days-surf] error: {msg}", file=sys.stderr)


# Compat exports for any vendored caller that does `from . import ui` and
# touches names other than ProgressDisplay. All no-ops.
def banner(topic: str = "") -> None:
    pass


def source_status(*args: Any, **kwargs: Any) -> None:
    pass
