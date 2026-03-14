from .base import BaseController


class ShortcutController(BaseController):
    def bind_shortcuts(self):
        self.root.bind_all("<Control-z>", self.app.canvas_controller.on_undo)
        self.root.bind_all("<Control-y>", self.app.canvas_controller.on_redo)
        self.root.bind_all("<Control-Key-0>", self.on_open_file)
        self.root.bind_all("<KeyPress-space>", self.app.canvas_controller.on_space_press)
        self.root.bind_all("<KeyRelease-space>", self.app.canvas_controller.on_space_release)

    def on_open_file(self, _event=None):
        self.app.file_controller.open_file()
        return "break"
