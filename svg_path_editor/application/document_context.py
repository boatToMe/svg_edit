from dataclasses import dataclass, field

from .session import EditorSession
from .state import InteractionState


@dataclass
class DocumentContext:
    name: str
    session: EditorSession = field(default_factory=EditorSession)
    state: InteractionState = field(default_factory=InteractionState)
    draft_text: str = ""
    draft_index: int | None = None

    def remember_draft(self, index: int | None, text: str):
        self.draft_index = index
        self.draft_text = text

    def clear_draft(self):
        self.draft_index = None
        self.draft_text = ""
