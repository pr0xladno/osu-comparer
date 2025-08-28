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

exe_name = f"osu-comparer-{version}"

cmd = f'pyinstaller --onefile --add-data ".env;." --name {exe_name} main.py'

subprocess.run(cmd, shell=True, check=True)