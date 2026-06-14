"""Property and geometry input panel for the desktop shell."""

from __future__ import annotations

import tkinter as tk
from tkinter import ttk

from .canvas import ModelCanvas


class PropertyPanel(ttk.LabelFrame):
    """Small input panel for creating basic canvas geometry."""

    def __init__(self, parent, model_canvas: ModelCanvas, *, status_callback=None) -> None:
        super().__init__(parent, text="Properties / Settings", padding=8)
        self.model_canvas = model_canvas
        self.status_callback = status_callback or (lambda message: None)

        self.x_var = tk.StringVar(value="0.0")
        self.y_var = tk.StringVar(value="0.0")
        self.length_var = tk.StringVar(value="1.0")
        self.angle_var = tk.StringVar(value="0.0")
        self.element_type_var = tk.StringVar(value="frame")
        self.material_var = tk.StringVar(value="M1")
        self.section_var = tk.StringVar(value="S1")

        self._build()

    def _build(self) -> None:
        self.columnconfigure(1, weight=1)

        ttk.Label(self, text="Node x").grid(row=0, column=0, sticky="w", pady=2)
        ttk.Entry(self, textvariable=self.x_var, width=12).grid(row=0, column=1, sticky="ew", pady=2)
        ttk.Label(self, text="Node y").grid(row=1, column=0, sticky="w", pady=2)
        ttk.Entry(self, textvariable=self.y_var, width=12).grid(row=1, column=1, sticky="ew", pady=2)
        ttk.Button(self, text="Add Node", command=self._add_node).grid(row=2, column=0, columnspan=2, sticky="ew", pady=(4, 10))

        ttk.Separator(self).grid(row=3, column=0, columnspan=2, sticky="ew", pady=6)

        ttk.Label(self, text="Element").grid(row=4, column=0, sticky="w", pady=2)
        element_box = ttk.Combobox(
            self,
            textvariable=self.element_type_var,
            values=("frame", "truss"),
            state="readonly",
            width=10,
        )
        element_box.grid(row=4, column=1, sticky="ew", pady=2)
        element_box.bind("<<ComboboxSelected>>", lambda event: self._set_element_type())

        ttk.Label(self, text="Material").grid(row=5, column=0, sticky="w", pady=2)
        material_box = ttk.Combobox(
            self,
            textvariable=self.material_var,
            values=("M1",),
            state="readonly",
            width=10,
        )
        material_box.grid(row=5, column=1, sticky="ew", pady=2)
        material_box.bind("<<ComboboxSelected>>", lambda event: self.model_canvas.set_active_material(self.material_var.get()))

        ttk.Label(self, text="Section").grid(row=6, column=0, sticky="w", pady=2)
        section_box = ttk.Combobox(
            self,
            textvariable=self.section_var,
            values=("S1",),
            state="readonly",
            width=10,
        )
        section_box.grid(row=6, column=1, sticky="ew", pady=2)
        section_box.bind("<<ComboboxSelected>>", lambda event: self.model_canvas.set_active_section(self.section_var.get()))

        ttk.Label(self, text="Length").grid(row=7, column=0, sticky="w", pady=(10, 2))
        ttk.Entry(self, textvariable=self.length_var, width=12).grid(row=7, column=1, sticky="ew", pady=(10, 2))
        ttk.Label(self, text="Angle").grid(row=8, column=0, sticky="w", pady=2)
        ttk.Entry(self, textvariable=self.angle_var, width=12).grid(row=8, column=1, sticky="ew", pady=2)
        ttk.Button(self, text="Draw Member", command=self._draw_member).grid(
            row=9,
            column=0,
            columnspan=2,
            sticky="ew",
            pady=(4, 10),
        )

        ttk.Label(self, text="Click canvas to add/snap nodes and draw members.", wraplength=220).grid(
            row=10,
            column=0,
            columnspan=2,
            sticky="nw",
            pady=(8, 0),
        )

    def _add_node(self) -> None:
        try:
            x = float(self.x_var.get())
            y = float(self.y_var.get())
        except ValueError:
            self.status_callback("Enter numeric x and y values.")
            return

        self.model_canvas.add_node_by_coordinates(x, y)

    def _draw_member(self) -> None:
        try:
            length = float(self.length_var.get())
            angle = float(self.angle_var.get())
        except ValueError:
            self.status_callback("Enter numeric length and angle values.")
            return

        if length <= 0:
            self.status_callback("Member length must be positive.")
            return

        self._set_element_type()
        self.model_canvas.draw_member_by_length_angle(length, angle)

    def _set_element_type(self) -> None:
        element_type = self.element_type_var.get()
        self.model_canvas.set_active_element_type(element_type)
        self.status_callback(f"Active element type: {element_type}.")
