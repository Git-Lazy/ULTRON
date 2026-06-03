# ULTRON
Ultra Light Trained Robot of Neumont (Ultron)

run pip install -r requirements.txt

then run the start.py file

you can give your own example classes and image for them, then sort folders or get predictions


the application can be bundled into a .exe file with the following steps, note that the exe file will not be capable of the projects full capabilities

pyinstaller model.spec
pyinstaller backend.spec
pyinstaller frontend.spec
pyinstaller joiner.spec

after these commands an ULTRON.exe file will be created inside of dist