from ..models import Handle, Segment
from ..path_ops import approximate_cubic, approximate_quadratic
from .constants import (
    ALL_SHAPES_COLOR,
    CENTER_GUIDE_COLOR,
    CUSTOM_GUIDE_ACTIVE_COLOR,
    CUSTOM_GUIDE_COLOR,
    HANDLE_FOCUS_COLOR,
    HANDLE_LABEL_COLOR,
    INFO_BG_COLOR,
    INFO_BORDER_COLOR,
    INFO_TEXT_COLOR,
    SELECTED_SHAPE_COLOR,
    TOAST_BG_COLOR,
    TOAST_FG_COLOR,
    VIEWBOX_BORDER_COLOR,
    VIEWBOX_WARNING_COLOR,
    WARNING_TEXT_COLOR,
)
from .helpers import point_to_canvas


def redraw(controller):
    canvas = controller.view.canvas
    canvas.delete("all")
    draw_grid(controller)
    draw_viewbox_guides(controller)
    draw_custom_guides(controller)
    for idx, shape in controller.session.get_display_shapes():
        is_selected = idx == controller.session.current_index
        color = SELECTED_SHAPE_COLOR if is_selected else ALL_SHAPES_COLOR
        width = 2.5 if is_selected else 1.5
        for seg in shape.segments:
            draw_segment(controller, seg, color=color, width=width, show_controls=is_selected)
    draw_handles(controller)
    draw_viewbox_size_hint(controller)
    draw_toast(controller)


def draw_grid(controller):
    canvas = controller.view.canvas
    state = controller.state
    w = canvas.winfo_width()
    h = canvas.winfo_height()
    if w <= 1 or h <= 1:
        return
    grid_color = "#e5e7eb"
    axis_color = "#cbd5e1"
    step = max(20, int(state.scale * 10))
    start_x = int(state.offset_x % step)
    start_y = int(state.offset_y % step)
    for x in range(start_x, w, step):
        canvas.create_line(x, 0, x, h, fill=grid_color)
    for y in range(start_y, h, step):
        canvas.create_line(0, y, w, y, fill=grid_color)
    if 0 <= state.offset_x <= w:
        canvas.create_line(state.offset_x, 0, state.offset_x, h, fill=axis_color, width=2)
    if 0 <= state.offset_y <= h:
        canvas.create_line(0, state.offset_y, w, state.offset_y, fill=axis_color, width=2)


def draw_viewbox_guides(controller):
    canvas = controller.view.canvas
    state = controller.state
    view_box = controller.session.document.view_box
    if view_box is None:
        return
    min_x, min_y, width, height = view_box
    max_x = min_x + width
    max_y = min_y + height
    center_x = min_x + width / 2
    center_y = min_y + height / 2
    exceeds = current_shape_exceeds_viewbox(controller)
    guide_color = VIEWBOX_WARNING_COLOR if exceeds else VIEWBOX_BORDER_COLOR
    center_color = VIEWBOX_WARNING_COLOR if exceeds else CENTER_GUIDE_COLOR
    guide_width = 2.2 if exceeds else 1.5
    left_top = point_to_canvas((min_x, min_y), state.scale, state.offset_x, state.offset_y)
    right_bottom = point_to_canvas((max_x, max_y), state.scale, state.offset_x, state.offset_y)
    canvas.create_rectangle(left_top[0], left_top[1], right_bottom[0], right_bottom[1], outline=guide_color, dash=(6, 4), width=guide_width)
    center_top = point_to_canvas((center_x, min_y), state.scale, state.offset_x, state.offset_y)
    center_bottom = point_to_canvas((center_x, max_y), state.scale, state.offset_x, state.offset_y)
    center_left = point_to_canvas((min_x, center_y), state.scale, state.offset_x, state.offset_y)
    center_right = point_to_canvas((max_x, center_y), state.scale, state.offset_x, state.offset_y)
    canvas.create_line(*center_top, *center_bottom, fill=center_color, dash=(4, 4), width=guide_width)
    canvas.create_line(*center_left, *center_right, fill=center_color, dash=(4, 4), width=guide_width)
    center = point_to_canvas((center_x, center_y), state.scale, state.offset_x, state.offset_y)
    size = 8
    canvas.create_line(center[0] - size, center[1], center[0] + size, center[1], fill=center_color, width=2)
    canvas.create_line(center[0], center[1] - size, center[0], center[1] + size, fill=center_color, width=2)
    canvas.create_text(center[0] + 12, center[1] - 12, text=f"中心 ({center_x:g}, {center_y:g})", fill=center_color, anchor="sw", font=("Segoe UI", 9, "bold"))


