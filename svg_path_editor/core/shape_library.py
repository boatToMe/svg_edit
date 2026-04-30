from xml.etree import ElementTree as ET

from .svg_document import SVG_NS


DEFAULT_STROKE = "#0f172a"
DEFAULT_STROKE_WIDTH = "6"
DEFAULT_LINEJOIN = "round"
DEFAULT_LINECAP = "round"

BASIC_SHAPES: tuple[tuple[str, str], ...] = (
    ("line", "直线"),
    ("triangle", "三角形"),
    ("rectangle", "矩形"),
    ("diamond", "菱形"),
    ("arrow", "箭头"),
)


def _format_svg_value(value: float) -> str:
    if abs(value - round(value)) < 1e-6:
        return str(int(round(value)))
    return f"{value:.3f}".rstrip("0").rstrip(".")


def _shape_attributes(**attrs) -> dict[str, str]:
    result: dict[str, str] = {}
    for key, value in attrs.items():
        if isinstance(value, (int, float)):
            result[key] = _format_svg_value(float(value))
        else:
            result[key] = str(value)
    return result


def _get_view_box(view_box: tuple[float, float, float, float] | None) -> tuple[float, float, float, float]:
    if view_box is None:
        return (0.0, 0.0, 512.0, 512.0)
    return view_box


def list_basic_shapes() -> tuple[tuple[str, str], ...]:
    return BASIC_SHAPES


def build_basic_shape_element(shape_key: str, view_box: tuple[float, float, float, float] | None = None) -> ET.Element:
    min_x, min_y, width, height = _get_view_box(view_box)
    left = min_x + width * 0.2
    right = min_x + width * 0.8
    top = min_y + height * 0.2
    bottom = min_y + height * 0.8
    center_x = min_x + width * 0.5
    center_y = min_y + height * 0.5

    common = {
        "fill": "none",
        "stroke": DEFAULT_STROKE,
        "stroke-width": DEFAULT_STROKE_WIDTH,
        "stroke-linejoin": DEFAULT_LINEJOIN,
        "stroke-linecap": DEFAULT_LINECAP,
    }

    if shape_key == "line":
        return ET.Element(
            f"{{{SVG_NS}}}line",
            _shape_attributes(
                x1=left,
                y1=center_y,
                x2=right,
                y2=center_y,
                stroke=DEFAULT_STROKE,
                **{"stroke-width": DEFAULT_STROKE_WIDTH, "stroke-linecap": DEFAULT_LINECAP},
            ),
        )

    if shape_key == "triangle":
        points = [
            (center_x, top),
            (right, bottom),
            (left, bottom),
        ]
        return ET.Element(
            f"{{{SVG_NS}}}polygon",
            _shape_attributes(points=" ".join(f"{_format_svg_value(x)},{_format_svg_value(y)}" for x, y in points), **common),
        )

    if shape_key == "rectangle":
        points = [
            (left, top),
            (right, top),
            (right, bottom),
            (left, bottom),
        ]
        return ET.Element(
            f"{{{SVG_NS}}}polygon",
            _shape_attributes(points=" ".join(f"{_format_svg_value(x)},{_format_svg_value(y)}" for x, y in points), **common),
        )

    if shape_key == "diamond":
        points = [
            (center_x, min_y + height * 0.12),
            (min_x + width * 0.88, center_y),
            (center_x, min_y + height * 0.88),
            (min_x + width * 0.12, center_y),
        ]
        return ET.Element(
            f"{{{SVG_NS}}}polygon",
            _shape_attributes(points=" ".join(f"{_format_svg_value(x)},{_format_svg_value(y)}" for x, y in points), **common),
        )

    if shape_key == "arrow":
        arrow_head_x = min_x + width * 0.78
        shaft_start_x = min_x + width * 0.18
        shaft_end_x = min_x + width * 0.56
        half_thickness = height * 0.09
        head_half_height = height * 0.22
        path_data = (
            f"M{_format_svg_value(shaft_start_x)} {_format_svg_value(center_y - half_thickness)} "
            f"L{_format_svg_value(shaft_end_x)} {_format_svg_value(center_y - half_thickness)} "
            f"L{_format_svg_value(shaft_end_x)} {_format_svg_value(center_y - head_half_height)} "
            f"L{_format_svg_value(arrow_head_x)} {_format_svg_value(center_y)} "
            f"L{_format_svg_value(shaft_end_x)} {_format_svg_value(center_y + head_half_height)} "
            f"L{_format_svg_value(shaft_end_x)} {_format_svg_value(center_y + half_thickness)} "
            f"L{_format_svg_value(shaft_start_x)} {_format_svg_value(center_y + half_thickness)} Z"
        )
        return ET.Element(
            f"{{{SVG_NS}}}path",
            _shape_attributes(d=path_data, **common),
        )

    raise ValueError(f"Unsupported basic shape: {shape_key}")
