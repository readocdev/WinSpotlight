import PyInstaller.__main__

PyInstaller.__main__.run([
    "main.py",
    "--name=WinSpotlight",
    "--onefile",
    "--windowed",
    "--clean",
    "--noconfirm"
])
