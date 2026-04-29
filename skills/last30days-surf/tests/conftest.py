"""Pytest config for last30days-surf tests.

Vendored upstream tests use `sys.path.insert(0, "skills/last30days/scripts")`
to find their `lib` module. Our skill location is different — this conftest
prepends the right path before any test imports run.
"""

from __future__ import annotations

import sys
from pathlib import Path

SCRIPTS_DIR = Path(__file__).resolve().parents[1] / "scripts"
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))