def draw_custom_guides(controller):
    canvas = controller.view.canvas
    state = controller.state
    view_box = controller.session.document.view_box
    if not state.custom_guides or view_box is None:
        return
    min_x, min_y, width, height = view_box
    max_x = min_x + width
    max_y = min_y + height
    for idx, (axis, value) in enumerate(state.custom_guides):
        is_selected = idx == state.selected_guide_index
        color = CUSTOM_GUIDE_ACTIVE_COLOR if is_selected else CUSTOM_GUIDE_COLOR
        line_width = 2.2 if is_selected else 1.5
        if axis == "x":
            top = point_to_canvas((value, min_y), state.scale, state.offset_x, state.offset_y)
            bottom = point_to_canvas((value, max_y), state.scale, state.offset_x, state.offset_y)
            canvas.create_line(*top, *bottom, fill=color, dash=(2, 4), width=line_width)
            canvas.create_text(top[0] + 6, top[1] + 8, text=f"x={value:g}", anchor="nw", fill=color, font=("Segoe UI", 9, "bold"))
        else:
            left = point_to_canvas((min_x, value), state.scale, state.offset_x, state.offset_y)
            right = point_to_canvas((max_x, value), state.scale, state.offset_x, state.offset_y)
            canvas.create_line(*left, *right, fill=color, dash=(2, 4), width=line_width)
            canvas.create_text(left[0] + 6, left[1] - 6, text=f"y={value:g}", anchor="sw", fill=color, font=("Segoe UI", 9, "bold"))


def draw_segment(controller, seg: Segment, color: str, width: float, show_controls: bool):
    canvas = controller.view.canvas
    state = controller.state
    if seg.command == "M":
        return
    if seg.command in {"L", "Z"}:
        start = point_to_canvas(seg.start, state.scale, state.offset_x, state.offset_y)
        end = point_to_canvas(seg.end, state.scale, state.offset_x, state.offset_y)
        canvas.create_line(*start, *end, fill=color, width=width)
        return
    if seg.command == "Q":
        points = approximate_quadratic(seg.start, seg.controls[0], seg.end)
    elif seg.command == "C":
        points = approximate_cubic(seg.start, seg.controls[0], seg.controls[1], seg.end)
    else:
        points = [seg.start, seg.end]
    flat = []
    for point in points:
        flat.extend(point_to_canvas(point, state.scale, state.offset_x, state.offset_y))
    canvas.create_line(*flat, fill=color, width=width, smooth=True)
    if show_controls:
        for control in seg.controls:
            start = point_to_canvas(seg.start, state.scale, state.offset_x, state.offset_y)
            ctrl = point_to_canvas(control, state.scale, state.offset_x, state.offset_y)
            end = point_to_canvas(seg.end, state.scale, state.offset_x, state.offset_y)
            canvas.create_line(*start, *ctrl, fill="#f59e0b", dash=(4, 3))
            canvas.create_line(*end, *ctrl, fill="#f59e0b", dash=(4, 3))


