"""Minimal Tkinter desktop shell for the structural analysis app."""

from __future__ import annotations

import tkinter as tk
from tkinter import ttk

from .canvas import ModelCanvas
from .object_tree import ObjectTreePanel
from .property_panel import PropertyPanel
from .template_dialog import ask_new_model


TOOLBAR_ACTIONS = ("New", "Open XML", "Save XML", "Validate", "Run Analysis", "Results")
COMMANDS = (
    "Select / Inspect",
    "Draw Node",
    "Draw Member",
    "Materials / Sections",
    "Assign Support",
    "Assign Load",
    "Assign Mass",
    "Assign Diaphragm",
    "Delete",
)


class MainWindow:
    """Tkinter shell for model-building workflows; no analysis execution."""

    def __init__(self) -> None:
        self.root = tk.Tk()
        self.root.title("CE 4011 Structural Analysis")
        self.root.geometry("1280x780")
        self.root.minsize(980, 620)

        self.selected_command = tk.StringVar(value="Select / Inspect")
        self.status_message = tk.StringVar(value="Select / Inspect: click a node or member to inspect it.")

        self._configure_grid()
        self._build_toolbar()
        self._build_left_panel()
        self._build_model_canvas()
        self._build_right_panel()
        self._build_status_panel()
        self._refresh_object_tree()

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
            ttk.Button(toolbar, text=label, command=lambda name=label: self._toolbar_action(name)).grid(
                row=0,
                column=column,
                padx=(0, 6),
                sticky="w",
            )
        toolbar.columnconfigure(len(TOOLBAR_ACTIONS), weight=1)

    def _build_left_panel(self) -> None:
        panel = ttk.Frame(self.root, padding=(8, 4))
        panel.grid(row=1, column=0, sticky="nsw")
        panel.columnconfigure(0, weight=1)

        tools = ttk.LabelFrame(panel, text="Commands", padding=8)
        tools.grid(row=0, column=0, sticky="new", pady=(0, 8))
        for row, label in enumerate(COMMANDS):
            ttk.Radiobutton(
                tools,
                text=label,
                value=label,
                variable=self.selected_command,
                command=lambda name=label: self._select_command(name),
            ).grid(row=row, column=0, sticky="ew", pady=2)
        tools.columnconfigure(0, minsize=150)

        self.object_tree = ObjectTreePanel(panel, selection_callback=self._select_from_tree)
        self.object_tree.grid(row=1, column=0, sticky="nsew")
        panel.rowconfigure(1, weight=1)

    def _build_model_canvas(self) -> None:
        self.model_canvas = ModelCanvas(
            self.root,
            status_callback=self._write_status,
            selection_callback=self._show_selection,
            change_callback=self._refresh_object_tree,
        )
        self.model_canvas.grid(row=1, column=1, sticky="nsew", pady=4)
        self.canvas = self.model_canvas.canvas

    def _build_right_panel(self) -> None:
        self.property_panel = PropertyPanel(self.root, self.model_canvas, status_callback=self._write_status)
        self.property_panel.grid(row=1, column=2, sticky="nse", padx=(4, 8), pady=4)
        self.property_panel.columnconfigure(0, minsize=240)

    def _build_status_panel(self) -> None:
        panel = ttk.Frame(self.root, padding=(8, 4))
        panel.grid(row=2, column=0, columnspan=3, sticky="ew")
        panel.columnconfigure(0, weight=1)
        ttk.Label(panel, textvariable=self.status_message).grid(row=0, column=0, sticky="w")
        self.log = tk.Text(panel, height=4, wrap="word")
        self.log.grid(row=1, column=0, sticky="ew", pady=(4, 0))
        self.log.insert("end", "Desktop model builder ready.\n")
        self.log.configure(state="disabled")

    def _select_command(self, name: str) -> None:
        self.model_canvas.set_active_command(name)
        self.property_panel.show_command(name)
        self._write_status(self.model_canvas.command_instruction())

    def _toolbar_action(self, name: str) -> None:
        if name == "New":
            self._new_model()
            return
        self._write_status(f"{name}: not wired yet.")

    def _new_model(self) -> None:
        builder = ask_new_model(self.root)
        if builder is None:
            self._write_status("New model canceled.")
            return
        self.model_canvas.load_builder(builder)
        self.property_panel.sync_from_canvas()
        self.property_panel.show_command(self.selected_command.get())
        self._refresh_object_tree()
        self._write_status(f"New model created: {builder.model.name}.")
        for message in getattr(builder, "creation_messages", []):
            self._write_status(message)

    def _show_selection(self, kind: str | None, obj: object | None) -> None:
        self.property_panel.show_selection(kind, obj)

    def _select_from_tree(self, kind: str, object_id: str) -> None:
        if kind == "node":
            self.model_canvas.select_node(int(object_id))
            self._write_status(f"Selected node {object_id} from object tree.")
        elif kind == "element":
            self.model_canvas.select_element(object_id)
            self._write_status(f"Selected member {object_id} from object tree.")
        elif kind == "support":
            self.model_canvas.select_node(int(object_id))
            self._write_status(f"Selected support at node {object_id} from object tree.")
        elif kind == "mass":
            self.model_canvas.select_node(int(object_id))
            self._write_status(f"Selected mass at node {object_id} from object tree.")
        else:
            self._write_status(f"Selected {kind} {object_id}. Canvas highlighting is pending for this object type.")

    def _refresh_object_tree(self) -> None:
        if hasattr(self, "object_tree") and hasattr(self, "model_canvas"):
            self.object_tree.refresh(self.model_canvas.builder.model)

    def _write_status(self, message: str) -> None:
        self.status_message.set(message)
        self.log.configure(state="normal")
        if not message.endswith("."):
            message = f"{message}."
        self.log.insert("end", f"{message}\n")
        lines = self.log.get("1.0", "end-1c").splitlines()
        if len(lines) > 12:
            self.log.delete("1.0", f"{len(lines) - 11}.0")
        self.log.see("end")
        self.log.configure(state="disabled")


DesktopMainWindow = MainWindow
