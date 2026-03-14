import tkinter as tk
from tkinter import ttk

from .components.flow import FlowRow


class PreviewWindow:
    def __init__(self, parent):
        self.parent = parent
        self.frame: ttk.Frame | None = None
        self.window = None
        self.width_var = tk.StringVar(value="512")
        self.size_var = tk.StringVar(value="预览尺寸：512 x 512 px")
        self.scope_var = tk.StringVar(value="整体图形")
        self.background_theme_var = tk.StringVar(value="亮色")
        self.stroke_width_var = tk.StringVar()
        self.stroke_color_var = tk.StringVar()
        self.fill_color_var = tk.StringVar()
        self.corner_radius_var = tk.StringVar(value="0")
        self.linecap_var = tk.StringVar(value="继承")
        self.linejoin_var = tk.StringVar(value="继承")
        self.canvas: tk.Canvas | None = None
        self.zoom_in_button = None
        self.zoom_out_button = None
        self.apply_button = None
        self.width_entry = None
        self.scope_combo = None
        self.background_theme_combo = None
        self.stroke_width_entry = None
        self.stroke_color_entry = None
        self.fill_color_entry = None
        self.corner_radius_entry = None
        self.linecap_combo = None
        self.linejoin_combo = None
        self.apply_style_button = None
        self.reset_style_button = None
        self.pick_stroke_button = None
        self.pick_fill_button = None

    def is_open(self) -> bool:
        return self.frame is not None and self.frame.winfo_exists()

    def ensure_window(self):
        if self.is_open():
            return self.frame
        self.frame = ttk.Frame(self.parent)
        self.frame.pack(fill="both", expand=True)

        top = FlowRow(self.frame)
        top.pack(fill="x", pady=(0, 8))
        top.add(ttk.Label(top.frame, text="目标宽度(px)："))
        self.width_entry = ttk.Entry(top.frame, textvariable=self.width_var, width=10)
        top.add(self.width_entry)
        self.apply_button = ttk.Button(top.frame, text="应用尺寸")
        top.add(self.apply_button)
        self.zoom_out_button = ttk.Button(top.frame, text="缩小 10%")
        top.add(self.zoom_out_button)
        self.zoom_in_button = ttk.Button(top.frame, text="放大 10%")
        top.add(self.zoom_in_button)
        top.add(ttk.Label(top.frame, textvariable=self.size_var), stretch=True)

        canvas_box = ttk.LabelFrame(self.frame, text="预览画布", padding=8)
        canvas_box.pack(fill="x", pady=(0, 8))
        canvas_row = FlowRow(canvas_box)
        canvas_row.pack(fill="x")
        canvas_row.add(ttk.Label(canvas_row.frame, text="背景主题"))
        self.background_theme_combo = ttk.Combobox(canvas_row.frame, textvariable=self.background_theme_var, values=["亮色", "暗色"], state="readonly", width=8)
        canvas_row.add(self.background_theme_combo)

        style_box = ttk.LabelFrame(self.frame, text="预览样式", padding=8)
        style_box.pack(fill="x", pady=(0, 8))

        row1 = FlowRow(style_box)
        row1.pack(fill="x")
        row1.add(ttk.Label(row1.frame, text="目标元素"))
        self.scope_combo = ttk.Combobox(row1.frame, textvariable=self.scope_var, values=["整体图形"], state="readonly", width=16)
        row1.add(self.scope_combo)
        row1.add(ttk.Label(row1.frame, text="线条宽度"))
        self.stroke_width_entry = ttk.Entry(row1.frame, textvariable=self.stroke_width_var, width=10)
        row1.add(self.stroke_width_entry)
        row1.add(ttk.Label(row1.frame, text="px"))

        row2 = FlowRow(style_box)
        row2.pack(fill="x", pady=(8, 0))
        row2.add(ttk.Label(row2.frame, text="线条颜色"))
        self.stroke_color_entry = ttk.Entry(row2.frame, textvariable=self.stroke_color_var, width=12)
        row2.add(self.stroke_color_entry)
        self.pick_stroke_button = ttk.Button(row2.frame, text="选择")
        row2.add(self.pick_stroke_button)
        row2.add(ttk.Label(row2.frame, text="填充颜色"))
        self.fill_color_entry = ttk.Entry(row2.frame, textvariable=self.fill_color_var, width=12)
        row2.add(self.fill_color_entry)
        self.pick_fill_button = ttk.Button(row2.frame, text="选择")
        row2.add(self.pick_fill_button)

        row3 = FlowRow(style_box)
        row3.pack(fill="x", pady=(8, 0))
        row3.add(ttk.Label(row3.frame, text="圆角"))
        self.corner_radius_entry = ttk.Entry(row3.frame, textvariable=self.corner_radius_var, width=10)
        row3.add(self.corner_radius_entry)
        row3.add(ttk.Label(row3.frame, text="边界处理"))
        self.linecap_combo = ttk.Combobox(row3.frame, textvariable=self.linecap_var, values=["继承", "butt", "round", "square"], state="readonly", width=10)
        row3.add(self.linecap_combo)
        row3.add(ttk.Label(row3.frame, text="拐弯处理"))
        self.linejoin_combo = ttk.Combobox(row3.frame, textvariable=self.linejoin_var, values=["继承", "miter", "round", "bevel"], state="readonly", width=10)
        row3.add(self.linejoin_combo)

        row4 = FlowRow(style_box)
        row4.pack(fill="x", pady=(8, 0))
        self.apply_style_button = ttk.Button(row4.frame, text="应用样式")
        row4.add(self.apply_style_button)
        self.reset_style_button = ttk.Button(row4.frame, text="重置当前范围")
        row4.add(self.reset_style_button)
        ttk.Label(style_box, text="颜色留空表示继承原始样式；圆角为预览近似效果，不会改原 SVG。", justify="left").pack(anchor="w", pady=(8, 0))

        self.canvas = tk.Canvas(self.frame, background="#ffffff", highlightthickness=1, highlightbackground="#cbd5e1")
        self.canvas.pack(fill="both", expand=True)
        return self.frame

    def show(self):
        frame = self.ensure_window()
        frame.tkraise()
        return frame

    def set_scope_options(self, options: list[str]):
        if self.scope_combo is not None:
            self.scope_combo["values"] = options
        if self.scope_var.get() not in options and options:
            self.scope_var.set(options[0])

    def get_target_width(self) -> int:
        return int(self.width_var.get().strip())

    def set_target_width(self, width_px: int):
        self.width_var.set(str(max(1, int(round(width_px)))))

    def update_size_label(self, width_px: int, height_px: int):
        self.size_var.set(f"预览尺寸：{width_px} x {height_px} px")

    def resize_canvas(self, width_px: int, height_px: int):
        if self.canvas is None:
            return
        self.canvas.configure(width=width_px, height=height_px, scrollregion=(0, 0, width_px, height_px))
