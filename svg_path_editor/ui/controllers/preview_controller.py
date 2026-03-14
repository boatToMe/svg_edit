from tkinter import colorchooser, messagebox

from ...core import strip_ns
from ..preview import HEX_COLOR_RE, INHERIT, PreviewRenderer, SCOPE_ALL, get_theme_style
from .base import BaseController


FLASH_COLOR = "#f97316"
FLASH_STEPS = 6
FLASH_INTERVAL_MS = 90


class PreviewController(BaseController):
    def __init__(self, app):
        super().__init__(app)
        self.preview = app.preview_view
        self._bindings_ready = False
        self.global_style_override: dict[str, str] = {}
        self.element_style_overrides: dict[int, dict[str, str]] = {}
        self.target_label_to_index: dict[str, int | None] = {SCOPE_ALL: None}
        self.flash_target_index: int | None = None
        self.flash_step_remaining = 0
        self.flash_after_id = None
        self.renderer = PreviewRenderer(strip_ns)

    def open_preview(self):
        self.preview.show()
        if not self._bindings_ready:
            self.preview.apply_button.configure(command=self.apply_preview_size)
            self.preview.zoom_in_button.configure(command=lambda: self.zoom_preview(1.1))
            self.preview.zoom_out_button.configure(command=lambda: self.zoom_preview(1 / 1.1))
            self.preview.apply_style_button.configure(command=self.apply_style_settings)
            self.preview.reset_style_button.configure(command=self.reset_style_settings)
            self.preview.pick_stroke_button.configure(command=lambda: self.pick_color(self.preview.stroke_color_var))
            self.preview.pick_fill_button.configure(command=lambda: self.pick_color(self.preview.fill_color_var))
            self.preview.width_entry.bind("<Return>", lambda _event: self.apply_preview_size())
            self.preview.stroke_width_entry.bind("<Return>", lambda _event: self.apply_style_settings())
            self.preview.stroke_color_entry.bind("<Return>", lambda _event: self.apply_style_settings())
            self.preview.fill_color_entry.bind("<Return>", lambda _event: self.apply_style_settings())
            self.preview.corner_radius_entry.bind("<Return>", lambda _event: self.apply_style_settings())
            self.preview.scope_combo.bind("<<ComboboxSelected>>", self.on_target_selected)
            self.preview.background_theme_combo.bind("<<ComboboxSelected>>", self.on_background_theme_changed)
            self.preview.canvas.bind("<MouseWheel>", self.on_mousewheel)
            self.preview.canvas.bind("<Configure>", self.on_canvas_configure)
            self._bindings_ready = True
        self.refresh_target_options(reload_fields=True)
        self._ensure_default_width()
        self.redraw_preview()

    def refresh_target_options(self, reload_fields: bool = True):
        current = self.preview.scope_var.get()
        previous_target_index = self.target_label_to_index.get(current)
        self.target_label_to_index = {SCOPE_ALL: None}
        options = [SCOPE_ALL]
        for index, element in enumerate(self.session.document.editable_elements):
            label = f"{self.session.get_element_name(index)} · {strip_ns(element.tag)}"
            self.target_label_to_index[label] = index
            options.append(label)
        self.preview.set_scope_options(options)
        if current in self.target_label_to_index:
            self.preview.scope_var.set(current)
        elif previous_target_index is not None and previous_target_index < len(self.session.document.editable_elements):
            self.preview.scope_var.set(self._label_for_index(previous_target_index))
        elif self.session.current_index is not None:
            self.preview.scope_var.set(self._label_for_index(self.session.current_index))
        else:
            self.preview.scope_var.set(SCOPE_ALL)
        if reload_fields:
            self.load_scope_settings()

    def redraw_if_open(self):
        if self.preview.is_open():
            self.refresh_target_options(reload_fields=False)
            self.redraw_preview()

    def on_target_selected(self, _event=None):
        self.load_scope_settings()
        target_index = self._get_selected_target_index()
        if target_index is not None:
            self.start_target_flash(target_index)
        else:
            self.redraw_preview()

    def on_background_theme_changed(self, _event=None):
        self.redraw_preview()

    def on_canvas_configure(self, _event=None):
        self.redraw_preview()

    def start_target_flash(self, target_index: int):
        self.flash_target_index = target_index
        self.flash_step_remaining = FLASH_STEPS
        if self.flash_after_id is not None and self.preview.frame is not None:
            self.preview.frame.after_cancel(self.flash_after_id)
            self.flash_after_id = None
        self.redraw_preview()
        self.schedule_flash_step()

    def schedule_flash_step(self):
        if self.preview.frame is None:
            return
        if self.flash_step_remaining <= 0:
            self.flash_target_index = None
            self.flash_after_id = None
            self.redraw_preview()
            return
        self.flash_after_id = self.preview.frame.after(FLASH_INTERVAL_MS, self.advance_flash)

    def advance_flash(self):
        self.flash_step_remaining -= 1
        if self.flash_step_remaining <= 0:
            self.flash_target_index = None
            self.flash_after_id = None
        self.redraw_preview()
        if self.flash_target_index is not None:
            self.schedule_flash_step()

    def _is_flash_on(self, index: int) -> bool:
        return self.flash_target_index == index and self.flash_step_remaining > 0 and self.flash_step_remaining % 2 == 0

    def _label_for_index(self, index: int) -> str:
        element = self.session.document.editable_elements[index]
        return f"{self.session.get_element_name(index)} · {strip_ns(element.tag)}"

    def apply_preview_size(self):
        try:
            width_px = self.preview.get_target_width()
        except ValueError:
            messagebox.showerror("尺寸无效", "目标宽度必须是整数像素值。")
            return
        if width_px <= 0:
            messagebox.showerror("尺寸无效", "目标宽度必须大于 0。")
            return
        self.preview.set_target_width(width_px)
        self.redraw_preview()

    def apply_style_settings(self):
        override = self._collect_style_override_from_form()
        if override is None:
            return
        target_index = self._get_selected_target_index()
        if target_index is None:
            self.global_style_override = override
        else:
            self.element_style_overrides[target_index] = override
        self.load_scope_settings()
        self.redraw_preview()

    def reset_style_settings(self):
        target_index = self._get_selected_target_index()
        if target_index is None:
            self.global_style_override = {}
        else:
            self.element_style_overrides.pop(target_index, None)
        self.load_scope_settings()
        self.redraw_preview()

    def load_scope_settings(self):
        override = self._get_scope_override()
        self.preview.stroke_width_var.set(override.get("stroke-width", ""))
        self.preview.stroke_color_var.set(override.get("stroke", ""))
        self.preview.fill_color_var.set(override.get("fill", ""))
        self.preview.corner_radius_var.set(override.get("_corner_radius", "0"))
        self.preview.linecap_var.set(override.get("stroke-linecap", INHERIT) or INHERIT)
        self.preview.linejoin_var.set(override.get("stroke-linejoin", INHERIT) or INHERIT)

    def pick_color(self, target_var):
        color = colorchooser.askcolor(color=target_var.get() or "#111827", title="选择颜色", parent=self.root)
        if not color or not color[1]:
            return
        target_var.set(color[1])

    def _collect_style_override_from_form(self):
        override: dict[str, str] = {}
        stroke_width = self.preview.stroke_width_var.get().strip()
        if stroke_width:
            try:
                width_value = float(stroke_width)
            except ValueError:
                messagebox.showerror("线条宽度无效", "线条宽度必须是数字。")
                return None
            if width_value < 0:
                messagebox.showerror("线条宽度无效", "线条宽度不能小于 0。")
                return None
            override["stroke-width"] = str(width_value)

        for key, raw in (("stroke", self.preview.stroke_color_var.get().strip()), ("fill", self.preview.fill_color_var.get().strip())):
            if raw:
                if not HEX_COLOR_RE.fullmatch(raw):
                    messagebox.showerror("颜色无效", "颜色必须是十六进制格式，例如 #111827 或 #fff。")
                    return None
                override[key] = raw

        corner_radius = self.preview.corner_radius_var.get().strip()
        if corner_radius:
            try:
                radius_value = float(corner_radius)
            except ValueError:
                messagebox.showerror("圆角无效", "圆角必须是数字。")
                return None
            if radius_value < 0:
                messagebox.showerror("圆角无效", "圆角不能小于 0。")
                return None
            override["_corner_radius"] = str(radius_value)
        else:
            override["_corner_radius"] = "0"

        if self.preview.linecap_var.get() != INHERIT:
            override["stroke-linecap"] = self.preview.linecap_var.get()
        if self.preview.linejoin_var.get() != INHERIT:
            override["stroke-linejoin"] = self.preview.linejoin_var.get()
        return override

    def _get_selected_target_index(self):
        return self.target_label_to_index.get(self.preview.scope_var.get())

    def _get_scope_override(self):
        target_index = self._get_selected_target_index()
        if target_index is None:
            return dict(self.global_style_override)
        merged = dict(self.global_style_override)
        merged.update(self.element_style_overrides.get(target_index, {}))
        return merged

    def zoom_preview(self, factor: float):
        self._ensure_default_width()
        width_px = max(1, int(round(self.preview.get_target_width() * factor)))
        self.preview.set_target_width(width_px)
        self.redraw_preview()

    def on_mousewheel(self, event):
        self.zoom_preview(1.1 if event.delta > 0 else 1 / 1.1)
        return "break"

    def _ensure_default_width(self):
        try:
            width_px = self.preview.get_target_width()
            if width_px > 0:
                return
        except ValueError:
            pass
        _min_x, _min_y, width, _height = self.renderer.get_bounds(self.session)
        self.preview.set_target_width(max(64, int(round(width))))

    def redraw_preview(self):
        if not self.preview.is_open() or self.preview.canvas is None:
            return
        try:
            width_px = max(1, self.preview.get_target_width())
        except ValueError:
            width_px = 512
            self.preview.set_target_width(width_px)
        theme_style = get_theme_style(self.preview.background_theme_var.get())
        self.renderer.redraw(
            preview=self.preview,
            session=self.session,
            theme_style=theme_style,
            target_width=width_px,
            global_style_override=self.global_style_override,
            element_style_overrides=self.element_style_overrides,
            flash_color=FLASH_COLOR,
            is_flash_on=self._is_flash_on,
        )
