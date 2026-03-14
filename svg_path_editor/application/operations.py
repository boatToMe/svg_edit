from .commands import EditorCommand
from .session import EditorSession
from .state import InteractionState


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
