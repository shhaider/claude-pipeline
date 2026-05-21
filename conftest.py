"""Root conftest.

Ensures `src/` is importable for pytest without requiring an editable install
or a PYTHONPATH env var. Lets reviewers rerun `pytest -v` from a clean clone.
"""

from __future__ import annotations

import sys
from pathlib import Path

_SRC = Path(__file__).resolve().parent / "src"
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))
