cd /d %~dp0
pyinstaller --onefile --console --name "Mod Packer" "modpacker.py"
pause