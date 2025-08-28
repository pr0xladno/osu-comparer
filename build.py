import subprocess
import sys
import os

if os.path.exists("requirements.txt"):
    print("Checking dependencies from requirements.txt...")
    subprocess.run([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"], check=True)
else:
    print("requirements.txt not found. Skipping dependency check.")

try:
    version = subprocess.getoutput("git describe --tags --abbrev=0")
except Exception as e:
    print(f"Cannot get version from git: {e}")
    version = "v0.0.0"

exe_name_cli = f"osu-comparer-{version}-cli"
exe_name_gui = f"osu-comparer-{version}-gui"

commands = [
    f'pyinstaller --onefile --console --add-data ".env;." --name "{exe_name_cli}" osu_comparer/cli.py',
    f'pyinstaller --onefile --noconsole --add-data ".env;." --name "{exe_name_gui}" osu_comparer/gui.py'
]

for cmd in commands:
    print(f"Running: {cmd}")
    subprocess.run(cmd, shell=True, check=True)