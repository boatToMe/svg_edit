from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from pathlib import Path

from ..models import EditableShape, Handle, PathToken, Segment
from ..path_ops import apply_shape_to_element, build_handles, element_to_shape, segments_to_tokens, text_to_shape
from ..svg_document import SVGPathDocument


class EditorCommand(ABC):
    label = "编辑操作"

    @abstractmethod
    def execute(self) -> None:
        pass

    @abstractmethod
    def undo(self) -> None:
        pass


class HistoryManager:
    def __init__(self):
        self.past: list[EditorCommand] = []
        self.future: list[EditorCommand] = []

    def reset(self):
        self.past.clear()
        self.future.clear()

    def execute(self, command: EditorCommand) -> None:
        command.execute()
        self.past.append(command)
        self.future.clear()

    def push_executed(self, command: EditorCommand) -> None:
        self.past.append(command)
        self.future.clear()

    def can_undo(self) -> bool:
        return bool(self.past)

    def can_redo(self) -> bool:
        return bool(self.future)

    def undo(self) -> EditorCommand | None:
        if not self.past:
            return None
        command = self.past.pop()
        command.undo()
        self.future.append(command)
        return command

    def redo(self) -> EditorCommand | None:
        if not self.future:
            return None
        command = self.future.pop()
        command.execute()
        self.past.append(command)
        return command


@dataclass
class InteractionState:
    active_handle: Handle | None = None
    focus_handle: Handle | None = None
    selected_guide_index: int | None = None
    active_guide_index: int | None = None
    scale: float = 1.0
    offset_x: float = 40.0
    offset_y: float = 40.0
    padding: float = 40.0
    custom_guides: list[tuple[str, float]] = field(default_factory=list)
    toast_text: str | None = None
    toast_after_id: str | None = None
    drag_shape_before_text: str | None = None
    drag_guide_before_value: float | None = None
    handle_text_spans: list[dict] = field(default_factory=list)
    text_selected_handle_indices: set[int] = field(default_factory=set)
    is_space_pressed: bool = False


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


class UpdateShapeCommand(EditorCommand):
    label = "更新图形"

    def __init__(self, session: EditorSession, index: int, before_text: str, after_text: str):
        self.session = session
        self.index = index
        self.before_text = before_text
        self.after_text = after_text

    def execute(self) -> None:
        self.session.apply_shape_text(self.index, self.after_text)

    def undo(self) -> None:
        self.session.apply_shape_text(self.index, self.before_text)


class AddGuideCommand(EditorCommand):
    label = "添加辅助线"

    def __init__(self, state: InteractionState, axis: str, value: float):
        self.state = state
        self.axis = axis
        self.value = float(value)
        self.insert_index: int | None = None

    def execute(self) -> None:
        if self.insert_index is None:
            self.insert_index = len(self.state.custom_guides)
        self.state.custom_guides.insert(self.insert_index, (self.axis, self.value))
        self.state.selected_guide_index = self.insert_index
        self.state.active_guide_index = None

    def undo(self) -> None:
        if self.insert_index is None:
            return
        self.state.custom_guides.pop(self.insert_index)
        self.state.selected_guide_index = None
        self.state.active_guide_index = None


class DeleteGuideCommand(EditorCommand):
    label = "删除辅助线"

    def __init__(self, state: InteractionState, index: int):
        self.state = state
        self.index = index
        self.removed_guide: tuple[str, float] | None = None

    def execute(self) -> None:
        self.removed_guide = self.state.custom_guides.pop(self.index)
        self.state.selected_guide_index = None
        self.state.active_guide_index = None

    def undo(self) -> None:
        if self.removed_guide is None:
            return
        self.state.custom_guides.insert(self.index, self.removed_guide)
        self.state.selected_guide_index = self.index
        self.state.active_guide_index = None


class ClearGuidesCommand(EditorCommand):
    label = "清空辅助线"

    def __init__(self, state: InteractionState):
        self.state = state
        self.previous_guides = list(state.custom_guides)

    def execute(self) -> None:
        self.state.custom_guides.clear()
        self.state.selected_guide_index = None
        self.state.active_guide_index = None

    def undo(self) -> None:
        self.state.custom_guides[:] = self.previous_guides
        self.state.selected_guide_index = None
        self.state.active_guide_index = None


class MoveGuideCommand(EditorCommand):
    label = "移动辅助线"

    def __init__(self, state: InteractionState, index: int, before_value: float, after_value: float):
        self.state = state
        self.index = index
        self.before_value = float(before_value)
        self.after_value = float(after_value)

    def execute(self) -> None:
        axis, _ = self.state.custom_guides[self.index]
        self.state.custom_guides[self.index] = (axis, self.after_value)
        self.state.selected_guide_index = self.index
        self.state.active_guide_index = None

    def undo(self) -> None:
        axis, _ = self.state.custom_guides[self.index]
        self.state.custom_guides[self.index] = (axis, self.before_value)
        self.state.selected_guide_index = self.index
        self.state.active_guide_index = None
