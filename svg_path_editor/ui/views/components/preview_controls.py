import tkinter as tk
from tkinter import ttk

from .flow import FlowRow


CHECKER_LIGHT = "#f8fafc"
CHECKER_DARK = "#cbd5e1"
SWATCH_BORDER = "#64748b"
SWATCH_SIZE = 18


class LabeledControl:
    def __init__(self, parent, label_text: str):
        self.frame = ttk.Frame(parent)
        self.label = ttk.Label(self.frame, text=label_text)
        self.content = ttk.Frame(self.frame)
        self.widget = None
        self._build()

    def _build(self):
        self.label.pack(side="left")
        self.content.pack(side="left", padx=(6, 0))

    def attach(self, widget):
        self.widget = widget
        widget.pack(in_=self.content, side="left")
        return widget

    def set_enabled(self, enabled: bool):
        if self.widget is not None:
            try:
                self.widget.configure(state="readonly" if enabled and isinstance(self.widget, ttk.Combobox) else ("normal" if enabled else "disabled"))
            except tk.TclError:
                pass


class ButtonPair:
    def __init__(self, parent, first_text: str, second_text: str):
        self.frame = ttk.Frame(parent)
        self.first_button = ttk.Button(self.frame, text=first_text)
        self.second_button = ttk.Button(self.frame, text=second_text)
        self._build()

    def _build(self):
        self.first_button.pack(side="left")
        self.second_button.pack(side="left", padx=(6, 0))

    def set_enabled(self, enabled: bool):
        state = "normal" if enabled else "disabled"
        self.first_button.configure(state=state)
        self.second_button.configure(state=state)


class CheckerboardSwatch(tk.Canvas):
    def __init__(self, parent, size: int = SWATCH_SIZE):
        super().__init__(parent, width=size, height=size, highlightthickness=0, bd=0, relief="flat", cursor="hand2")
        self.size = size
        self._color = ""
        self._draw()

    def _draw(self):
        self.delete("all")
        block = self.size // 2
        for row in range(2):
            for column in range(2):
                color = CHECKER_LIGHT if (row + column) % 2 == 0 else CHECKER_DARK
                x0 = column * block
                y0 = row * block
                self.create_rectangle(x0, y0, x0 + block, y0 + block, fill=color, outline=color)
        if self._color:
            self.create_rectangle(1, 1, self.size - 1, self.size - 1, fill=self._color, outline=self._color)
        self.create_rectangle(0, 0, self.size - 1, self.size - 1, outline=SWATCH_BORDER)

    def set_color(self, color: str):
        self._color = color.strip()
        self._draw()


class ColorField:
    def __init__(self, parent, label_text: str):
        self.frame = ttk.Frame(parent)
        self.row = ttk.Frame(self.frame)
        self.label = ttk.Label(self.row, text=label_text)
        self.swatch = CheckerboardSwatch(self.row)
        self._enabled = True
        self._build()

    def _build(self):
        self.row.pack(anchor="w")
        self.label.pack(side="left")
        self.swatch.pack(side="left", padx=(6, 0))

    def set_color(self, color: str):
        self.swatch.set_color(color)

    def bind_pick(self, callback):
        self.swatch.bind("<Button-1>", callback)

    def set_enabled(self, enabled: bool):
        self._enabled = enabled
        self.swatch.configure(cursor="hand2" if enabled else "arrow")


class ZoomControls:
    def __init__(self, parent, width_var: tk.StringVar, size_var: tk.StringVar):
        self.frame = ttk.LabelFrame(parent, text="预览缩放", padding=8)
        self.row = FlowRow(self.frame)
        self.width_control = LabeledControl(self.row.frame, "目标宽度(px)：")
        self.width_entry = self.width_control.attach(ttk.Entry(self.width_control.content, textvariable=width_var, width=10))
        self.apply_button = ttk.Button(self.row.frame, text="应用尺寸")
        self.zoom_buttons = ButtonPair(self.row.frame, "缩小 10%", "放大 10%")
        self.zoom_out_button = self.zoom_buttons.first_button
        self.zoom_in_button = self.zoom_buttons.second_button
        self.size_label = ttk.Label(self.row.frame, textvariable=size_var)
        self._build()

    def _build(self):
        self.frame.pack(fill="x", pady=(0, 8))
        self.row.pack(fill="x")
        self.row.add(self.width_control.frame)
        self.row.add(self.apply_button)
        self.row.add(self.zoom_buttons.frame)
        self.row.add(self.size_label, stretch=True)

    def set_enabled(self, enabled: bool):
        self.width_entry.configure(state="normal" if enabled else "disabled")
        self.apply_button.configure(state="normal" if enabled else "disabled")
        self.zoom_buttons.set_enabled(enabled)


