# Decisions

Why this project is built the way it is, oldest first. One entry per decision that changes a
contract, a dependency, a data format or the architecture; IDs are consecutive and never reused.

### ADR-001: Adopt pytest as the canonical test command
- **Date**: 2026-10-21
- **Status**: Accepted
- **Context**: auto-detection picked `python -m unittest discover`, which discovers zero tests: `tests/` has no `__init__.py` and two of three test modules are pytest-style.
- **Decision**: `.aikit/project.json` `test_command` is set to `python -m pytest tests`; 13/13 tests pass.
- **Consequences**: every future gate run exercises the real suite; pytest stays a development dependency of the project.

### ADR-002: Rename main/gui/utils.py to main/gui/dialogs.py
- **Date**: 2026-10-21
- **Status**: Accepted
- **Context**: the AIKit structure gate flags `utils` as a junk-drawer name; the module holds exactly one role: QMessageBox helpers (show_error, show_warning, show_info).
- **Decision**: renamed the module and updated all 7 import sites; behavior unchanged, 13/13 tests pass.
- **Consequences**: import path `main.gui.utils` no longer exists; `main/utils/` and `main/api/` remain as documented empty reserved packages.
