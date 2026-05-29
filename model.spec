a = Analysis(
    ['model/main.py'],
    datas=[
        ('model/*.pth', '.'),  # bundle model weights
    ],
    hiddenimports=[
        'uvicorn.logging', 'uvicorn.loops.auto',
        'uvicorn.protocols.http.auto', 'uvicorn.lifespan.on'
    ],
)
pyz = PYZ(a.pure)
exe = EXE(pyz, a.scripts, a.binaries, a.datas,
    name='model', onefile=True, console=True)