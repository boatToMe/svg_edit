from ...core import approximate_cubic, approximate_quadratic, element_to_shape
from ..constants import ALL_SHAPES_COLOR, SELECTED_SHAPE_COLOR
from .styles import corner_radius, merge_style_overrides, normalize_color, parse_style_rules, resolve_style, stroke_width


LOW_RES_PREVIEW_WIDTH = 64
LOW_RES_SCALE_THRESHOLD = 1.5


class PreviewRenderer:
    def __init__(self, strip_ns):
        self.strip_ns = strip_ns

    def get_bounds(self, session):
        if session.document.view_box is not None:
            return session.document.view_box
        points = []
        for _idx, shape in session.get_display_shapes():
            for seg in shape.segments:
                points.append(seg.start)
                points.append(seg.end)
                points.extend(seg.controls)
        if not points:
            return (0.0, 0.0, 512.0, 512.0)
        xs = [point[0] for point in points]
        ys = [point[1] for point in points]
        min_x = min(xs)
        min_y = min(ys)
        return (min_x, min_y, max(1.0, max(xs) - min_x), max(1.0, max(ys) - min_y))

    def redraw(self, preview, session, theme_style, target_width, global_style_override, element_style_overrides, flash_color, is_flash_on):
        if preview.canvas is None:
            return
        min_x, min_y, width, height = self.get_bounds(session)
        width_px = max(1, int(target_width))
        height_px = max(1, int(round(width_px * height / max(width, 1.0))))
        scale = width_px / max(width, 1.0)
        low_res_mode = width_px <= LOW_RES_PREVIEW_WIDTH or scale <= LOW_RES_SCALE_THRESHOLD
        preview.resize_canvas(width_px, height_px)
        preview.update_size_label(width_px, height_px)

        canvas = preview.canvas
        canvas.update_idletasks()
        canvas_width = max(width_px, canvas.winfo_width())
        canvas_height = max(height_px, canvas.winfo_height())
        offset_x = (canvas_width - width_px) / 2
        offset_y = (canvas_height - height_px) / 2

        canvas.delete("all")
        canvas.configure(
            background=theme_style["background"],
            highlightbackground=theme_style["border"],
            scrollregion=(0, 0, canvas_width, canvas_height),
        )

        style_rules = parse_style_rules(session.document.root, self.strip_ns)
        for index, element in enumerate(session.document.editable_elements):
            try:
                shape = session.current_shape if index == session.current_index and session.current_shape is not None else element_to_shape(element)
            except Exception:
                continue
            style = resolve_style(element, style_rules)
            style = merge_style_overrides(style, global_style_override, element_style_overrides.get(index))
            self._draw_shape(
                canvas,
                shape,
                style,
                min_x,
                min_y,
                scale,
                offset_x,
                offset_y,
                selected=index == session.current_index,
                flash=is_flash_on(index),
                flash_color=flash_color,
                low_res_mode=low_res_mode,
            )

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

    def _pixel_snap(self, value: float, for_stroke: bool) -> float:
        return round(value) + 0.5 if for_stroke else round(value)

    def _to_canvas_points(self, points, min_x, min_y, scale, offset_x, offset_y, low_res_mode: bool, for_stroke: bool):
        flat = []
        for x, y in points:
            canvas_x = ((x - min_x) * scale) + offset_x
            canvas_y = ((y - min_y) * scale) + offset_y
            if low_res_mode:
                canvas_x = self._pixel_snap(canvas_x, for_stroke)
                canvas_y = self._pixel_snap(canvas_y, for_stroke)
            flat.extend((canvas_x, canvas_y))
        return flat

    def _draw_shape(self, canvas, shape, style, min_x, min_y, scale, offset_x, offset_y, selected: bool, flash: bool, flash_color: str, low_res_mode: bool):
        fallback_fill = "#111827" if shape.shape_type in {"path", "polygon"} else ""
        fallback_stroke = "#111827" if shape.shape_type == "line" else ""
        fill = normalize_color(style.get("fill"), fallback_fill)
        stroke = normalize_color(style.get("stroke"), fallback_stroke)
        scaled_stroke_width = stroke_width(style, scale)
        scaled_corner_radius = corner_radius(style, scale)
        if flash:
            stroke = flash_color
            if fill:
                fill = flash_color
        elif selected and not stroke and not fill:
            stroke = SELECTED_SHAPE_COLOR
        elif not selected and not stroke and not fill:
            stroke = ALL_SHAPES_COLOR

        if low_res_mode:
            scaled_stroke_width = max(1.0, round(scaled_stroke_width))
            scaled_corner_radius = 0.0

        smooth = scaled_corner_radius > 0
        smooth_steps = max(8, int(scaled_corner_radius)) if smooth else 12

        for points, closed in self._shape_subpaths(shape):
            if len(points) < 2:
                continue
            if closed:
                flat = self._to_canvas_points(points, min_x, min_y, scale, offset_x, offset_y, low_res_mode, False)
                canvas.create_polygon(
                    *flat,
                    fill=fill or "",
                    outline=stroke or "",
                    width=scaled_stroke_width if stroke else 1,
                    joinstyle=style.get("stroke-linejoin", "round"),
                    smooth=smooth,
                    splinesteps=smooth_steps,
                )
            else:
                flat = self._to_canvas_points(points, min_x, min_y, scale, offset_x, offset_y, low_res_mode, True)
                line_color = stroke or fill or "#111827"
                canvas.create_line(
                    *flat,
                    fill=line_color,
                    width=scaled_stroke_width,
                    capstyle=style.get("stroke-linecap", "round"),
                    joinstyle=style.get("stroke-linejoin", "round"),
                    smooth=smooth,
                    splinesteps=smooth_steps,
                )
