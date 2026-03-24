# -*- mode: python ; coding: utf-8 -*-
# SchoolAutoChat.spec  –  PyInstaller build spec (onefile)

from PyInstaller.utils.hooks import collect_all, collect_submodules

# ── Collect every submodule / data shipped with the SocketIO stack ──────────
def _gather(pkg):
    d, b, h = collect_all(pkg)
    return d, b, h

datas_extra, bins_extra, hidden_extra = [], [], []
for _pkg in ('flask_socketio', 'socketio', 'engineio', 'simple_websocket', 'wsproto', 'bidict'):
    _d, _b, _h = _gather(_pkg)
    datas_extra  += _d
    bins_extra   += _b
    hidden_extra += _h

# Extra hidden imports that collect_all sometimes misses
hidden_extra += [
    'engineio.async_drivers.threading',
    'engineio.async_drivers',
    'flask.templating',
    'jinja2.ext',
    'dns',
    'dns.resolver',
]

a = Analysis(
    ['server.py'],
    pathex=[],
    binaries=bins_extra,
    datas=datas_extra + [
        ('templates',     'templates'),
        ('static',        'static'),
        ('knowledge_base','knowledge_base'),
    ],
    hiddenimports=hidden_extra,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='SchoolAutoChat',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,          # keep console window so teachers can see the server IP
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
