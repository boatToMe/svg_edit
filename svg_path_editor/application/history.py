from .commands import EditorCommand


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
