"""One-step launcher: creates a private environment, installs what's needed, opens the app."""
import os
import subprocess
import sys
import venv
from pathlib import Path

here = Path(__file__).parent
env = here / ".venv"
py = env / ("Scripts/python.exe" if os.name == "nt" else "bin/python")

if sys.version_info < (3, 9):
    sys.exit("Please install Python 3.9 or newer from https://www.python.org/downloads/")

if not py.exists():
    print("Setting up (first run only, about a minute)...")
    venv.create(env, with_pip=True)

marker = env / ".installed"
if not marker.exists():
    subprocess.check_call([str(py), "-m", "pip", "install", "--quiet", "--upgrade", "pip"])
    subprocess.check_call([str(py), "-m", "pip", "install", "--quiet", "-r", str(here / "requirements.txt")])
    marker.touch()

print("Starting the dashboard. Your browser will open; press Ctrl+C here to stop.")
os.environ["STREAMLIT_BROWSER_GATHER_USAGE_STATS"] = "false"
subprocess.call([str(py), "-m", "streamlit", "run", str(here / "kenya_student_life_app.py")])
