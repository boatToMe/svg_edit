from xml.etree import ElementTree as ET
from tkinter import messagebox

from ...application import AddShapeCommand
from ...core import build_basic_shape_element, list_basic_shapes
from .base import BaseController


class ShapeController(BaseController):
    def __init__(self, app):
        super().__init__(app)
        self.shape_labels = dict(list_basic_shapes())

    def insert_basic_shape(self, shape_key: str):
        if self.session.document.root is None:
            return
        try:
            element = build_basic_shape_element(shape_key, self.session.document.view_box)
            element_xml = ET.tostring(element, encoding="unicode")
            command = AddShapeCommand(self.session, element_xml, self.shape_labels.get(shape_key, shape_key))
            self.session.history.execute(command)
        except Exception as exc:
            messagebox.showerror("插入图形失败", str(exc))
            return

        inserted_index = command.inserted_index
        if inserted_index is None:
            return
        self.view.set_element_labels(self.session.get_element_labels())
        self.app.current_document.clear_draft()
        self.app.file_controller.load_path(inserted_index, show_toast=False, refit=True)
        self.app.code_controller.refresh_code_view()
        self.view.set_status(f"已插入基础图形：{self.shape_labels.get(shape_key, shape_key)}。")
