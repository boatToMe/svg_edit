import tkinter as tk
from tkinter import ttk

from .flow import FlowRow
from .preview_controls import ButtonPair


TAB_SELECTED_BG = "#f8fafc"
TAB_SELECTED_FG = "#020617"
TAB_UNSELECTED_BG = "#6b7280"
TAB_UNSELECTED_FG = "#f8fafc"
TAB_HOVER_BG = "#4b5563"
TABBAR_BG = "#cbd5e1"


class InspectorNotebook(ttk.Frame):
    def __init__(self, parent):
        super().__init__(parent)
        self.current_index = -1
        self._tabs: list[dict[str, object]] = []
        self._hover_index: int | None = None
        self.tab_bar = tk.Frame(self, bg=TABBAR_BG, bd=0, highlightthickness=0)
        self.content = ttk.Frame(self)
        self.tab_bar.pack(fill="x")
        self.content.pack(fill="both", expand=True)

    def add(self, child, text: str):
        index = len(self._tabs)
        button = tk.Button(
            self.tab_bar,
            text=text,
            bd=0,
            relief="flat",
            highlightthickness=0,
            padx=12,
            pady=5,
            bg=TAB_UNSELECTED_BG,
            fg=TAB_UNSELECTED_FG,
            activebackground=TAB_HOVER_BG,
            activeforeground=TAB_UNSELECTED_FG,
            command=lambda idx=index: self.select(idx),
            cursor="hand2",
        )
        button.pack(side="left", padx=(0, 2))
        button.bind("<Enter>", lambda _event, idx=index: self._set_hover(idx))
        button.bind("<Leave>", lambda _event, idx=index: self._clear_hover(idx))
        self._tabs.append({"frame": child, "button": button, "text": text})
        if self.current_index == -1:
            self.select(0)

    def add_tab_changed_handler(self, handler):
        self.bind("<<NotebookTabChanged>>", handler)

    def select(self, index: int):
        if index < 0 or index >= len(self._tabs):
            return
        if self.current_index == index:
            return
        if self.current_index >= 0:
            previous = self._tabs[self.current_index]["frame"]
            previous.pack_forget()
        self.current_index = index
        current = self._tabs[index]["frame"]
        current.pack(in_=self.content, fill="both", expand=True)
        self._refresh_button_styles()
        self.event_generate("<<NotebookTabChanged>>")

    def index(self, which):
        if which == "current":
            return self.current_index
        raise ValueError(which)

    def tab(self, index: int, option: str):
        if option == "text":
            return self._tabs[index]["text"]
        raise ValueError(option)

    def _set_hover(self, index: int):
        self._hover_index = index
        self._refresh_button_styles()

    def _clear_hover(self, index: int):
        if self._hover_index == index:
            self._hover_index = None
            self._refresh_button_styles()

    def _refresh_button_styles(self):
        for index, tab in enumerate(self._tabs):
            button = tab["button"]
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


class ElementManagerGroup:
    def __init__(self, parent):
        self.frame = ttk.LabelFrame(parent, text="元素管理", padding=8)
        self.listbox = None
        self._build()

    def _build(self):
        self.frame.pack(fill="x", pady=(0, 8))
        list_frame = ttk.Frame(self.frame)
        list_frame.pack(fill="x")
        self.listbox = tk.Listbox(list_frame, height=6, exportselection=False)
        self.listbox.pack(side="left", fill="x", expand=True)
        scrollbar = ttk.Scrollbar(list_frame, orient="vertical", command=self.listbox.yview)
        scrollbar.pack(side="right", fill="y")
        self.listbox.configure(yscrollcommand=scrollbar.set)


class GuideListActions:
    def __init__(self, parent):
        self.frame = ttk.Frame(parent)
        self.buttons = ButtonPair(self.frame, "删除选中辅助线", "清空辅助线")
        self.delete_button = self.buttons.first_button
        self.clear_button = self.buttons.second_button
        self._build()

    def _build(self):
        self.frame.pack(fill="x", pady=(8, 0))
        self.buttons.frame.pack(anchor="w")


