# SVG Path Editor

[![Python Version](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)

一个基于 Python 标准库实现的轻量级 SVG 可视化几何编辑工具。采用 `core/application/ui` 分层架构，支持实时预览、指令级编辑、撤销重做以及辅助线对齐，适合快速查看和微调 SVG 路径。

---

## ✨ 核心特性

### 🎨 可视化编辑
- **多格式支持**：支持 `path`、`line`、`polygon` 等常见图元。
- **直观交互**：支持通过鼠标拖拽节点、整体图形以及辅助线。
- **实时同步**：几何数据区数值高亮与画布节点一一对应，双向联动。
- **吸附对齐**：支持自定义步长吸附，让对齐更轻松。

### 🔍 专业预览
- **双渲染引擎**：
  - **编辑画布**：显示节点坐标、`viewBox` 边界、中心辅助线及警示色提示。
  - **内嵌浏览器**：内置 WebView 内核（基于 tkwebview），按浏览器标准 1:1 渲染，支持 CSS 变量（`currentColor`）。
- **样式实时调节**：在预览面板直接调整描边宽度、颜色、填充、圆角近似及线段端点样式。
- **亮暗主题**：预览背景一键切换，适配不同应用场景。

### 🛠 生产力工具
- **撤销重做**：完整的 `Ctrl + Z / Y` 支持。
- **批量修改**：一键替换相同数值，快速完成整体缩放或位移。
- **辅助线系统**：支持 X/Y 轴辅助线，支持一键从当前焦点生成。
- **代码预览**：保存前可预览生成的 SVG 源码。

---

## 🚀 快速开始

### 环境要求
- Python 3.8+
- Windows 环境（由于依赖 `tkwebview` 的二进制组件）

### 启动应用
```powershell
# 克隆仓库
git clone https://github.com/your-username/svg_edit.git
cd svg_edit

# 运行
python app.py
```

---

## ⌨️ 常用快捷键

| 快捷键 | 功能 |
| :--- | :--- |
| **Ctrl + O** | 快速打开 SVG 文件 |
| **Ctrl + S** | 保存文件 |
| **Ctrl + Z** | 撤销上次操作 |
| **Ctrl + Y** | 重做操作 |
| **Space + 拖拽** | 平移画布 |
| **鼠标滚轮** | 缩放画布 |

---

## 🛠 架构设计

本项目遵循严格的 **MVC 分层架构** 维护：

- `svg_path_editor/core/`: 几何数据结构、SVG 解析与序列化核心逻辑。
- `svg_path_editor/application/`: 应用状态管理（Session）与命令模式实现（Undo/Redo）。
- `svg_path_editor/ui/views/`: 基于 Tkinter 的纯视图组件。
- `svg_path_editor/ui/controllers/`: 交互逻辑中转站，连接视图与业务逻辑。
- `svg_path_editor/ui/preview/`: 独立的预览渲染逻辑与样式解析。

---

## 📝 格式说明

在右侧文本框中编辑数据时，遵循以下格式：
- `path`: 直接编辑 `d` 属性（支持 `M/L/H/V/C/S/Q/T/Z` 指令）。
- `line`: 格式为 `x1 y1 x2 y2`。
- `polygon`: 编辑 `points` 列表。

> **说明**：为了保证兼容性，工具在保存时会自动展开部分简写指令，几何形状将保持 100% 一致。

---

## 📄 开源协议

本项目采用 [MIT License](LICENSE) 开源。
