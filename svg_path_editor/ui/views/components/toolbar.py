import tkinter as tk
from tkinter import ttk

from .flow import FlowRow


class EditorToolbar:
    def __init__(self, parent):
        self.frame = ttk.Frame(parent, padding=8)
        self.row = FlowRow(self.frame)
        self.new_button = ttk.Button(self.row.frame, text="新建 SVG")
        self.open_button = ttk.Button(self.row.frame, text="打开 SVG")
        self.save_button = ttk.Button(self.row.frame, text="保存")
        self.save_as_button = ttk.Button(self.row.frame, text="另存为")
        self.preview_button = ttk.Button(self.row.frame, text="刷新预览")
        self._build()

    def _build(self):
        self.frame.pack(fill="x")
        self.row.pack(fill="x")
        self.row.add(self.new_button)
        self.row.add(self.open_button)
        self.row.add(self.save_button)
        self.row.add(self.save_as_button)
        self.row.add(self.preview_button)
