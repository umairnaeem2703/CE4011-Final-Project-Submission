"""Launch entry point for the Tkinter desktop shell."""

from __future__ import annotations

import sys
from pathlib import Path


def _ensure_src_import_path() -> None:
    src_root = str(Path(__file__).resolve().parents[1])
    if src_root not in sys.path:
        sys.path.insert(0, src_root)


def main() -> None:
    """Create and run the desktop shell."""
    _ensure_src_import_path()
    from .main_window import DesktopMainWindow

    app = DesktopMainWindow()
    app.run()


if __name__ == "__main__":
    main()
