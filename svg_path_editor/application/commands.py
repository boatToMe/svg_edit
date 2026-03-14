from abc import ABC, abstractmethod


class EditorCommand(ABC):
    label = "编辑操作"

    @abstractmethod
    def execute(self) -> None:
        pass

    @abstractmethod
    def undo(self) -> None:
        pass