def draw_handles(controller):
    canvas = controller.view.canvas
    state = controller.state
    highlighted_indices = set(state.text_selected_handle_indices)
    focus_index = controller.get_focus_handle_index()
    for index, handle in enumerate(controller.session.handles):
        x, y = point_to_canvas(handle.point, state.scale, state.offset_x, state.offset_y)
        is_focus = focus_index is not None and index == focus_index
        is_selected = index in highlighted_indices
        active = is_focus or is_selected
        if handle.kind == "anchor":
            fill = HANDLE_FOCUS_COLOR if active else "#2563eb"
            radius = 6 if active else 5
        else:
            fill = HANDLE_FOCUS_COLOR if active else "#f97316"
            radius = 5 if active else 4
        canvas.create_oval(x - radius, y - radius, x + radius, y + radius, fill=fill, outline="white", width=1.5)
        draw_handle_label(controller, handle, x, y, active)


def draw_handle_label(controller, handle: Handle, x: float, y: float, is_active: bool):
    controller.view.canvas.create_text(x + 10, y - 10, text=f"({handle.point[0]:g}, {handle.point[1]:g})", anchor="sw", fill=HANDLE_FOCUS_COLOR if is_active else HANDLE_LABEL_COLOR, font=("Consolas", 9, "bold" if is_active else "normal"))


def compute_shape_bounds(shape):
    points = []
    for seg in shape.segments:
        points.append(seg.start)
        points.append(seg.end)
        points.extend(seg.controls)
    if not points:
        return None
    xs = [point[0] for point in points]
    ys = [point[1] for point in points]
    return min(xs), min(ys), max(xs), max(ys)


def current_shape_exceeds_viewbox(controller):
    view_box = controller.session.document.view_box
    shape = controller.session.current_shape
    if view_box is None or shape is None:
        return False
    bounds = compute_shape_bounds(shape)
    if bounds is None:
        return False
    min_x, min_y, width, height = view_box
    shape_min_x, shape_min_y, shape_max_x, shape_max_y = bounds
    return (
        shape_min_x < min_x
        or shape_min_y < min_y
        or shape_max_x > min_x + width
        or shape_max_y > min_y + height
    )


def draw_viewbox_size_hint(controller):
    view_box = controller.session.document.view_box
    if view_box is None:
        return
    min_x, min_y, width, height = view_box
    exceeds = current_shape_exceeds_viewbox(controller)
    text = f"viewBox: {width:g} x {height:g}"
    if exceeds:
        text += "  |  当前元素超出 viewBox"
    else:
        text += "  |  当前元素未超出 viewBox"

    canvas = controller.view.canvas
    canvas_w = max(1, canvas.winfo_width())
    canvas_h = max(1, canvas.winfo_height())
    x = canvas_w / 2
    y = canvas_h - 18
    text_id = canvas.create_text(
        x,
        y,
        text=text,
        anchor="s",
        fill=WARNING_TEXT_COLOR if exceeds else INFO_TEXT_COLOR,
        font=("Segoe UI", 9, "bold"),
    )
    bbox = canvas.bbox(text_id)
    if bbox is None:
        return
    pad_x = 10
    pad_y = 6
    bg_id = canvas.create_rectangle(
        bbox[0] - pad_x,
        bbox[1] - pad_y,
        bbox[2] + pad_x,
        bbox[3] + pad_y,
        fill=INFO_BG_COLOR,
        outline=VIEWBOX_WARNING_COLOR if exceeds else INFO_BORDER_COLOR,
        width=1,
    )
    canvas.tag_raise(text_id)


def draw_toast(controller):
    if not controller.state.toast_text:
        return
    canvas = controller.view.canvas
    x = 16
    y = 16
    pad_x = 10
    pad_y = 6
    text_id = canvas.create_text(x + pad_x, y + pad_y, text=controller.state.toast_text, anchor="nw", fill=TOAST_FG_COLOR, font=("Segoe UI", 10, "bold"))
    bbox = canvas.bbox(text_id)
    if bbox is None:
        return
    canvas.create_rectangle(bbox[0] - pad_x, bbox[1] - pad_y, bbox[2] + pad_x, bbox[3] + pad_y, fill=TOAST_BG_COLOR, outline="")
    canvas.tag_raise(text_id)
