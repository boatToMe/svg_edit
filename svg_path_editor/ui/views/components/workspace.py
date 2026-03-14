import tkinter as tk
from tkinter import ttk

from .inspector import InspectorSidebar


PREVIEW_WEIGHT = 3
CANVAS_WEIGHT = 5
INSPECTOR_WEIGHT = 2
TOTAL_WEIGHT = PREVIEW_WEIGHT + CANVAS_WEIGHT + INSPECTOR_WEIGHT


class PreviewPane:
    def __init__(self, parent):
        self.frame = ttk.Frame(parent, padding=(0, 0, 8, 0))
        self.host = ttk.LabelFrame(self.frame, text="预览", padding=8)
        self._build()

    def _build(self):
        self.host.pack(fill="both", expand=True)


class CanvasPane:
    def __init__(self, parent):
        self.frame = ttk.Frame(parent, padding=(0, 0, 8, 0))
        self.canvas = tk.Canvas(self.frame, background="#f8fafc", highlightthickness=0)
        self._build()

    def _build(self):
        self.canvas.pack(fill="both", expand=True)


class EditorWorkspace:
    def __init__(self, parent, guide_axis_var: tk.StringVar, guide_value_var: tk.StringVar, drag_step_var: tk.StringVar):
        self.main = ttk.PanedWindow(parent, orient="horizontal")
        self.preview_pane = PreviewPane(self.main)
        self.canvas_pane = CanvasPane(self.main)
        self.inspector = InspectorSidebar(self.main, guide_axis_var, guide_value_var, drag_step_var)
        self._layout_after_id = None
        self._build(parent)

    def _build(self, parent):
        self.main.pack(fill="both", expand=True, padx=8, pady=(0, 8))
        self.main.add(self.preview_pane.frame)
        self.main.add(self.canvas_pane.frame)
        self.main.add(self.inspector.frame)
        self.main.bind("<Configure>", self._on_configure)
        self.main.after_idle(self._apply_proportions)

    def _on_configure(self, _event=None):
        if self._layout_after_id is not None:
            self.main.after_cancel(self._layout_after_id)
        self._layout_after_id = self.main.after_idle(self._apply_proportions)

    def _apply_proportions(self):
        self._layout_after_id = None
        total_width = self.main.winfo_width()
        if total_width <= 1:
            return

        preview_width = int(total_width * PREVIEW_WEIGHT / TOTAL_WEIGHT)
        canvas_width = int(total_width * CANVAS_WEIGHT / TOTAL_WEIGHT)
        preview_canvas_boundary = preview_width
        canvas_inspector_boundary = preview_width + canvas_width

        try:
            self.main.sashpos(0, preview_canvas_boundary)
            self.main.sashpos(1, canvas_inspector_boundary)
        except tk.TclError:
            return
