"""Compatibility: ``python -m signalbench`` forwards to :mod:`azimuth_bench`."""

from __future__ import annotations

from azimuth_bench.__main__ import main

if __name__ == "__main__":
    raise SystemExit(main())
