from PyInstaller.utils.hooks import copy_metadata

a = Analysis(
    ['backend/main.py'],
    datas=[
        *copy_metadata('imageio'),  # bundles the package metadata
    ],
    hiddenimports=[
        'uvicorn.logging', 'uvicorn.loops.auto',
        'uvicorn.protocols.http.auto', 'uvicorn.lifespan.on'
    ],
)
pyz = PYZ(a.pure)
exe = EXE(pyz, a.scripts, a.binaries, a.datas,
    name='backend', onefile=True, console=True)