a = Analysis(
    ['frontend/main.py'],
    datas=[
        ('frontend/static/app.js', './static'),
        ('frontend/static/style.css', './static'),
        ('frontend/static/index.html', './static'),
        ('frontend/images/favicon.ico', './images'),
    ],
    hiddenimports=[
        'webview',
        'webview.platforms.winforms',
        'clr',
    ],
)
pyz = PYZ(a.pure)
exe = EXE(pyz, a.scripts, a.binaries, a.datas,
    name='frontend', onefile=True, console=True)