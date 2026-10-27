import os
import sys
import shutil
import subprocess

proga_dir = r"C:\Users\kosty\Desktop\Proga\ZapretManager"
assets_dir = os.path.join(proga_dir, "assets")
icon_ico = os.path.join(assets_dir, "icon.ico")
main_py = os.path.join(proga_dir, "src", "main.py")
src_dir = os.path.join(proga_dir, "src")
dist_dir = os.path.join(proga_dir, "dist")
build_dir = os.path.join(proga_dir, "build")

cmd = [
    sys.executable, "-m", "PyInstaller",
    "--name=ZapretManager",
    "--onefile",
    "--noconsole",
    "--uac-admin",
    f"--icon={icon_ico}",
    f"--paths={src_dir}",
    f"--paths={proga_dir}",
    f"--add-data={assets_dir};assets",
    "--collect-all=customtkinter",
    "--collect-all=requests",
    "--collect-all=urllib3",
    "--collect-all=pystray",
    "--collect-all=PIL",
    f"--distpath={dist_dir}",
    f"--workpath={build_dir}",
    "--clean",
    main_py
]

print("Compiling ZapretManager.exe...")
res = subprocess.run(cmd)
if res.returncode == 0:
    dist_exe = os.path.join(dist_dir, "ZapretManager.exe")
    root_exe = os.path.join(proga_dir, "ZapretManager.exe")
    zapret_folder_exe = r"C:\Users\kosty\Desktop\zapret-discord-youtube-1.10.1\ZapretManager.exe"
    shutil.copy2(dist_exe, root_exe)
    try:
        shutil.copy2(dist_exe, zapret_folder_exe)
    except Exception as e:
        print("Notice:", e)
    print("BUILD SUCCESSFUL!")