class EditInspectorTab:
    def __init__(self, parent, guide_axis_var: tk.StringVar, guide_value_var: tk.StringVar, drag_step_var: tk.StringVar):
        self.frame = ttk.Frame(parent, padding=8)
        self.element_manager = None
        self.element_listbox = None
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
        self.guide_actions = None
        self._build(guide_axis_var, guide_value_var, drag_step_var)

    def _build(self, guide_axis_var: tk.StringVar, guide_value_var: tk.StringVar, drag_step_var: tk.StringVar):
        self.element_manager = ElementManagerGroup(self.frame)
        self.element_listbox = self.element_manager.listbox

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

        guide_focus = FlowRow(guide_box)
        guide_focus.pack(fill="x", pady=(8, 0))
        self.add_focus_x_button = ttk.Button(guide_focus.frame, text="添加焦点 X")
        self.add_focus_y_button = ttk.Button(guide_focus.frame, text="添加焦点 Y")
        guide_focus.add(self.add_focus_x_button)
        guide_focus.add(self.add_focus_y_button)

        list_frame = ttk.Frame(guide_box)
        list_frame.pack(fill="x", pady=(8, 0))
        self.guide_listbox = tk.Listbox(list_frame, height=6, exportselection=False)
        self.guide_listbox.pack(side="left", fill="x", expand=True)
        guide_scrollbar = ttk.Scrollbar(list_frame, orient="vertical", command=self.guide_listbox.yview)
        guide_scrollbar.pack(side="right", fill="y")
        self.guide_listbox.configure(yscrollcommand=guide_scrollbar.set)

        self.guide_actions = GuideListActions(guide_box)
        self.delete_guide_button = self.guide_actions.delete_button
        self.clear_guides_button = self.guide_actions.clear_button


class CodeInspectorTab:
    def __init__(self, parent):
        self.frame = ttk.Frame(parent, padding=8)
        self.strip_css_button = None
        self.preview_saved_code_button = None
        self.text = None
        self._build()

    def _build(self):
        code_box = ttk.LabelFrame(self.frame, text="SVG 代码", padding=8)
        code_box.pack(fill="both", expand=True)
        text_frame = ttk.Frame(code_box)
        text_frame.pack(fill="both", expand=True)
        self.text = tk.Text(text_frame, wrap="none", font=("Consolas", 10), state="disabled")
        self.text.pack(side="left", fill="both", expand=True)
        y_scroll = ttk.Scrollbar(text_frame, orient="vertical", command=self.text.yview)
        y_scroll.pack(side="right", fill="y")
        x_scroll = ttk.Scrollbar(code_box, orient="horizontal", command=self.text.xview)
        x_scroll.pack(fill="x", pady=(8, 0))
        self.text.configure(yscrollcommand=y_scroll.set, xscrollcommand=x_scroll.set)

        actions_box = ttk.LabelFrame(self.frame, text="操作面板", padding=8)
        actions_box.pack(fill="x", pady=(8, 0))
        actions = FlowRow(actions_box)
        actions.pack(fill="x")
        self.strip_css_button = ttk.Button(actions.frame, text="去除所有 CSS")
        self.preview_saved_code_button = ttk.Button(actions.frame, text="预览结果代码")
        actions.add(self.strip_css_button)
        actions.add(self.preview_saved_code_button)


class InspectorSidebar:
    def __init__(self, parent, guide_axis_var: tk.StringVar, guide_value_var: tk.StringVar, drag_step_var: tk.StringVar):
        self.frame = ttk.Frame(parent)
        self.notebook = InspectorNotebook(self.frame)
        self.edit_tab = EditInspectorTab(self.notebook.content, guide_axis_var, guide_value_var, drag_step_var)
        self.code_tab = CodeInspectorTab(self.notebook.content)

        self.element_listbox = self.edit_tab.element_listbox
        self.text = self.edit_tab.text
        self.apply_text_button = self.edit_tab.apply_text_button
        self.reload_button = self.edit_tab.reload_button
        self.batch_replace_button = self.edit_tab.batch_replace_button
        self.drag_step_entry = self.edit_tab.drag_step_entry
        self.guide_axis_combo = self.edit_tab.guide_axis_combo
        self.guide_value_entry = self.edit_tab.guide_value_entry
        self.add_guide_button = self.edit_tab.add_guide_button
        self.add_focus_x_button = self.edit_tab.add_focus_x_button
        self.add_focus_y_button = self.edit_tab.add_focus_y_button
        self.delete_guide_button = self.edit_tab.delete_guide_button
        self.clear_guides_button = self.edit_tab.clear_guides_button
        self.guide_listbox = self.edit_tab.guide_listbox
        self.code_text = self.code_tab.text
        self.strip_css_button = self.code_tab.strip_css_button
        self.preview_saved_code_button = self.code_tab.preview_saved_code_button
        self._build()

    def _build(self):
        self.frame.pack(fill="both", expand=True)
        self.notebook.pack(fill="both", expand=True)
        self.notebook.add(self.edit_tab.frame, text="图形")
        self.notebook.add(self.code_tab.frame, text="代码")
