import re

from .models import EditableShape, Handle, PathToken, Segment


TOKEN_RE = re.compile(r"[A-Za-z]|[-+]?(?:\d+\.\d+|\d+\.|\.\d+|\d+)(?:[eE][-+]?\d+)?")
COMMAND_SPECS = {
    "M": 2,
    "L": 2,
    "H": 1,
    "V": 1,
    "C": 6,
    "S": 4,
    "Q": 4,
    "T": 2,
    "Z": 0,
}


def format_num(value: float) -> str:
    if abs(value) < 1e-9:
        value = 0.0
    text = f"{value:.3f}".rstrip("0").rstrip(".")
    return text or "0"


def parse_points_text(points_text: str) -> list[tuple[float, float]]:
    values = [float(token) for token in TOKEN_RE.findall(points_text.replace(",", " "))]
    if len(values) % 2 != 0:
        raise ValueError("Polygon points must contain pairs of coordinates.")
    return [(values[idx], values[idx + 1]) for idx in range(0, len(values), 2)]


def points_to_text(points: list[tuple[float, float]]) -> str:
    return " ".join(f"{format_num(x)},{format_num(y)}" for x, y in points)


def line_to_text(points: list[tuple[float, float]]) -> str:
    if len(points) != 2:
        raise ValueError("Line must contain exactly 2 points.")
    return " ".join(format_num(value) for point in points for value in point)


def line_to_segments(x1: float, y1: float, x2: float, y2: float) -> list[Segment]:
    start = (x1, y1)
    end = (x2, y2)
    return [Segment("M", (0.0, 0.0), start), Segment("L", start, end)]


def polygon_to_segments(points: list[tuple[float, float]]) -> list[Segment]:
    if not points:
        return []
    segments = [Segment("M", (0.0, 0.0), points[0])]
    for start, end in zip(points, points[1:]):
        segments.append(Segment("L", start, end))
    if len(points) > 2:
        segments.append(Segment("Z", points[-1], points[0], closed=True))
    return segments


def segments_to_points(segments: list[Segment], closed: bool) -> list[tuple[float, float]]:
    points: list[tuple[float, float]] = []
    for seg in segments:
        if seg.command in {"M", "L"}:
            points.append((float(seg.end[0]), float(seg.end[1])))
    if closed and len(points) < 3:
        raise ValueError("Polygon needs at least 3 points.")
    return points


def parse_path_tokens(d_attr: str) -> list[PathToken]:
    raw = TOKEN_RE.findall(d_attr.replace(",", " "))
    if not raw:
        return []
    tokens: list[PathToken] = []
    i = 0
    current_cmd = None
    while i < len(raw):
        item = raw[i]
        if re.fullmatch(r"[A-Za-z]", item):
            current_cmd = item
            i += 1
        elif current_cmd is None:
            raise ValueError("Path data must start with a command.")

        if current_cmd is None:
            raise ValueError("Missing path command.")
        upper = current_cmd.upper()
        if upper not in COMMAND_SPECS:
            raise ValueError(f"Unsupported SVG path command: {current_cmd}")
        size = COMMAND_SPECS[upper]
        if upper == "Z":
            tokens.append(PathToken(current_cmd, []))
            current_cmd = None
            continue
        if i + size > len(raw):
            raise ValueError(f"Command {current_cmd} is missing parameters.")
        values = [float(raw[i + offset]) for offset in range(size)]
        tokens.append(PathToken(current_cmd, values))
        i += size

        while i < len(raw) and not re.fullmatch(r"[A-Za-z]", raw[i]):
            implied = "L" if upper == "M" else upper
            if COMMAND_SPECS[implied] == 0:
                break
            size = COMMAND_SPECS[implied]
            if i + size > len(raw):
                raise ValueError(f"Command {implied} is missing parameters.")
            values = [float(raw[i + offset]) for offset in range(size)]
            cmd = implied.lower() if current_cmd.islower() else implied
            tokens.append(PathToken(cmd, values))
            i += size
            upper = implied
    return tokens


def reflect_point(control, around):
    return (2 * around[0] - control[0], 2 * around[1] - control[1])


