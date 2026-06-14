"""Minimal Tkinter desktop shell for the structural analysis app."""

from __future__ import annotations

import tkinter as tk
from tkinter import ttk

from .canvas import ModelCanvas
from .property_panel import PropertyPanel
from .template_dialog import ask_new_model


TOOLBAR_ACTIONS = ("New", "Open XML", "Save XML", "Validate", "Run Analysis", "Results")
DRAWING_TOOLS = (
    "Select",
    "Draw Frame",
    "Draw Truss",
    "Support",
    "Nodal Load",
    "Member Load",
    "Mass",
    "Diaphragm",
)


class DesktopMainWindow:
    """Tkinter shell only; solver integration will be added later."""

    def __init__(self) -> None:
        self.root = tk.Tk()
        self.root.title("CE 4011 Structural Analysis")
        self.root.geometry("1200x760")
        self.root.minsize(900, 600)

        self.selected_tool = tk.StringVar(value="Select")
        self.status_message = tk.StringVar(value="Ready. Create or open a model to begin.")

        self._configure_grid()
        self._build_toolbar()
        self._build_left_tool_panel()
        self._build_model_canvas()
        self._build_property_panel()
        self._build_status_panel()

    def run(self) -> None:
        self.root.mainloop()

    def _configure_grid(self) -> None:
        self.root.columnconfigure(0, weight=0)
        self.root.columnconfigure(1, weight=1)
        self.root.columnconfigure(2, weight=0)
        self.root.rowconfigure(0, weight=0)
        self.root.rowconfigure(1, weight=1)
        self.root.rowconfigure(2, weight=0)

    def _build_toolbar(self) -> None:
        toolbar = ttk.Frame(self.root, padding=(8, 6))
        toolbar.grid(row=0, column=0, columnspan=3, sticky="ew")

        for column, label in enumerate(TOOLBAR_ACTIONS):
            button = ttk.Button(toolbar, text=label, command=lambda name=label: self._log_action(name))
            button.grid(row=0, column=column, padx=(0, 6), sticky="w")

        toolbar.columnconfigure(len(TOOLBAR_ACTIONS), weight=1)

    def _build_left_tool_panel(self) -> None:
        panel = ttk.LabelFrame(self.root, text="Tools", padding=8)
        panel.grid(row=1, column=0, sticky="nsw", padx=(8, 4), pady=4)

        for row, label in enumerate(DRAWING_TOOLS):
            button = ttk.Radiobutton(
                panel,
                text=label,
                value=label,
                variable=self.selected_tool,
                command=lambda name=label: self._select_tool(name),
            )
            button.grid(row=row, column=0, sticky="ew", pady=2)

        panel.columnconfigure(0, minsize=140)

    def _build_model_canvas(self) -> None:
        self.model_canvas = ModelCanvas(self.root, status_callback=self._write_status)
        self.model_canvas.grid(row=1, column=1, sticky="nsew", pady=4)
        self.canvas = self.model_canvas.canvas

    def _build_property_panel(self) -> None:
        self.property_panel = PropertyPanel(self.root, self.model_canvas, status_callback=self._write_status)
        self.property_panel.grid(row=1, column=2, sticky="nse", padx=(4, 8), pady=4)
        self.property_panel.columnconfigure(0, minsize=90)
        self.property_panel.columnconfigure(1, minsize=130)

    def _build_status_panel(self) -> None:
        panel = ttk.Frame(self.root, padding=(8, 4))
        panel.grid(row=2, column=0, columnspan=3, sticky="ew")
        panel.columnconfigure(0, weight=1)

        ttk.Label(panel, textvariable=self.status_message).grid(row=0, column=0, sticky="w")
        self.log = tk.Text(panel, height=5, wrap="word")
        self.log.grid(row=1, column=0, sticky="ew", pady=(4, 0))
        self.log.insert("end", "Desktop shell initialized.\n")
        self.log.configure(state="disabled")

    def _select_tool(self, name: str) -> None:
        self.model_canvas.set_active_tool(name)
        self._write_status(f"Selected tool: {name}")

    def _log_action(self, name: str) -> None:
        if name == "New":
            self._new_model()
            return
        self._write_status(f"{name} action is not wired yet.")

    def _new_model(self) -> None:
        builder = ask_new_model(self.root)
        if builder is None:
            self._write_status("New model canceled.")
            return
        self.model_canvas.load_builder(builder)
        self._write_status(f"New model created: {builder.model.name}.")

    def _write_status(self, message: str) -> None:
        self.status_message.set(message)
        self.log.configure(state="normal")
        self.log.insert("end", f"{message}\n")
        self.log.see("end")
        self.log.configure(state="disabled")
