"""Per-domain data transformation modules.

Each module reads from ``sources/``, writes to ``data/``, and is
orchestrated by ``build/pipeline.py``. See ``docs/architecture.md`` for
the transformation pipeline design.
"""

from __future__ import annotations
