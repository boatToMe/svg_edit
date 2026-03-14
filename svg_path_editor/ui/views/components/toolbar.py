import tkinter as tk
from tkinter import ttk


class EditorToolbar:
    def __init__(self, parent, path_var: tk.StringVar):
        self.frame = ttk.Frame(parent, padding=8)
        self.open_button = ttk.Button(self.frame, text="打开 SVG")
        self.save_button = ttk.Button(self.frame, text="保存")
        self.save_as_button = ttk.Button(self.frame, text="另存为")
        self.preview_button = ttk.Button(self.frame, text="显示预览")
        self.path_combo = ttk.Combobox(self.frame, textvariable=path_var, state="readonly", width=42, values=[])
        self._build()

    def _build(self):
        self.frame.pack(fill="x")
        self.open_button.pack(side="left")
        self.save_button.pack(side="left", padx=(8, 0))
        self.save_as_button.pack(side="left", padx=(8, 0))
        self.preview_button.pack(side="left", padx=(8, 0))
        ttk.Label(self.frame, text="元素：").pack(side="left", padx=(18, 6))
        self.path_combo.pack(side="left", fill="x", expand=True)
