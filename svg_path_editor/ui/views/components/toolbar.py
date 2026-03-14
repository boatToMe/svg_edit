import tkinter as tk
from tkinter import ttk

from .flow import FlowRow


class EditorToolbar:
    def __init__(self, parent, path_var: tk.StringVar):
        self.frame = ttk.Frame(parent, padding=8)
        self.row = FlowRow(self.frame)
        self.open_button = ttk.Button(self.row.frame, text="打开 SVG")
        self.save_button = ttk.Button(self.row.frame, text="保存")
        self.save_as_button = ttk.Button(self.row.frame, text="另存为")
        self.preview_button = ttk.Button(self.row.frame, text="显示预览")
        self.element_label = ttk.Label(self.row.frame, text="元素：")
        self.path_combo = ttk.Combobox(self.row.frame, textvariable=path_var, state="readonly", width=42, values=[])
        self._build()

    def _build(self):
        self.frame.pack(fill="x")
        self.row.pack(fill="x")
        self.row.add(self.open_button)
        self.row.add(self.save_button)
        self.row.add(self.save_as_button)
        self.row.add(self.preview_button)
        self.row.add(self.element_label)
        self.row.add(self.path_combo, stretch=True)
