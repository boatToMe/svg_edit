# AGENTS.md

## Skills
A skill is a set of local instructions stored in a `SKILL.md` file. Use the project-local skill below when the task matches its trigger.

### Available skills
- svg-editor-maintenance: Maintain and extend this project's Python Tkinter SVG editor while preserving its layered `core/application/ui` architecture, command-based undo-redo model, preview rendering split, and controller boundaries. Use when refactoring structure, adding features, documenting patterns, or deciding where new code should live. (file: skills/svg-editor-maintenance/SKILL.md)

### How to use skills
- Discovery: The skill list above is the set of project-local skills available in this repository.
- Trigger rules: If the user names a skill with `$SkillName` or plain text, or if the task clearly matches the skill description, you must use that skill for the turn.
- Missing or blocked: If the skill file cannot be read, say so briefly and continue with the best fallback.
- Usage flow:
  1. Open the referenced `SKILL.md`.
  2. Read only enough to follow the workflow.
  3. Load additional files only when needed.
- Context hygiene:
  - Keep the loaded context small.
  - Prefer the project skill over re-deriving the architecture from scratch when it applies.
