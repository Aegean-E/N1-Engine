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

## Licensing migration (apache-final)

- New versions use the Aegean License 1.1 (AL-1.1); versions up to and including `apache-final` remain under the Apache License 2.0.
- Rights holder: AegeanWorks; commercial use under ACL-1.0.
- Counsel review of the 1.1 texts remains pending.

## License notice cleanup (2026-10-26)

- The license-history notes and the old-license boundary tag were removed: the project is offered only under the Aegean License 1.1 (AL-1.1), with commercial use under ACL-1.0.
