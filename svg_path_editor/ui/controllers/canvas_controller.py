import math

from ...application import UpdateShapeCommand
from ...core import approximate_cubic, approximate_quadratic
from ..helpers import canvas_to_point, point_to_canvas
from .base import BaseController


OPEN_HAND_CURSOR = "hand2"
CLOSED_HAND_CURSOR = "fleur"
DEFAULT_CURSOR = ""
SHAPE_HIT_TOLERANCE = 8.0


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
        self.state.drag_shape_origin_point = None
        self.state.drag_shape_origin_handles = []
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
            return
        if self._start_shape_drag(event.x, event.y):
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
        if self.state.drag_shape_origin_point is not None:
            self._drag_active_shape(event.x, event.y)
            return
        if self.app.guide_controller.drag_active_guide(event):
            return

    def on_left_up(self, _event):
        if self.state.active_handle is not None or self.state.drag_shape_origin_point is not None:
            self._finalize_shape_drag()
        elif self.state.active_guide_index is not None:
            self.app.guide_controller.finalize_guide_move()
        self.state.active_handle = None
        self.state.active_guide_index = None
        self.state.drag_shape_origin_point = None
        self.state.drag_shape_origin_handles = []
        self.app._pan_origin = None
        self.set_canvas_cursor(OPEN_HAND_CURSOR if self.state.is_space_pressed else DEFAULT_CURSOR)

    def _finalize_shape_drag(self):
        if self.session.current_index is None or self.state.drag_shape_before_text is None or self.session.current_shape is None:
            self.state.drag_shape_before_text = None
            return
        after_text = self.session.current_shape.raw_text
        before_text = self.state.drag_shape_before_text
        self.state.drag_shape_before_text = None
        if after_text == before_text:
            return
        self.session.history.push_executed(UpdateShapeCommand(self.session, self.session.current_index, before_text, after_text))
        self.view.set_status(f"已按 {self.get_drag_step():g} 步长移动图形。")

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
        self.state.drag_shape_origin_point = None
        self.state.drag_shape_origin_handles = []
        self.app.guide_controller.refresh_guide_listbox()
        self.app.current_document.clear_draft()
        self.app.refresh_active_document_view(refit=False, restore_draft=False)

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

    def _start_shape_drag(self, canvas_x: float, canvas_y: float) -> bool:
        if self.session.current_shape is None or self.session.current_index is None:
            return False
        if not self._shape_hit_test(canvas_x, canvas_y):
            return False
        self.state.drag_shape_before_text = self.session.get_shape_text(self.session.current_index)
        self.state.drag_shape_origin_point = canvas_to_point(canvas_x, canvas_y, self.state.scale, self.state.offset_x, self.state.offset_y)
        self.state.drag_shape_origin_handles = [tuple(handle.point) for handle in self.session.handles]
        self.view.set_status(f"正在按 {self.get_drag_step():g} 步长整体移动图形。")
        return True

    def _drag_active_shape(self, canvas_x: float, canvas_y: float):
        if self.state.drag_shape_origin_point is None or not self.state.drag_shape_origin_handles:
            return
        current_point = canvas_to_point(canvas_x, canvas_y, self.state.scale, self.state.offset_x, self.state.offset_y)
        dx = self.snap_value(current_point[0] - self.state.drag_shape_origin_point[0])
        dy = self.snap_value(current_point[1] - self.state.drag_shape_origin_point[1])
        for handle, (origin_x, origin_y) in zip(self.session.handles, self.state.drag_shape_origin_handles):
            handle.point[0] = origin_x + dx
            handle.point[1] = origin_y + dy
        self.app.text_controller.handles_to_tokens()
        self.app.text_controller.refresh_text_highlights()
        self.view.set_status(f"正在按 {self.get_drag_step():g} 步长整体移动图形：dx={dx:g}, dy={dy:g}")
        self.app.redraw()

    def _shape_hit_test(self, canvas_x: float, canvas_y: float) -> bool:
        shape = self.session.current_shape
        if shape is None:
            return False
        subpaths = self._shape_subpaths(shape)
        hit_stroke = False
        for points, closed in subpaths:
            canvas_points = [point_to_canvas(point, self.state.scale, self.state.offset_x, self.state.offset_y) for point in points]
            if self._point_hits_polyline((canvas_x, canvas_y), canvas_points, closed):
                hit_stroke = True
                break
            if closed and self._point_in_polygon((canvas_x, canvas_y), canvas_points):
                return True
        return hit_stroke

    def _shape_subpaths(self, shape):
        subpaths: list[tuple[list[tuple[float, float]], bool]] = []
        current: list[tuple[float, float]] = []
        for seg in shape.segments:
            if seg.command == "M":
                if current:
                    subpaths.append((current, False))
                current = [tuple(seg.end)]
                continue
            if not current:
                current = [tuple(seg.start)]
            if seg.command in {"L", "Z"}:
                current.append(tuple(seg.end))
            elif seg.command == "Q":
                current.extend(approximate_quadratic(seg.start, seg.controls[0], seg.end)[1:])
            elif seg.command == "C":
                current.extend(approximate_cubic(seg.start, seg.controls[0], seg.controls[1], seg.end)[1:])
            if seg.command == "Z":
                if current and current[0] != current[-1]:
                    current.append(current[0])
                subpaths.append((current, True))
                current = []
        if current:
            subpaths.append((current, False))
        return subpaths

    def _point_hits_polyline(self, point, points, closed: bool) -> bool:
        if len(points) < 2:
            return False
        pairs = list(zip(points, points[1:]))
        if closed and points[0] != points[-1]:
            pairs.append((points[-1], points[0]))
        for start, end in pairs:
            if self._distance_to_segment(point, start, end) <= SHAPE_HIT_TOLERANCE:
                return True
        return False

    def _distance_to_segment(self, point, start, end) -> float:
        px, py = point
        x1, y1 = start
        x2, y2 = end
        dx = x2 - x1
        dy = y2 - y1
        if abs(dx) < 1e-9 and abs(dy) < 1e-9:
            return math.hypot(px - x1, py - y1)
        t = ((px - x1) * dx + (py - y1) * dy) / (dx * dx + dy * dy)
        t = max(0.0, min(1.0, t))
        proj_x = x1 + t * dx
        proj_y = y1 + t * dy
        return math.hypot(px - proj_x, py - proj_y)

    def _point_in_polygon(self, point, polygon) -> bool:
        x, y = point
        inside = False
        point_count = len(polygon)
        if point_count < 3:
            return False
        j = point_count - 1
        for i in range(point_count):
            xi, yi = polygon[i]
            xj, yj = polygon[j]
            intersects = ((yi > y) != (yj > y)) and (x < (xj - xi) * (y - yi) / max(yj - yi, 1e-9) + xi)
            if intersects:
                inside = not inside
            j = i
        return inside
