# -*- mode: python ; coding: utf-8 -*-
"""
PyInstaller spec file para ACES Contabilidad
Empaqueta la aplicación Flask completa en un ejecutable
"""

block_cipher = None

a = Analysis(
    ['app.py'],
    pathex=[],
    binaries=[],
    datas=[
        ('templates', 'templates'),
        ('static', 'static'),
        ('database', 'database'),
        ('modules', 'modules'),
        ('routes', 'routes'),
        ('config.py', '.'),
    ],
    hiddenimports=[
        'flask',
        'flask.cli',
        'werkzeug',
        'jinja2',
        'markupsafe',
        'pandas',
        'numpy',
        'sqlite3',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludedimports=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='ACES_Contabilidad',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,
    disable_windowed_traceback=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='icon.ico' if os.path.exists('icon.ico') else None,
)
