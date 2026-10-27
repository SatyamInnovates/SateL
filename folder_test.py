import json
import shutil
import subprocess
from pathlib import Path

FOLDERS_FILE = Path(__file__).with_name("folders.json")

def load_folders():
    try:
        with open(FOLDERS_FILE, encoding="utf-8") as f:
            data = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {}
    return {k.lower(): v for k, v in data.items()}

def open_folder(nickname, folders):
    path = folders.get(nickname)
    if path is None:
        speak("I don't know that folder")
        return
    if not Path(path).is_dir():
        speak("That folder is missing")
        return
    code = shutil.which("code")
    if code is None:
        speak("VS Code not found")
        return
    subprocess.Popen([code, path])
    speak(f"Opening {nickname}")