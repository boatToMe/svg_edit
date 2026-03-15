import tkinter as tk
from tkinter import ttk

from .components import BrowserPreview, ColorSettingsGroup, LabeledControl, PreviewCanvasSettings, StrokeSettingsGroup, ZoomControls


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
        self.browser_preview: BrowserPreview | None = None
        self.zoom_controls: ZoomControls | None = None
        self.canvas_settings: PreviewCanvasSettings | None = None
        self.color_settings: ColorSettingsGroup | None = None
        self.stroke_settings: StrokeSettingsGroup | None = None
        self.target_control: LabeledControl | None = None
        self.reset_style_button = None
        self.scope_combo = None

        self.apply_button = None
        self.zoom_in_button = None
        self.zoom_out_button = None
        self.width_entry = None
        self.background_theme_combo = None
        self.stroke_width_entry = None
        self.corner_radius_entry = None
        self.linecap_combo = None
        self.linejoin_combo = None
        self.stroke_color_field = None
        self.fill_color_field = None

    def is_open(self) -> bool:
        return self.frame is not None and self.frame.winfo_exists()

    def ensure_window(self):
        if self.is_open():
            return self.frame
        self.frame = ttk.Frame(self.parent)
        self.frame.pack(fill="both", expand=True)

        self.zoom_controls = ZoomControls(self.frame, self.width_var, self.size_var)
        self.apply_button = self.zoom_controls.apply_button
        self.zoom_in_button = self.zoom_controls.zoom_in_button
        self.zoom_out_button = self.zoom_controls.zoom_out_button
        self.width_entry = self.zoom_controls.width_entry

        self.canvas_settings = PreviewCanvasSettings(self.frame, self.background_theme_var)
        self.background_theme_combo = self.canvas_settings.background_theme_combo
        self.reset_style_button = self.canvas_settings.reset_button

        style_box = ttk.LabelFrame(self.frame, text="样式编辑", padding=8)
        style_box.pack(fill="x", pady=(0, 8))

        self.target_control = LabeledControl(style_box, "目标元素")
        self.target_control.frame.pack(anchor="w")
        self.scope_combo = self.target_control.attach(
            ttk.Combobox(self.target_control.content, textvariable=self.scope_var, values=["整体图形"], state="readonly", width=18)
        )

        self.color_settings = ColorSettingsGroup(style_box)
        self.stroke_color_field = self.color_settings.stroke_field
        self.fill_color_field = self.color_settings.fill_field

        self.stroke_settings = StrokeSettingsGroup(
            style_box,
            self.stroke_width_var,
            self.corner_radius_var,
            self.linecap_var,
            self.linejoin_var,
        )
        self.stroke_width_entry = self.stroke_settings.stroke_width_entry
        self.corner_radius_entry = self.stroke_settings.corner_radius_entry
        self.linecap_combo = self.stroke_settings.linecap_combo
        self.linejoin_combo = self.stroke_settings.linejoin_combo

        self.browser_preview = BrowserPreview(self.frame)
        self.browser_preview.frame.pack(fill="both", expand=True)
        self.update_color_swatch("stroke")
        self.update_color_swatch("fill")
        self.set_document_loaded(False)
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

    def set_document_loaded(self, loaded: bool):
        if not self.is_open():
            return
        self.zoom_controls.set_enabled(loaded)
        self.canvas_settings.set_enabled(loaded)
        self.color_settings.set_enabled(loaded)
        self.stroke_settings.set_enabled(loaded)
        self.scope_combo.configure(state="readonly" if loaded else "disabled")
        if not loaded:
            self.size_var.set("预览尺寸：未加载 SVG")

    def get_target_width(self) -> int:
        return int(self.width_var.get().strip())

    def set_target_width(self, width_px: int):
        self.width_var.set(str(max(1, int(round(width_px)))))

    def update_size_label(self, width_px: int, height_px: int, zoom_percent: int = 100):
        self.size_var.set(f"预览尺寸：{width_px} x {height_px} px · {zoom_percent}%")

    def set_preview_html(self, html_text: str):
        if self.browser_preview is None:
            return
        self.browser_preview.set_html(html_text)

    def get_preview_viewport_size(self) -> tuple[int, int]:
        if self.browser_preview is None:
            return (0, 0)
        return self.browser_preview.get_viewport_size()

    def is_browser_available(self) -> bool:
        return self.browser_preview is not None and self.browser_preview.is_available()

    def update_color_swatch(self, kind: str):
        if kind == "stroke":
            value = self.stroke_color_var.get().strip()
            field = self.stroke_color_field
        else:
            value = self.fill_color_var.get().strip()
            field = self.fill_color_field
        if field is None:
            return
        field.set_color(value)
