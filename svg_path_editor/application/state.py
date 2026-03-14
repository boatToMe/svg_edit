from dataclasses import dataclass, field

from ..core import Handle


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
