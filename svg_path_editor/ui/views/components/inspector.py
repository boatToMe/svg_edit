import tkinter as tk
from tkinter import ttk

from .flow import FlowRow


HELP_TEXT = (
    "画布会同时显示全部可编辑元素\n"
    "当前元素高亮，节点可拖动\n"
    "拖动会按编辑设置里的步长吸附\n"
    "按住空格并左键拖动可移动画布\n"
    "节点拖动后可用 Ctrl+Z 撤销、Ctrl+Y 重做\n"
    "选中几何数据区数字时会高亮对应端点\n"
    "可对选中的同值数字做批量替换\n"
    "左侧预览区会实时显示渲染效果"
)


class InspectorSidebar:
    def __init__(self, parent, guide_axis_var: tk.StringVar, guide_value_var: tk.StringVar, drag_step_var: tk.StringVar):
        self.frame = ttk.Frame(parent)
        self.text = None
        self.apply_text_button = None
        self.reload_button = None
        self.batch_replace_button = None
        self.drag_step_entry = None
        self.guide_axis_combo = None
        self.guide_value_entry = None
        self.add_guide_button = None
        self.add_focus_x_button = None
        self.add_focus_y_button = None
        self.delete_guide_button = None
        self.clear_guides_button = None
        self.guide_listbox = None
        self._build(guide_axis_var, guide_value_var, drag_step_var)

    def _build(self, guide_axis_var: tk.StringVar, guide_value_var: tk.StringVar, drag_step_var: tk.StringVar):
        self.frame.pack(fill="both", expand=True)

        geometry_box = ttk.LabelFrame(self.frame, text="几何数据", padding=8)
        geometry_box.pack(fill="x")
        self.text = tk.Text(geometry_box, wrap="word", font=("Consolas", 11), height=7)
        self.text.pack(fill="x", expand=False)
        self.text.tag_configure("number_default", foreground="#0f172a")
        self.text.tag_configure("number_focus", foreground="#2563eb")
        self.text.tag_configure("number_selected", foreground="#dc2626")
        text_buttons = FlowRow(geometry_box)
        text_buttons.pack(fill="x", pady=(8, 0))
        self.apply_text_button = ttk.Button(text_buttons.frame, text="应用文本")
        self.reload_button = ttk.Button(text_buttons.frame, text="重新载入")
        self.batch_replace_button = ttk.Button(text_buttons.frame, text="批量修改同值")
        text_buttons.add(self.apply_text_button)
        text_buttons.add(self.reload_button)
        text_buttons.add(self.batch_replace_button)

        editor_box = ttk.LabelFrame(self.frame, text="编辑设置", padding=8)
        editor_box.pack(fill="x", pady=(8, 0))
        step_row = FlowRow(editor_box)
        step_row.pack(fill="x")
        step_row.add(ttk.Label(step_row.frame, text="拖动步长"))
        self.drag_step_entry = ttk.Entry(step_row.frame, textvariable=drag_step_var, width=10)
        step_row.add(self.drag_step_entry)
        step_row.add(ttk.Label(step_row.frame, text="px"))
        ttk.Label(editor_box, text="端点和辅助线拖动都会按这个步长吸附。", justify="left").pack(anchor="w", pady=(8, 0))

        guide_box = ttk.LabelFrame(self.frame, text="辅助线", padding=8)
        guide_box.pack(fill="x", pady=(8, 0))
        guide_input = FlowRow(guide_box)
        guide_input.pack(fill="x")
        guide_input.add(ttk.Label(guide_input.frame, text="方向"))
        self.guide_axis_combo = ttk.Combobox(guide_input.frame, textvariable=guide_axis_var, values=["x", "y"], width=4, state="readonly")
        guide_input.add(self.guide_axis_combo)
        guide_input.add(ttk.Label(guide_input.frame, text="位置"))
        self.guide_value_entry = ttk.Entry(guide_input.frame, textvariable=guide_value_var, width=10)
        guide_input.add(self.guide_value_entry)
        self.add_guide_button = ttk.Button(guide_input.frame, text="添加辅助线")
        guide_input.add(self.add_guide_button)

        guide_actions = FlowRow(guide_box)
        guide_actions.pack(fill="x", pady=(8, 0))
        self.add_focus_x_button = ttk.Button(guide_actions.frame, text="添加焦点 X")
        self.add_focus_y_button = ttk.Button(guide_actions.frame, text="添加焦点 Y")
        self.delete_guide_button = ttk.Button(guide_actions.frame, text="删除选中辅助线")
        self.clear_guides_button = ttk.Button(guide_actions.frame, text="清空辅助线")
        guide_actions.add(self.add_focus_x_button)
        guide_actions.add(self.add_focus_y_button)
        guide_actions.add(self.delete_guide_button)
        guide_actions.add(self.clear_guides_button)

        list_frame = ttk.Frame(guide_box)
        list_frame.pack(fill="x", pady=(8, 0))
        self.guide_listbox = tk.Listbox(list_frame, height=6, exportselection=False)
        self.guide_listbox.pack(side="left", fill="x", expand=True)
        guide_scrollbar = ttk.Scrollbar(list_frame, orient="vertical", command=self.guide_listbox.yview)
        guide_scrollbar.pack(side="right", fill="y")
        self.guide_listbox.configure(yscrollcommand=guide_scrollbar.set)

        help_box = ttk.LabelFrame(self.frame, text="提示", padding=8)
        help_box.pack(fill="x", pady=(8, 0))
        ttk.Label(help_box, text=HELP_TEXT, justify="left").pack(anchor="w")