class PreviewCanvasSettings:
    def __init__(self, parent, background_theme_var: tk.StringVar):
        self.frame = ttk.LabelFrame(parent, text="预览设置", padding=8)
        self.row = FlowRow(self.frame)
        self.background_control = LabeledControl(self.row.frame, "画布主题")
        self.background_theme_combo = self.background_control.attach(
            ttk.Combobox(self.background_control.content, textvariable=background_theme_var, values=["亮色", "暗色"], state="readonly", width=8)
        )
        self.reset_button = ttk.Button(self.row.frame, text="重置设置")
        self._build()

    def _build(self):
        self.frame.pack(fill="x", pady=(0, 8))
        self.row.pack(fill="x")
        self.row.add(self.background_control.frame)
        self.row.add(self.reset_button)

    def set_enabled(self, enabled: bool):
        self.background_theme_combo.configure(state="readonly" if enabled else "disabled")
        self.reset_button.configure(state="normal" if enabled else "disabled")


class ColorSettingsGroup:
    def __init__(self, parent):
        self.frame = ttk.LabelFrame(parent, text="颜色样式", padding=8)
        self.row = FlowRow(self.frame)
        self.stroke_field = ColorField(self.row.frame, "线条颜色")
        self.fill_field = ColorField(self.row.frame, "填充颜色")
        self._build()

    def _build(self):
        self.frame.pack(fill="x", pady=(8, 0))
        self.row.pack(fill="x")
        self.row.add(self.stroke_field.frame)
        self.row.add(self.fill_field.frame)

    def set_enabled(self, enabled: bool):
        self.stroke_field.set_enabled(enabled)
        self.fill_field.set_enabled(enabled)


class StrokeSettingsGroup:
    def __init__(self, parent, stroke_width_var: tk.StringVar, corner_radius_var: tk.StringVar, linecap_var: tk.StringVar, linejoin_var: tk.StringVar):
        self.frame = ttk.LabelFrame(parent, text="线条参数", padding=8)
        self.row = FlowRow(self.frame)
        self.stroke_width_control = LabeledControl(self.row.frame, "线条宽度")
        self.stroke_width_entry = self.stroke_width_control.attach(ttk.Entry(self.stroke_width_control.content, textvariable=stroke_width_var, width=10))
        ttk.Label(self.stroke_width_control.content, text="px").pack(side="left", padx=(4, 0))
        self.corner_radius_control = LabeledControl(self.row.frame, "圆角")
        self.corner_radius_entry = self.corner_radius_control.attach(ttk.Entry(self.corner_radius_control.content, textvariable=corner_radius_var, width=10))
        self.linecap_control = LabeledControl(self.row.frame, "边界处理")
        self.linecap_combo = self.linecap_control.attach(
            ttk.Combobox(self.linecap_control.content, textvariable=linecap_var, values=["继承", "butt", "round", "square"], state="readonly", width=10)
        )
        self.linejoin_control = LabeledControl(self.row.frame, "拐弯处理")
        self.linejoin_combo = self.linejoin_control.attach(
            ttk.Combobox(self.linejoin_control.content, textvariable=linejoin_var, values=["继承", "miter", "round", "bevel"], state="readonly", width=10)
        )
        self._build()

    def _build(self):
        self.frame.pack(fill="x", pady=(8, 0))
        self.row.pack(fill="x")
        self.row.add(self.stroke_width_control.frame)
        self.row.add(self.corner_radius_control.frame)
        self.row.add(self.linecap_control.frame)
        self.row.add(self.linejoin_control.frame)

    def set_enabled(self, enabled: bool):
        state = "normal" if enabled else "disabled"
        combo_state = "readonly" if enabled else "disabled"
        self.stroke_width_entry.configure(state=state)
        self.corner_radius_entry.configure(state=state)
        self.linecap_combo.configure(state=combo_state)
        self.linejoin_combo.configure(state=combo_state)
