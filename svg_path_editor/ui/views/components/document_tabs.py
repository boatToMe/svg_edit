import tkinter as tk
from tkinter import ttk


TAB_SELECTED_BG = "#0f172a"
TAB_SELECTED_FG = "#f8fafc"
TAB_UNSELECTED_BG = "#cbd5e1"
TAB_UNSELECTED_FG = "#0f172a"
TAB_HOVER_BG = "#94a3b8"


class DocumentTabBar(ttk.Frame):
    def __init__(self, parent):
        super().__init__(parent, padding=(8, 0, 8, 8))
        self.current_index = -1
        self._labels: list[str] = []
        self._buttons: list[tk.Button] = []
        self._hover_index: int | None = None
        self._bar = tk.Frame(self, bg="#e2e8f0", bd=0, highlightthickness=0)
        self._bar.pack(fill="x")

    def add_tab_changed_handler(self, handler):
        self.bind("<<DocumentTabChanged>>", handler)

    def set_tabs(self, labels: list[str], current_index: int | None):
        if labels != self._labels:
            self._rebuild(labels)
        self.current_index = -1 if current_index is None else current_index
        self._refresh_styles()

    def get_selected_index(self) -> int | None:
        return self.current_index if self.current_index >= 0 else None

    def select(self, index: int, *, emit: bool = False):
        if index < 0 or index >= len(self._labels):
            return
        changed = self.current_index != index
        self.current_index = index
        self._refresh_styles()
        if emit and changed:
            self.event_generate("<<DocumentTabChanged>>")

    def _rebuild(self, labels: list[str]):
        self._labels = list(labels)
        for button in self._buttons:
            button.destroy()
        self._buttons.clear()
        for index, label in enumerate(labels):
            button = tk.Button(
                self._bar,
                text=label,
                bd=0,
                relief="flat",
                highlightthickness=0,
                padx=14,
                pady=6,
                cursor="hand2",
                command=lambda idx=index: self.select(idx, emit=True),
            )
            button.bind("<Enter>", lambda _event, idx=index: self._set_hover(idx))
            button.bind("<Leave>", lambda _event, idx=index: self._clear_hover(idx))
            button.pack(side="left", padx=(0, 4))
            self._buttons.append(button)

    def _set_hover(self, index: int):
        self._hover_index = index
        self._refresh_styles()

    def _clear_hover(self, index: int):
        if self._hover_index == index:
            self._hover_index = None
            self._refresh_styles()

    def _refresh_styles(self):
        for index, button in enumerate(self._buttons):
            if index == self.current_index:
                button.configure(
                    bg=TAB_SELECTED_BG,
                    fg=TAB_SELECTED_FG,
                    activebackground=TAB_SELECTED_BG,
                    activeforeground=TAB_SELECTED_FG,
                )
            elif index == self._hover_index:
                button.configure(
                    bg=TAB_HOVER_BG,
                    fg=TAB_UNSELECTED_FG,
                    activebackground=TAB_HOVER_BG,
                    activeforeground=TAB_UNSELECTED_FG,
                )
            else:
                button.configure(
                    bg=TAB_UNSELECTED_BG,
                    fg=TAB_UNSELECTED_FG,
                    activebackground=TAB_HOVER_BG,
                    activeforeground=TAB_UNSELECTED_FG,
                )
