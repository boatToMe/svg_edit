import tkinter as tk
from tkinter import ttk


class PreviewWindow:
    def __init__(self, root: tk.Tk):
        self.root = root
        self.window: tk.Toplevel | None = None
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
        self._placed_once = False

    def is_open(self) -> bool:
        return self.window is not None and self.window.winfo_exists()

    def ensure_window(self):
        if self.is_open():
            return self.window
        self.window = tk.Toplevel(self.root)
        self.window.title("SVG 预览")
        self.window.geometry("820x920")
        self.window.minsize(520, 560)
        self.window.protocol("WM_DELETE_WINDOW", self.window.withdraw)

        top = ttk.Frame(self.window, padding=8)
        top.pack(fill="x")
        ttk.Label(top, text="目标宽度(px)：").pack(side="left")
        self.width_entry = ttk.Entry(top, textvariable=self.width_var, width=10)
        self.width_entry.pack(side="left", padx=(6, 8))
        self.apply_button = ttk.Button(top, text="应用尺寸")
        self.apply_button.pack(side="left")
        self.zoom_out_button = ttk.Button(top, text="缩小 10%")
        self.zoom_out_button.pack(side="left", padx=(8, 0))
        self.zoom_in_button = ttk.Button(top, text="放大 10%")
        self.zoom_in_button.pack(side="left", padx=(8, 0))
        ttk.Label(top, textvariable=self.size_var).pack(side="right")

        canvas_box = ttk.LabelFrame(self.window, text="预览画布", padding=8)
        canvas_box.pack(fill="x", padx=8, pady=(0, 8))
        canvas_row = ttk.Frame(canvas_box)
        canvas_row.pack(fill="x")
        ttk.Label(canvas_row, text="背景主题").pack(side="left")
        self.background_theme_combo = ttk.Combobox(canvas_row, textvariable=self.background_theme_var, values=["亮色", "暗色"], state="readonly", width=8)
        self.background_theme_combo.pack(side="left", padx=(8, 0))

        style_box = ttk.LabelFrame(self.window, text="预览样式", padding=8)
        style_box.pack(fill="x", padx=8, pady=(0, 8))

        row1 = ttk.Frame(style_box)
        row1.pack(fill="x")
        ttk.Label(row1, text="目标元素").pack(side="left")
        self.scope_combo = ttk.Combobox(row1, textvariable=self.scope_var, values=["整体图形"], state="readonly", width=16)
        self.scope_combo.pack(side="left", padx=(8, 16))
        ttk.Label(row1, text="线条宽度").pack(side="left")
        self.stroke_width_entry = ttk.Entry(row1, textvariable=self.stroke_width_var, width=10)
        self.stroke_width_entry.pack(side="left", padx=(8, 6))
        ttk.Label(row1, text="px").pack(side="left")

        row2 = ttk.Frame(style_box)
        row2.pack(fill="x", pady=(8, 0))
        ttk.Label(row2, text="线条颜色").pack(side="left")
        self.stroke_color_entry = ttk.Entry(row2, textvariable=self.stroke_color_var, width=12)
        self.stroke_color_entry.pack(side="left", padx=(8, 6))
        self.pick_stroke_button = ttk.Button(row2, text="选择")
        self.pick_stroke_button.pack(side="left", padx=(0, 16))
        ttk.Label(row2, text="填充颜色").pack(side="left")
        self.fill_color_entry = ttk.Entry(row2, textvariable=self.fill_color_var, width=12)
        self.fill_color_entry.pack(side="left", padx=(8, 6))
        self.pick_fill_button = ttk.Button(row2, text="选择")
        self.pick_fill_button.pack(side="left")

        row3 = ttk.Frame(style_box)
        row3.pack(fill="x", pady=(8, 0))
        ttk.Label(row3, text="圆角").pack(side="left")
        self.corner_radius_entry = ttk.Entry(row3, textvariable=self.corner_radius_var, width=10)
        self.corner_radius_entry.pack(side="left", padx=(8, 16))
        ttk.Label(row3, text="边界处理").pack(side="left")
        self.linecap_combo = ttk.Combobox(row3, textvariable=self.linecap_var, values=["继承", "butt", "round", "square"], state="readonly", width=10)
        self.linecap_combo.pack(side="left", padx=(8, 16))
        ttk.Label(row3, text="拐弯处理").pack(side="left")
        self.linejoin_combo = ttk.Combobox(row3, textvariable=self.linejoin_var, values=["继承", "miter", "round", "bevel"], state="readonly", width=10)
        self.linejoin_combo.pack(side="left", padx=(8, 0))

        row4 = ttk.Frame(style_box)
        row4.pack(fill="x", pady=(8, 0))
        self.apply_style_button = ttk.Button(row4, text="应用样式")
        self.apply_style_button.pack(side="left")
        self.reset_style_button = ttk.Button(row4, text="重置当前范围")
        self.reset_style_button.pack(side="left", padx=(8, 0))
        ttk.Label(style_box, text="颜色留空表示继承原始样式；圆角为预览近似效果，不会改原 SVG。", justify="left").pack(anchor="w", pady=(8, 0))

        body = ttk.Frame(self.window, padding=(8, 0, 8, 8))
        body.pack(fill="both", expand=True)
        self.canvas = tk.Canvas(body, background="#ffffff", highlightthickness=1, highlightbackground="#cbd5e1")
        self.canvas.pack(fill="both", expand=True)
        return self.window

    def _place_beside_root(self):
        if self.window is None or self._placed_once:
            return
        self.root.update_idletasks()
        self.window.update_idletasks()
        root_x = self.root.winfo_rootx()
        root_y = self.root.winfo_rooty()
        root_w = self.root.winfo_width()
        root_h = self.root.winfo_height()
        window_w = self.window.winfo_width()
        window_h = self.window.winfo_height()
        screen_w = self.window.winfo_screenwidth()
        screen_h = self.window.winfo_screenheight()
        x = min(screen_w - window_w, root_x + root_w + 16)
        x = max(0, x)
        y = max(0, min(screen_h - window_h, root_y + max(0, (root_h - window_h) // 2)))
        self.window.geometry(f"{window_w}x{window_h}+{x}+{y}")
        self._placed_once = True

    def show(self):
        window = self.ensure_window()
        self._place_beside_root()
        window.deiconify()
        window.lift()
        window.focus_force()

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
