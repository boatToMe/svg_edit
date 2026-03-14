from tkinter import ttk


class FlowRow:
    def __init__(self, parent, *, gap_x: int = 8, gap_y: int = 8):
        self.frame = ttk.Frame(parent)
        self.gap_x = gap_x
        self.gap_y = gap_y
        self._items: list[tuple[object, bool]] = []
        self._after_id = None
        self._pending_width: int | None = None
        self._last_layout_signature = None
        self._layout_running = False
        self._force_layout = False
        self.frame.bind("<Configure>", self._on_configure)

    def add(self, widget, *, stretch: bool = False):
        self._items.append((widget, stretch))
        self._schedule_layout(force=True)
        return widget

    def pack(self, **kwargs):
        self.frame.pack(**kwargs)

    def _on_configure(self, event=None):
        width = event.width if event is not None else self.frame.winfo_width()
        self._schedule_layout(width=width)

    def _schedule_layout(self, *, width: int | None = None, force: bool = False):
        if width is not None:
            self._pending_width = width
        if force:
            self._force_layout = True
        if self._after_id is None:
            self._after_id = self.frame.after_idle(self._layout)

    def _layout(self):
        self._after_id = None
        if self._layout_running:
            return

        width = self._pending_width if self._pending_width is not None else self.frame.winfo_width()
        if width <= 1:
            return

        item_widths = tuple(widget.winfo_reqwidth() for widget, _stretch in self._items)
        signature = (width, item_widths, len(self._items))
        if signature == self._last_layout_signature and not self._force_layout:
            return

        self._layout_running = True
        try:
            for child, _stretch in self._items:
                child.grid_forget()

            for column in range(len(self._items) + 1):
                self.frame.grid_columnconfigure(column, weight=0)

            row = 0
            column = 0
            row_width = 0
            row_items: list[tuple[object, bool, int]] = []

            for child, stretch in self._items:
                child_width = child.winfo_reqwidth()
                next_width = child_width if not row_items else row_width + self.gap_x + child_width
                if row_items and next_width > width:
                    self._apply_row(row_items, row)
                    row += 1
                    column = 0
                    row_width = 0
                    row_items = []
                    next_width = child_width
                row_items.append((child, stretch, column))
                row_width = next_width
                column += 1

            if row_items:
                self._apply_row(row_items, row)
        finally:
            self._layout_running = False
            self._force_layout = False
            self._last_layout_signature = signature

    def _apply_row(self, row_items, row: int):
        for child, stretch, column in row_items:
            padx = (0, self.gap_x) if column < len(row_items) - 1 else (0, 0)
            pady = (0, self.gap_y)
            child.grid(row=row, column=column, sticky="ew" if stretch else "w", padx=padx, pady=pady)
            self.frame.grid_columnconfigure(column, weight=1 if stretch else 0)
