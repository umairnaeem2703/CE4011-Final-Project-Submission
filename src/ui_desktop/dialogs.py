"""Small dialog/data helpers for desktop assignment tools."""

from __future__ import annotations

from dataclasses import dataclass
import tkinter as tk
from tkinter import ttk


@dataclass
class SupportSettings:
    support_type: str = "fixed"
    restrain_ux: bool = True
    restrain_uy: bool = True
    restrain_rz: bool = True
    settlement_ux: float = 0.0
    settlement_uy: float = 0.0
    settlement_rz: float = 0.0


@dataclass
class LoadSettings:
    target: str = "Node"
    load_type: str = "Nodal Force/Moment"
    load_case: str = "LC1"
    fx: float = 0.0
    fy: float = 0.0
    mz: float = 0.0
    wx: float = 0.0
    wy: float = 0.0
    position: float = 0.5


class SupportDialog(tk.Toplevel):
    """Placeholder modal for future support editing flows."""

    def __init__(self, parent, settings: SupportSettings | None = None) -> None:
        super().__init__(parent)
        self.title("Support Settings")
        self.resizable(False, False)
        self.result = settings or SupportSettings()
        ttk.Label(self, text="Support settings are edited in the property panel.").grid(
            row=0,
            column=0,
            padx=12,
            pady=12,
        )
