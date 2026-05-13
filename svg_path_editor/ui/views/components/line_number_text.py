import tkinter as tk
from tkinter import ttk

LINE_BG = "#f1f5f9"
LINE_FG = "#64748b"
TEXT_BG = "#ffffff"


class LineNumberText:
    def __init__(self, parent, *, font=("Consolas", 10), wrap="char", state="normal", show_line_numbers=True):
        self.frame = ttk.Frame(parent)
        self._show_line_numbers = show_line_numbers

        self.line_numbers = tk.Text(
            self.frame, width=4, padx=4, pady=2,
            bg=LINE_BG, fg=LINE_FG, font=font,
            state="disabled", takefocus=0, relief="flat", bd=0,
            highlightthickness=0,
        )
        self.text = tk.Text(
            self.frame, wrap=wrap, font=font, state=state,
            padx=4, pady=2, bg=TEXT_BG,
        )
        self.scrollbar = ttk.Scrollbar(self.frame, orient="vertical", command=self._on_scroll)

        self.text.configure(yscrollcommand=self._on_text_scroll)
        self.line_numbers.configure(yscrollcommand=self._on_text_scroll)

        if show_line_numbers:
            self.line_numbers.pack(side="left", fill="y")
        self.text.pack(side="left", fill="both", expand=True)
        self.scrollbar.pack(side="right", fill="y")

        self.text.bind("<KeyRelease>", lambda e: self._update_line_numbers())
        self.text.bind("<MouseWheel>", lambda e: self._update_line_numbers())
        self.frame.bind("<Configure>", lambda e: self._update_line_numbers())

    def _on_scroll(self, *args):
        self.text.yview(*args)
        self.line_numbers.yview(*args)

    def _on_text_scroll(self, first, last):
        self.scrollbar.set(first, last)
        self.line_numbers.yview_moveto(first)

    def _update_line_numbers(self):
        if not self._show_line_numbers:
            return
        self.line_numbers.configure(state="normal")
        self.line_numbers.delete("1.0", "end")
        line_count = int(self.text.index("end-1c").split(".")[0])
        line_numbers_text = "\n".join(str(i) for i in range(1, line_count + 1))
        self.line_numbers.insert("1.0", line_numbers_text)
        self.line_numbers.configure(state="disabled")

    def set_show_line_numbers(self, show: bool):
        self._show_line_numbers = show
        if show:
            self.line_numbers.pack(side="left", fill="y", before=self.text)
            self._update_line_numbers()
        else:
            self.line_numbers.pack_forget()

    def get_show_line_numbers(self) -> bool:
        return self._show_line_numbers

    def set_text(self, text: str, *, state="normal"):
        self.text.configure(state="normal")
        self.text.delete("1.0", "end")
        self.text.insert("1.0", text)
        self.text.configure(state=state)
        self._update_line_numbers()

    def get_text(self) -> str:
        return self.text.get("1.0", "end").strip()

    def configure(self, **kwargs):
        if "state" in kwargs:
            self.text.configure(state=kwargs["state"])