def tokens_to_segments(tokens: list[PathToken]) -> list[Segment]:
    segments: list[Segment] = []
    current = (0.0, 0.0)
    subpath_start = (0.0, 0.0)
    last_cubic_control = None
    last_quad_control = None

    for token in tokens:
        cmd = token.command
        upper = cmd.upper()
        relative = cmd.islower()
        vals = token.values

        def point_pair(ix):
            x = vals[ix]
            y = vals[ix + 1]
            if relative:
                return current[0] + x, current[1] + y
            return x, y

        if upper == "M":
            new_point = point_pair(0)
            segments.append(Segment("M", current, new_point))
            current = new_point
            subpath_start = new_point
            last_cubic_control = None
            last_quad_control = None
        elif upper == "L":
            end = point_pair(0)
            segments.append(Segment("L", current, end))
            current = end
            last_cubic_control = None
            last_quad_control = None
        elif upper == "H":
            x = vals[0] + current[0] if relative else vals[0]
            end = (x, current[1])
            segments.append(Segment("L", current, end))
            current = end
            last_cubic_control = None
            last_quad_control = None
        elif upper == "V":
            y = vals[0] + current[1] if relative else vals[0]
            end = (current[0], y)
            segments.append(Segment("L", current, end))
            current = end
            last_cubic_control = None
            last_quad_control = None
        elif upper == "C":
            c1 = point_pair(0)
            c2 = point_pair(2)
            end = point_pair(4)
            segments.append(Segment("C", current, end, [c1, c2]))
            current = end
            last_cubic_control = c2
            last_quad_control = None
        elif upper == "S":
            if last_cubic_control is None:
                c1 = current
            else:
                c1 = reflect_point(last_cubic_control, current)
            c2 = point_pair(0)
            end = point_pair(2)
            segments.append(Segment("C", current, end, [c1, c2]))
            current = end
            last_cubic_control = c2
            last_quad_control = None
        elif upper == "Q":
            c1 = point_pair(0)
            end = point_pair(2)
            segments.append(Segment("Q", current, end, [c1]))
            current = end
            last_quad_control = c1
            last_cubic_control = None
        elif upper == "T":
            if last_quad_control is None:
                c1 = current
            else:
                c1 = reflect_point(last_quad_control, current)
            end = point_pair(0)
            segments.append(Segment("Q", current, end, [c1]))
            current = end
            last_quad_control = c1
            last_cubic_control = None
        elif upper == "Z":
            segments.append(Segment("Z", current, subpath_start, closed=True))
            current = subpath_start
            last_cubic_control = None
            last_quad_control = None
        else:
            raise ValueError(f"Unsupported SVG path command: {cmd}")
    return segments


def segments_to_tokens(segments: list[Segment]) -> list[PathToken]:
    tokens: list[PathToken] = []
    for seg in segments:
        if seg.command == "M":
            tokens.append(PathToken("M", [seg.end[0], seg.end[1]]))
        elif seg.command == "L":
            tokens.append(PathToken("L", [seg.end[0], seg.end[1]]))
        elif seg.command == "Q":
            c1 = seg.controls[0]
            tokens.append(PathToken("Q", [c1[0], c1[1], seg.end[0], seg.end[1]]))
        elif seg.command == "C":
            c1, c2 = seg.controls
            tokens.append(PathToken("C", [c1[0], c1[1], c2[0], c2[1], seg.end[0], seg.end[1]]))
        elif seg.command == "Z":
            tokens.append(PathToken("Z", []))
    return tokens


def tokens_to_d(tokens: list[PathToken]) -> str:
    parts = []
    for token in tokens:
        if token.values:
            values = " ".join(format_num(v) for v in token.values)
            parts.append(f"{token.command}{values}")
        else:
            parts.append(token.command)
    return " ".join(parts)


def element_to_shape(element) -> EditableShape:
    tag = element.tag.split("}", 1)[-1]
    if tag == "path":
        raw_text = element.get("d", "")
        return EditableShape("path", "d", raw_text, tokens_to_segments(parse_path_tokens(raw_text)))
    if tag == "line":
        x1 = float(element.get("x1", "0"))
        y1 = float(element.get("y1", "0"))
        x2 = float(element.get("x2", "0"))
        y2 = float(element.get("y2", "0"))
        points = [(x1, y1), (x2, y2)]
        return EditableShape("line", "line", line_to_text(points), line_to_segments(x1, y1, x2, y2))
    if tag == "polygon":
        raw_text = element.get("points", "")
        return EditableShape("polygon", "points", raw_text, polygon_to_segments(parse_points_text(raw_text)))
    raise ValueError(f"Unsupported SVG element: {tag}")


