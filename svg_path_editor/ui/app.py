import tkinter as tk

from ..application import EditorSession, InteractionState
from .views import EditorView, PreviewWindow
from .controllers import CanvasController, FileController, GuideController, PreviewController, ShortcutController, TextController
from . import rendering


class SVGPathEditor:
    def __init__(self, root: tk.Tk):
        self.root = root
        self.view = EditorView(root)
        self.preview_view = PreviewWindow(root)
        self.session = EditorSession()
        self.state = InteractionState()
        self._pan_origin = None

        self.file_controller = FileController(self)
        self.guide_controller = GuideController(self)
        self.text_controller = TextController(self)
        self.canvas_controller = CanvasController(self)
        self.preview_controller = PreviewController(self)
        self.shortcut_controller = ShortcutController(self)

        self._bind_events()

    def _bind_events(self):
        self.view.open_button.configure(command=self.file_controller.open_file)
        self.view.save_button.configure(command=self.file_controller.save_file)
        self.view.save_as_button.configure(command=self.file_controller.save_file_as)
        self.view.preview_button.configure(command=self.preview_controller.open_preview)
        self.view.apply_text_button.configure(command=self.text_controller.apply_text)
        self.view.reload_button.configure(command=self.file_controller.reload_selected_path)
        self.view.batch_replace_button.configure(command=self.text_controller.batch_replace_selected_value)
        self.view.add_guide_button.configure(command=self.guide_controller.add_guide_from_input)
        self.view.add_focus_x_button.configure(command=lambda: self.guide_controller.add_focus_guides("x"))
        self.view.add_focus_y_button.configure(command=lambda: self.guide_controller.add_focus_guides("y"))
        self.view.delete_guide_button.configure(command=self.guide_controller.delete_selected_guide)
        self.view.clear_guides_button.configure(command=self.guide_controller.clear_guides)

        self.view.path_combo.bind("<<ComboboxSelected>>", self.file_controller.on_path_selected)
        self.view.guide_listbox.bind("<<ListboxSelect>>", self.guide_controller.on_guide_selected)
        self.view.canvas.bind("<Configure>", lambda event: self.redraw())
        self.view.canvas.bind("<ButtonPress-1>", self.canvas_controller.on_left_down)
        self.view.canvas.bind("<B1-Motion>", self.canvas_controller.on_left_drag)
        self.view.canvas.bind("<ButtonRelease-1>", self.canvas_controller.on_left_up)
        self.view.canvas.bind("<MouseWheel>", self.canvas_controller.on_mousewheel)
        self.view.text.bind("<ButtonRelease-1>", self.text_controller.on_text_selection_changed)
        self.view.text.bind("<KeyRelease>", self.text_controller.on_text_key_release)
        self.shortcut_controller.bind_shortcuts()

    def redraw(self):
        rendering.redraw(self)
        self.preview_controller.redraw_if_open()

    def get_focus_handle_index(self) -> int | None:
        return self.text_controller.get_focus_handle_index()
