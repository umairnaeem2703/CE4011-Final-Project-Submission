"""Tkinter desktop UI package."""

__all__ = ["DesktopMainWindow", "main"]


def __getattr__(name: str):
    if name == "DesktopMainWindow":
        from .main_window import DesktopMainWindow

        return DesktopMainWindow
    if name == "main":
        from .app import main

        return main
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
