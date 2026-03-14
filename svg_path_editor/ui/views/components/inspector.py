import tkinter as tk
from tkinter import ttk


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
        text_buttons = ttk.Frame(geometry_box)
        text_buttons.pack(fill="x", pady=(8, 0))
        self.apply_text_button = ttk.Button(text_buttons, text="应用文本")
        self.apply_text_button.pack(side="left")
        self.reload_button = ttk.Button(text_buttons, text="重新载入")
        self.reload_button.pack(side="left", padx=(8, 0))
        self.batch_replace_button = ttk.Button(text_buttons, text="批量修改同值")
        self.batch_replace_button.pack(side="left", padx=(8, 0))

        editor_box = ttk.LabelFrame(self.frame, text="编辑设置", padding=8)
        editor_box.pack(fill="x", pady=(8, 0))
        step_row = ttk.Frame(editor_box)
        step_row.pack(fill="x")
        ttk.Label(step_row, text="拖动步长").pack(side="left")
        self.drag_step_entry = ttk.Entry(step_row, textvariable=drag_step_var, width=10)
        self.drag_step_entry.pack(side="left", padx=(8, 6))
        ttk.Label(step_row, text="px").pack(side="left")
        ttk.Label(editor_box, text="端点和辅助线拖动都会按这个步长吸附。", justify="left").pack(anchor="w", pady=(8, 0))

        guide_box = ttk.LabelFrame(self.frame, text="辅助线", padding=8)
        guide_box.pack(fill="x", pady=(8, 0))
        guide_input = ttk.Frame(guide_box)
        guide_input.pack(fill="x")
        ttk.Label(guide_input, text="方向").pack(side="left")
        self.guide_axis_combo = ttk.Combobox(guide_input, textvariable=guide_axis_var, values=["x", "y"], width=4, state="readonly")
        self.guide_axis_combo.pack(side="left", padx=(6, 8))
        ttk.Label(guide_input, text="位置").pack(side="left")
        self.guide_value_entry = ttk.Entry(guide_input, textvariable=guide_value_var, width=10)
        self.guide_value_entry.pack(side="left", padx=(6, 8))
        self.add_guide_button = ttk.Button(guide_input, text="添加辅助线")
        self.add_guide_button.pack(side="left")
        guide_actions = ttk.Frame(guide_box)
        guide_actions.pack(fill="x", pady=(8, 0))
        self.add_focus_x_button = ttk.Button(guide_actions, text="添加焦点 X")
        self.add_focus_x_button.pack(side="left")
        self.add_focus_y_button = ttk.Button(guide_actions, text="添加焦点 Y")
        self.add_focus_y_button.pack(side="left", padx=(8, 0))
        self.delete_guide_button = ttk.Button(guide_actions, text="删除选中辅助线")
        self.delete_guide_button.pack(side="left", padx=(8, 0))
        self.clear_guides_button = ttk.Button(guide_actions, text="清空辅助线")
        self.clear_guides_button.pack(side="left", padx=(8, 0))
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
