"""Launch entry point for the Tkinter desktop shell."""

from __future__ import annotations


def main() -> None:
    """Create and run the desktop shell."""
    from .main_window import DesktopMainWindow

    app = DesktopMainWindow()
    app.run()


if __name__ == "__main__":
    main()
