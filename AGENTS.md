# AGENTS.md

## Cursor Cloud specific instructions

BakUI (`main.py`) is a single Python 3 desktop GUI app (Tkinter + `ttkbootstrap`) for
incremental/sync file backup. There is no backend, database, or network service — the only
outbound call is an optional GitHub update check. See `README.md` for the product overview.

### Environment
- Python deps live in a virtualenv at `.venv/` (Ubuntu 24.04 is PEP 668 externally-managed, so
  system-wide `pip install` is blocked). The update script creates `.venv` and installs
  `requirements.txt`.
- The app needs the OS-level Tk libraries (`python3-tk`) and a display. These are installed at
  VM-build time, not by the update script.

### Run (development)
- The xfce desktop that computer-use/VNC sees is on `DISPLAY=:1`. Launch the GUI there so it is
  visible for manual testing: `DISPLAY=:1 .venv/bin/python main.py`.
- A headless `Xvfb :99` display is also available (`DISPLAY=:99`) if you only need to smoke-test
  that Tk can start without a visible desktop.
- `backup_history.json` is auto-created in the working directory (gitignored).

### Lint / test / build caveats
- No linter is configured. Use a syntax check as a lightweight gate:
  `.venv/bin/python -m py_compile main.py build.py core/*.py gui/*.py`.
- The files in `tests/` are stale and fail to import: they reference `backup_core` /
  `history_manager`, but the real modules are `core.backup` (`BackupManager.start_backup`) and
  `core.history` (`HistoryManager`). `python -m unittest discover -s tests` errors out. Rewrite
  them against the real modules before relying on them.
- `build.py` (PyInstaller) targets a Windows `.exe` and references `BakUI.spec`, which is not in
  the repo — it is not usable for local dev.
