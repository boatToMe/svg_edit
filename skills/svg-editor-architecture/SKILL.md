---
name: svg-editor-architecture
description: Summarize and reuse the current architecture of this Python Tkinter SVG editor project. Use when explaining this repository's structure, documenting its layering, identifying the design patterns in use, or extending the editor while preserving its application/view/controller split and command-based undo-redo model.
---

# SVG Editor Architecture

Treat this project as a small desktop application with explicit layering. Preserve the current boundaries instead of moving behavior back into a single UI class.

## Architecture Map

Use these layers as the default mental model:

- `svg_path_editor/application/editor.py`: application layer. Hold session state, interaction state, history stack, and command objects.
- `svg_path_editor/ui/app.py`: composition root. Instantiate views, controllers, session, and state; bind events; coordinate redraw.
- `svg_path_editor/ui/views/`: view layer. Build Tk widgets only; avoid business logic here.
- `svg_path_editor/ui/controllers/`: controller layer. Translate UI events into application operations.
- `svg_path_editor/ui/rendering.py`: canvas rendering layer. Draw shapes, handles, guides, and overlay hints.
- `svg_path_editor/path_ops.py`: geometry layer. Parse, rebuild, and serialize SVG shapes and path data.
- `svg_path_editor/svg_document.py`: document I/O layer. Load and save SVG XML, collect editable elements, expose `viewBox`.
- `svg_path_editor/models.py`: shared geometry data structures.

Follow the dependency direction below:

`views -> controllers -> application -> path_ops/svg_document/models`

Let `rendering.py` depend on read-only editor state, not on controller-specific mutations.

## Design Patterns In Use

Recognize the current design as a mix of lightweight desktop patterns:

- `MVC`: views own widgets, controllers own event handling, the application/session layer owns state.
- `Composition Root`: `ui/app.py` wires dependencies in one place.
- `Facade`: `EditorSession` hides document loading, active shape switching, and shape application details.
- `Command Pattern`: editing operations are command objects with `execute()` and `undo()`.
- `Command History`: `HistoryManager` stores executed commands and drives `Ctrl+Z` / `Ctrl+Y`.
- `State Object`: `InteractionState` holds transient UI state such as focus handle, guides, zoom, drag state, and text selection mappings.
- `Strategy-like Rendering Split`: drawing logic lives in `rendering.py` and preview drawing lives in `PreviewController`, instead of being embedded in widgets.

## Extension Rules

Use these rules when adding features:

1. Put persistent editing operations into new command classes when the action must support undo/redo.
2. Keep drag-time temporary values in `InteractionState`; commit final edits through commands on mouse-up.
3. Add new UI widgets in `ui/views/` first, then bind them in `ui/app.py`, then implement behavior in a controller.
4. Put SVG parsing or serialization changes in `path_ops.py` or `svg_document.py`, not in controllers.
5. Keep preview-specific rendering separate from editor-canvas rendering unless both truly share the same drawing primitive.
6. Prefer expanding `EditorSession` only for cross-controller application behavior; do not move widget code into it.
7. If a controller grows around multiple unrelated workflows, split it by interaction domain rather than by widget type.

## Typical Feature Placement

Map common changes like this:

- Add a new undoable edit type: extend `application/editor.py` with a new command.
- Add a new supported SVG element: update `models.py` if needed, then `path_ops.py`, then document loading/saving expectations.
- Add a new panel or dialog: create or extend a view, then attach controller behavior.
- Add new canvas overlays: update `ui/rendering.py`.
- Add new preview behavior: update `ui/views/preview_view.py` and `ui/controllers/preview_controller.py`.

## Anti-Patterns To Avoid

Do not regress into these patterns:

- One giant `SVGPathEditor` class owning widgets, state, parsing, saving, and rendering.
- Controllers directly rewriting XML or geometry parsing logic.
- Views containing undo/redo logic or document mutation.
- Snapshots for every change when a semantic command is more appropriate.
- Duplicating shape parsing rules between preview code and editor code without a strong reason.

## Quick Summary

Describe the project in one sentence as:

"A layered Tkinter SVG editor that uses MVC-style separation, a session facade, explicit interaction state, and command-based undo/redo to keep editing behavior maintainable."
