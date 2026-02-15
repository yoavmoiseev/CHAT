Portable package (embeddable Python + wheels) - instructions

Goal
----
Create a truly offline, portable Windows package for School Auto Chat:
- a single EXE to run the server on Windows (no Python install required)
- optional `embedded_python/` for including a light embeddable Python runtime
- optional `wheels/` folder containing wheel files for offline installation

Files added
-----------
- `make_portable.bat` — orchestrates environment preparation and builds an EXE using PyInstaller.

How to prepare an offline portable bundle (recommended)
----------------------------------------------------
1. On a machine with internet and Python installed:
   - Optionally download the embeddable CPython ZIP from https://www.python.org/downloads/windows/ and extract into `embedded_python/`.
   - Create a `wheels/` folder and run `pip wheel -r requirements.txt -w wheels` to collect all required wheels. Commit `wheels/` to your repo (or keep it separately for distribution).
   - Run `make_portable.bat` — it will install packages from `wheels/` (offline) into a `.venv` and build `dist\start_server.exe`.

2. Without internet (build from prepared repo):
   - Ensure `embedded_python\` or `.venv\` exists and `wheels\` contains required wheel files.
   - Run `make_portable.bat` — it will use local wheels and produce `dist\start_server.exe`.

Notes
-----
- Embeddable Python may not include `ensurepip`; in that case use system Python to create `.venv` and install wheels, then run PyInstaller from `.venv`.
- `dist\start_server.exe` is a single-file executable that includes the Python interpreter and all dependencies; this is ideal for offline distribution.
- Building exe must be done on the same OS/architecture as the target.
