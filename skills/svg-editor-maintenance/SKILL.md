---
name: svg-editor-maintenance
description: Maintain, refactor, and extend this repository's Python Tkinter SVG editor while preserving its layered architecture. Use when reorganizing files, splitting oversized modules, adding new editor features, introducing undoable operations, or documenting the current design patterns and dependency boundaries for this specific project.
---

# SVG Editor Maintenance

Treat this repository as a layered desktop editor. Keep responsibilities separated instead of moving logic back into one large UI or controller module.

## Architecture Map

Default to these directories and roles:

- `svg_path_editor/core/`
  Hold geometry data structures, SVG parsing/serialization, and document I/O.
  Put reusable shape logic here, not in controllers.
- `svg_path_editor/application/`
  Hold application state and undoable operations.
  `session.py` manages the active document and selected shape.
  `state.py` holds transient interaction state.
  `commands.py`, `operations.py`, and `history.py` implement command-based editing.
- `svg_path_editor/ui/views/`
  Build Tkinter widgets only.
  Avoid business logic and SVG mutation here.
- `svg_path_editor/ui/controllers/`
  Translate widget events into application actions.
  Keep each controller focused on one interaction domain.
- `svg_path_editor/ui/preview/`
  Hold preview-only rendering and style resolution.
  Keep preview drawing concerns out of the main preview controller.
- `svg_path_editor/ui/rendering.py`
  Draw the main editing canvas, guides, handles, overlays, and warnings.
- `svg_path_editor/ui/app.py`
  Act as the composition root.
  Wire views, controllers, session, and state together.

Use this dependency direction:

`views -> controllers -> application -> core`

Allow `ui/rendering.py` and `ui/preview/renderer.py` to read state, but keep mutation inside controllers and application commands.

## Design Patterns To Preserve

Use these patterns deliberately:

- `MVC-style separation`
  Views own widgets, controllers own interaction flow, application owns state.
- `Composition Root`
  Keep object wiring centralized in `ui/app.py`.
- `Facade`
  Let `EditorSession` hide document loading, active element switching, and shape application details.
- `Command Pattern`
  Represent undoable edits as command objects with `execute()` and `undo()`.
- `Command History`
  Let `HistoryManager` drive undo/redo stacks instead of ad hoc snapshots.
- `State Object`
  Store transient drag, zoom, focus, guide, and text-selection state in `InteractionState`.
- `Renderer split`
  Keep canvas drawing in dedicated renderer modules rather than in controllers.
- `Compatibility shim`
  If file moves would be too disruptive, keep thin re-export modules temporarily, but make new code target the canonical directory.

## Extension Rules

Follow these rules when changing the editor:

1. Put new SVG shape parsing or XML save rules in `core/`.
2. Put undoable edits in `application/operations.py` or a new command module if the group grows.
3. Put new persistent editor state in `EditorSession`; put temporary drag/select state in `InteractionState`.
4. Add widgets in a view first, bind them in `ui/app.py`, and implement behavior in a controller.
5. If a controller grows beyond one interaction domain, split it before adding more features.
6. Keep preview-only behavior inside `ui/preview/` plus `preview_controller.py`; do not mix it into the main editor renderer.
7. Prefer creating a new subpackage when a feature needs both rendering helpers and controller helpers.

## Placement Guide

Map common work like this:

- Add a new supported SVG element:
  Update `core/models.py` if needed, then `core/path_ops.py`, then `core/svg_document.py`, then editor/preview rendering.
- Add a new undoable manipulation:
  Add a command in `application/operations.py` and trigger it from the relevant controller.
- Add a new overlay or guide on the editor canvas:
  Update `ui/rendering.py`.
- Add a new preview styling behavior:
  Update `ui/preview/styles.py`, `ui/preview/renderer.py`, and keep `preview_controller.py` as the coordinator.
- Reorganize architecture:
  Prefer new directories such as `core/`, `application/`, `ui/views/`, `ui/controllers/`, or `ui/preview/` over growing flat module lists.

## Refactoring Checklist

When doing structural work, verify these points before finishing:

- Imports still follow the layered dependency direction.
- Controllers do not parse SVG text directly.
- Views do not own save logic, undo logic, or geometry mutation.
- New undoable behavior participates in `HistoryManager`.
- Preview rendering still works without leaking preview rules into the main canvas renderer.
- Thin compatibility modules, if any remain, are only re-export shims.

## Anti-Patterns

Avoid these regressions:

- Reintroducing one giant `SVGPathEditor` class.
- Letting `preview_controller.py` become both controller and renderer again.
- Mixing XML/style parsing into UI event handlers.
- Storing drag-time state in command objects before the action is finalized.
- Creating new top-level modules when an existing layer directory is the clearer home.

## One-Sentence Summary

Describe the project as:

"A layered Tkinter SVG editor with a `core/application/ui` split, command-based undo/redo, explicit interaction state, and dedicated renderers for editor and preview flows."
