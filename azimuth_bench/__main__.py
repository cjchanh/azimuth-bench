"""Allow ``python -m azimuth_bench`` to run the ``azbench`` CLI."""

from __future__ import annotations

from azimuth_bench.cli.entrypoint import main

if __name__ == "__main__":
    raise SystemExit(main())
