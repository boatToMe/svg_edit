from pathlib import Path

from ..core import (
    EditableShape,
    PathToken,
    Segment,
    SVGPathDocument,
    apply_shape_to_element,
    build_handles,
    element_to_shape,
    segments_to_tokens,
    text_to_shape,
)
from .history import HistoryManager


class EditorSession:
    def __init__(self):
        self.document = SVGPathDocument()
        self.history = HistoryManager()
        self.current_index: int | None = None
        self.current_shape: EditableShape | None = None
        self.current_tokens: list[PathToken] = []
        self.current_segments: list[Segment] = []
        self.handles = []

    def open_file(self, file_path: Path):
        self.document.load(file_path)
        self.history.reset()
        self.current_index = None
        self.current_shape = None
        self.current_tokens = []
        self.current_segments = []
        self.handles = []
        return [f"元素{idx + 1}（{elem.tag.split('}', 1)[-1]}）" for idx, elem in enumerate(self.document.editable_elements)]

    def save(self, file_path: Path | None = None):
        self.document.save(file_path)

    def _set_active_shape(self, index: int, shape: EditableShape) -> EditableShape:
        self.current_index = index
        self.current_shape = shape
        self.current_tokens = segments_to_tokens(shape.segments) if shape.shape_type == "path" else []
        self.current_segments = shape.segments
        self.handles = build_handles(shape.segments)
        return shape

    def load_shape(self, index: int) -> EditableShape:
        if index < 0 or index >= len(self.document.editable_elements):
            raise IndexError(index)
        return self._set_active_shape(index, element_to_shape(self.document.editable_elements[index]))

    def get_shape_text(self, index: int) -> str:
        if index == self.current_index and self.current_shape is not None:
            return self.current_shape.raw_text
        return element_to_shape(self.document.editable_elements[index]).raw_text

    def apply_shape_text(self, index: int, raw_text: str) -> EditableShape:
        if index < 0 or index >= len(self.document.editable_elements):
            raise IndexError(index)
        if index == self.current_index and self.current_shape is not None:
            shape_type = self.current_shape.shape_type
        else:
            shape_type = element_to_shape(self.document.editable_elements[index]).shape_type
        shape = text_to_shape(shape_type, raw_text)
        apply_shape_to_element(self.document.editable_elements[index], shape)
        if index == self.current_index:
            self._set_active_shape(index, shape)
        return shape

    def commit_text(self, raw_text: str) -> EditableShape:
        if self.current_index is None or self.current_shape is None:
            raise RuntimeError("No active shape.")
        return self.apply_shape_text(self.current_index, raw_text)

    def sync_shape_from_segments(self, shape_text: str):
        if self.current_index is None or self.current_shape is None:
            return
        self.current_shape.raw_text = shape_text
        self.current_tokens = segments_to_tokens(self.current_segments) if self.current_shape.shape_type == "path" else []
        apply_shape_to_element(self.document.editable_elements[self.current_index], self.current_shape)

    def get_display_shapes(self):
        shapes: list[tuple[int, EditableShape]] = []
        for idx, elem in enumerate(self.document.editable_elements):
            if idx == self.current_index and self.current_shape is not None:
                shapes.append((idx, self.current_shape))
            else:
                try:
                    shapes.append((idx, element_to_shape(elem)))
                except Exception:
                    continue
        return shapes

    def get_element_name(self, index: int) -> str:
        return f"元素{index + 1}"
