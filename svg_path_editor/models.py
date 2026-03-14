from dataclasses import dataclass, field


@dataclass
class PathToken:
    command: str
    values: list[float]


@dataclass
class Handle:
    kind: str
    point: list[float]
    segment_index: int
    role: str


@dataclass
class Segment:
    command: str
    start: tuple[float, float]
    end: tuple[float, float]
    controls: list[tuple[float, float]] = field(default_factory=list)
    closed: bool = False


@dataclass
class EditableShape:
    shape_type: str
    attribute_name: str
    raw_text: str
    segments: list[Segment]
