import math

from ...application import UpdateShapeCommand
from ..helpers import canvas_to_point, point_to_canvas
from .base import BaseController


OPEN_HAND_CURSOR = "hand2"
CLOSED_HAND_CURSOR = "fleur"
DEFAULT_CURSOR = ""


class CanvasController(BaseController):
    def fit_view(self):
        if self.session.document.view_box is not None:
            min_x, min_y, width, height = self.session.document.view_box
        else:
            points = []
            for _, shape in self.session.get_display_shapes():
                for seg in shape.segments:
                    points.append(seg.start)
                    points.append(seg.end)
                    points.extend(seg.controls)
            if not points:
                self.state.scale = 1.0
                self.state.offset_x = self.state.padding
                self.state.offset_y = self.state.padding
                return
            xs = [p[0] for p in points]
            ys = [p[1] for p in points]
            min_x, max_x = min(xs), max(xs)
            min_y, max_y = min(ys), max(ys)
            width = max(1.0, max_x - min_x)
            height = max(1.0, max_y - min_y)
        canvas_w = max(300, self.view.canvas.winfo_width())
        canvas_h = max(300, self.view.canvas.winfo_height())
        self.state.scale = max(0.05, min((canvas_w - self.state.padding * 2) / max(1.0, width), (canvas_h - self.state.padding * 2) / max(1.0, height)))
        self.state.offset_x = self.state.padding - min_x * self.state.scale
        self.state.offset_y = self.state.padding - min_y * self.state.scale

    def get_drag_step(self) -> float:
        return self.view.get_drag_step()

    def snap_value(self, value: float) -> float:
        step = self.get_drag_step()
        return round(value / step) * step

    def snap_point(self, point: tuple[float, float]) -> tuple[float, float]:
        return (self.snap_value(point[0]), self.snap_value(point[1]))

    def set_canvas_cursor(self, cursor: str):
        self.view.canvas.configure(cursor=cursor)

    def show_toast(self, text: str):
        self.state.toast_text = text
        if self.state.toast_after_id is not None:
            self.root.after_cancel(self.state.toast_after_id)
        self.state.toast_after_id = self.root.after(1200, self.clear_toast)
        self.app.redraw()

    def clear_toast(self):
        self.state.toast_text = None
        self.state.toast_after_id = None
        self.app.redraw()

    def on_space_press(self, _event=None):
        self.state.is_space_pressed = True
        if self.app._pan_origin is None:
            self.set_canvas_cursor(OPEN_HAND_CURSOR)
        return "break"

    def on_space_release(self, _event=None):
        self.state.is_space_pressed = False
        self.app._pan_origin = None
        self.set_canvas_cursor(DEFAULT_CURSOR)
        return "break"

    def on_left_down(self, event):
        self.state.active_handle = None
        self.state.active_guide_index = None
        self.state.drag_shape_before_text = None
        self.state.drag_guide_before_value = None
        if self.state.is_space_pressed:
            self.on_pan_start(event)
            return
        self.state.active_handle = self.find_handle(event.x, event.y)
        if self.state.active_handle is not None:
            if self.session.current_index is not None:
                self.state.drag_shape_before_text = self.session.get_shape_text(self.session.current_index)
            self.state.focus_handle = self.state.active_handle
            focus_index = self.app.text_controller.get_focus_handle_index()
            self.state.text_selected_handle_indices = {focus_index} if focus_index is not None else set()
            self.app.text_controller.refresh_text_highlights()
            self.app.redraw()
            return
        guide_index = self.app.guide_controller.find_selected_guide_hit(event.x, event.y)
        if guide_index is not None:
            self.state.active_guide_index = guide_index
            self.state.drag_guide_before_value = self.state.custom_guides[guide_index][1]
            self.app.redraw()

    def on_left_drag(self, event):
        if self.state.is_space_pressed and self.app._pan_origin is not None:
            self.on_pan_drag(event)
            return
        if self.state.active_handle is not None:
            new_point = canvas_to_point(event.x, event.y, self.state.scale, self.state.offset_x, self.state.offset_y)
            snapped_point = self.snap_point(new_point)
            self.state.active_handle.point[0] = snapped_point[0]
            self.state.active_handle.point[1] = snapped_point[1]
            self.state.focus_handle = self.state.active_handle
            self.app.text_controller.handles_to_tokens()
            focus_index = self.app.text_controller.get_focus_handle_index()
            self.state.text_selected_handle_indices = {focus_index} if focus_index is not None else set()
            self.app.text_controller.refresh_text_highlights()
            self.app.redraw()
            return
        if self.app.guide_controller.drag_active_guide(event):
            return

    def on_left_up(self, _event):
        if self.state.active_handle is not None:
            self._finalize_handle_drag()
        elif self.state.active_guide_index is not None:
            self.app.guide_controller.finalize_guide_move()
        self.state.active_handle = None
        self.state.active_guide_index = None
        self.app._pan_origin = None
        self.set_canvas_cursor(OPEN_HAND_CURSOR if self.state.is_space_pressed else DEFAULT_CURSOR)

    def _finalize_handle_drag(self):
        if self.session.current_index is None or self.state.drag_shape_before_text is None or self.session.current_shape is None:
            self.state.drag_shape_before_text = None
            return
        after_text = self.session.current_shape.raw_text
        before_text = self.state.drag_shape_before_text
        self.state.drag_shape_before_text = None
        if after_text == before_text:
            return
        self.session.history.push_executed(UpdateShapeCommand(self.session, self.session.current_index, before_text, after_text))
        self.view.set_status(f"已按 {self.get_drag_step():g} 步长移动端点。")

    def on_pan_start(self, event):
        self.app._pan_origin = (event.x, event.y)
        self.set_canvas_cursor(CLOSED_HAND_CURSOR)
        self.view.set_status("正在移动画布。")

    def on_pan_drag(self, event):
        if self.app._pan_origin is None:
            self.app._pan_origin = (event.x, event.y)
            return
        last_x, last_y = self.app._pan_origin
        self.state.offset_x += event.x - last_x
        self.state.offset_y += event.y - last_y
        self.app._pan_origin = (event.x, event.y)
        self.app.redraw()

    def on_mousewheel(self, event):
        factor = 1.1 if event.delta > 0 else 1 / 1.1
        old_scale = self.state.scale
        self.state.scale = max(0.02, min(50, self.state.scale * factor))
        mouse_svg = canvas_to_point(event.x, event.y, old_scale, self.state.offset_x, self.state.offset_y)
        self.state.offset_x = event.x - mouse_svg[0] * self.state.scale
        self.state.offset_y = event.y - mouse_svg[1] * self.state.scale
        self.app.redraw()

    def _refresh_after_history(self):
        self.state.selected_guide_index = None
        self.state.active_guide_index = None
        self.state.drag_shape_before_text = None
        self.state.drag_guide_before_value = None
        self.app.guide_controller.refresh_guide_listbox()
        if self.session.current_index is not None:
            self.app.file_controller.load_path(self.session.current_index, show_toast=False, refit=False)
        else:
            self.app.redraw()

    def on_undo(self, _event=None):
        command = self.session.history.undo()
        if command is not None:
            self._refresh_after_history()
            self.view.set_status(f"已撤销：{command.label}。")
        return "break"

    def on_redo(self, _event=None):
        command = self.session.history.redo()
        if command is not None:
            self._refresh_after_history()
            self.view.set_status(f"已重做：{command.label}。")
        return "break"

    def find_handle(self, canvas_x, canvas_y):
        for handle in reversed(self.session.handles):
            hx, hy = point_to_canvas(handle.point, self.state.scale, self.state.offset_x, self.state.offset_y)
            if math.hypot(canvas_x - hx, hy - canvas_y) <= 10:
                return handle
        return None
