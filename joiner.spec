a = Analysis(
    ['joiner.py'],
    datas=[
        ('dist/*.exe', 'dist'),  # bundle model weights
    ],
    hiddenimports=[

    ],
)
pyz = PYZ(a.pure)
exe = EXE(pyz, a.scripts, a.binaries, a.datas,
    name='ULTRON', onefile=True, console=False)