def text_to_shape(shape_type: str, raw_text: str) -> EditableShape:
    if shape_type == "path":
        tokens = parse_path_tokens(raw_text)
        return EditableShape(shape_type, "d", raw_text, tokens_to_segments(tokens))
    if shape_type == "line":
        values = [float(token) for token in TOKEN_RE.findall(raw_text.replace(",", " "))]
        if len(values) != 4:
            raise ValueError("Line text must contain exactly 4 numbers: x1 y1 x2 y2")
        points = [(values[0], values[1]), (values[2], values[3])]
        return EditableShape(shape_type, "line", line_to_text(points), line_to_segments(*values))
    if shape_type == "polygon":
        points = parse_points_text(raw_text)
        return EditableShape(shape_type, "points", points_to_text(points), polygon_to_segments(points))
    raise ValueError(f"Unsupported SVG element: {shape_type}")


def apply_shape_to_element(element, shape: EditableShape):
    if shape.shape_type == "path":
        element.set("d", tokens_to_d(segments_to_tokens(shape.segments)))
        return
    if shape.shape_type == "line":
        points = segments_to_points(shape.segments, closed=False)
        if len(points) != 2:
            raise ValueError("Line must contain exactly 2 points.")
        (x1, y1), (x2, y2) = points
        element.set("x1", format_num(x1))
        element.set("y1", format_num(y1))
        element.set("x2", format_num(x2))
        element.set("y2", format_num(y2))
        return
    if shape.shape_type == "polygon":
        points = segments_to_points(shape.segments, closed=True)
        element.set("points", points_to_text(points))
        return
    raise ValueError(f"Unsupported SVG element: {shape.shape_type}")


def shape_to_text(shape_type: str, segments: list[Segment]) -> str:
    if shape_type == "path":
        return tokens_to_d(segments_to_tokens(segments))
    if shape_type == "line":
        return line_to_text(segments_to_points(segments, closed=False))
    if shape_type == "polygon":
        return points_to_text(segments_to_points(segments, closed=True))
    raise ValueError(f"Unsupported SVG element: {shape_type}")


def build_handles(segments: list[Segment]) -> list[Handle]:
    handles: list[Handle] = []
    for idx, seg in enumerate(segments):
        if seg.command == "M":
            handles.append(Handle("anchor", [seg.end[0], seg.end[1]], idx, "move"))
            continue
        if seg.command in {"L", "Q", "C", "Z"}:
            if seg.command in {"Q", "C"}:
                for c_index, control in enumerate(seg.controls):
                    handles.append(
                        Handle("control", [control[0], control[1]], idx, f"c{c_index + 1}")
                    )
            if seg.command != "Z":
                handles.append(Handle("anchor", [seg.end[0], seg.end[1]], idx, "end"))
    attach_handle_lists(segments, handles)
    return handles


def attach_handle_lists(segments: list[Segment], handles: list[Handle]):
    anchors_by_segment = {}
    for handle in handles:
        if handle.kind == "anchor":
            anchors_by_segment[handle.segment_index] = handle

    current_move_anchor = None
    for idx, seg in enumerate(segments):
        if seg.command == "M":
            current_move_anchor = anchors_by_segment.get(idx)
            if current_move_anchor is not None:
                seg.end = current_move_anchor.point
            seg.start = segments[idx - 1].end if idx > 0 else (0.0, 0.0)
            continue

        if seg.command in {"L", "Q", "C"}:
            anchor = anchors_by_segment.get(idx)
            if anchor is not None:
                seg.end = anchor.point
        if seg.command in {"Q", "C"}:
            seg.controls = [h.point for h in handles if h.segment_index == idx and h.kind == "control"]
        if idx > 0:
            prev_anchor = anchors_by_segment.get(idx - 1)
            if prev_anchor is not None:
                seg.start = prev_anchor.point
            elif segments[idx - 1].command == "Z":
                seg.start = segments[idx - 1].end
        if seg.command == "Z" and current_move_anchor is not None:
            seg.end = current_move_anchor.point


def approximate_quadratic(p0, p1, p2, steps=24):
    points = []
    for idx in range(steps + 1):
        t = idx / steps
        mt = 1 - t
        x = mt * mt * p0[0] + 2 * mt * t * p1[0] + t * t * p2[0]
        y = mt * mt * p0[1] + 2 * mt * t * p1[1] + t * t * p2[1]
        points.append((x, y))
    return points


def approximate_cubic(p0, p1, p2, p3, steps=32):
    points = []
    for idx in range(steps + 1):
        t = idx / steps
        mt = 1 - t
        x = (
            mt * mt * mt * p0[0]
            + 3 * mt * mt * t * p1[0]
            + 3 * mt * t * t * p2[0]
            + t * t * t * p3[0]
        )
        y = (
            mt * mt * mt * p0[1]
            + 3 * mt * mt * t * p1[1]
            + 3 * mt * t * t * p2[1]
            + t * t * t * p3[1]
        )
        points.append((x, y))
    return points
