import difflib
import os
import time
from pathlib import Path
import requests
import speech_recognition as sr
import win32com.client
from dotenv import load_dotenv
import json
import shutil
import subprocess
import webbrowser
from urllib.parse import urlparse
load_dotenv()

API_KEY = os.getenv("GROQ_API_KEY")
API_URL = "https://api.groq.com/openai/v1/chat/completions"
MODEL = "openai/gpt-oss-20b"
SYSTEM_PROMPT = "You are Jarvis, a friendly voice assistant. Give concise, helpful answers."

recognizer = sr.Recognizer()
recognizer.dynamic_energy_threshold = True
recognizer.pause_threshold = 0.8
recognizer.non_speaking_duration = 0.5
speaker = win32com.client.Dispatch("SAPI.SpVoice")
speaker.Volume = 100
speaker.Rate = 0
last_spoken_at = 0.0


FOLDERS_FILE = Path(__file__).with_name("folders.json")

def load_folders():
    try:
        with open(FOLDERS_FILE, encoding="utf-8") as f:
            data = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {}
    return {k.lower(): v for k, v in data.items()}
WEBSITE_FILE = Path(__file__).with_name('websites.json')
def load_websites():
    try:
        with open(WEBSITE_FILE,encoding="utf-8") as f:
            data = json.load(f)
    except (FileNotFoundError,json.JSONDecodeError):
        return {}
    return {k.lower(): v for k,v in data.items()}

def scan_apps():

    folders = [
        Path(os.environ.get("PROGRAMDATA", "C:/ProgramData"))
        / "Microsoft/Windows/Start Menu/Programs",
        Path(os.environ.get("APPDATA", str(Path.home() / "AppData/Roaming")))
        / "Microsoft/Windows/Start Menu/Programs",
    ]
    found = {}
    for folder in folders:
        if not folder.exists():
            continue
        try:
            for shortcut in folder.rglob("*.lnk"):
                found[shortcut.stem.lower()] = str(shortcut)
        except OSError as error:
            print(f"Couldn't scan {folder}: {error}")
    return found


apps = scan_apps()
folders = load_folders()
web_url = load_websites()


def listen():
    quiet_period = 0.7
    remaining = quiet_period - (time.monotonic() - last_spoken_at)
    if remaining > 0:
        time.sleep(remaining)
    asked_to_repeat = False
    while True:
        try:
            with sr.Microphone() as source:
                print("Listening...")
                audio = recognizer.listen(source, timeout=8, phrase_time_limit=10)
            text = recognizer.recognize_google(audio, language="en-IN").lower().strip()
            print(f"You said: {text}")
            return text
        except sr.WaitTimeoutError:
            return ""
        except sr.UnknownValueError:
            print("Couldn't understand that.")
            if asked_to_repeat:
                return ""
            speak("Can you say that again?")
            asked_to_repeat = True
        except sr.RequestError as error:
            print(f"Speech recognition problem: {error}")
            return ""
        except (OSError, AttributeError) as error:
            print(f"Microphone problem: {error}")
            speak(f"Microphone problem: {error}")
            return ""
    return ""

def speak(text):
    global last_spoken_at
    try:
        if not text:
            return
        speaker.Speak(str(text))
        last_spoken_at = time.monotonic()
    except Exception as e:
        print(f"Speech output problem: {e}")

        
    
            
def filter_user(text):
    fillers = {"please", "open", "can", "you", "hey", "launch", "start", "run", "bro", "satel", "jarvis", "the"}
    return [word for word in text.lower().split() if word not in fillers]

def open_folder(nickname, folders):
    path = folders.get(nickname)
    if path is None:
        speak("I don't know that folder")
        return
    if not Path(path).is_dir():
        print(f"Folder '{nickname}' points to a missing path: {path}")
        speak("That folder is missing")
        return
    code = shutil.which("code")
    if code is None:
        speak("VS Code not found")
        return
    try:
        subprocess.Popen([os.environ.get("COMSPEC", "cmd.exe"), "/c", "start", "", code, path])
        print(f"Opening '{nickname}' in VS Code: {path}")
        speak(f"Opening {nickname}")
    except OSError as error:
        print(f"Could not open '{nickname}' in VS Code: {error}")
        speak(f"Could not open {nickname} in VS Code")
    
def open_url(url, nickname=None):
    url = url.strip().rstrip(".,!?;:")
    if not urlparse(url).scheme:
        url = f"https://{url}"
    parsed = urlparse(url)
    host = parsed.hostname
    if (
        parsed.scheme not in {"http", "https"}
        or not host
        or any(char.isspace() for char in url)
        or ("." not in host and host != "localhost")
    ):
        print(f"Invalid website URL: {url}")
        speak("That website address is invalid")
        return

    if webbrowser.open(url, new=2):
        label = nickname or host
        print(f"Opening {label}: {url}")
        speak(f"Opening {label}")
    else:
        print(f"Could not open website: {url}")
        speak("I couldn't open that website")
            


def find_app(text):
    query = " ".join(filter_user(text))
    if not query:
        return None
    if query in apps:
        return query
    match = difflib.get_close_matches(query, apps.keys(), n=1, cutoff=0.68)
    return match[0] if match else None


def understand_app(user_input):
    if not API_KEY or not apps:
        return None
    names = ", ".join(sorted(apps))
    prompt = (
        "Identify which application the user wants to open. Choose only from this list: "
        f"{names}\nReturn exactly the selected app name, or none if no app fits.\n"
        f"User request: {user_input}"
        # f"If the user asks about a webstie return url:{web_url}"
    )
    try:
        response = requests.post(
            API_URL,
            headers={"Authorization": f"Bearer {API_KEY}"},
            json={
                "model": MODEL,
                "messages": [
                    {"role": "system", "content": "Follow the requested output format exactly."},
                    {"role": "user", "content": prompt},
                ],
                "temperature": 0,
                "max_tokens": 30,
            },
            timeout=12,
        )
        response.raise_for_status()
        result = response.json()["choices"][0]["message"]["content"].strip().lower()
        result = result.strip(" \t\r\n\"'`.,:;!?*-")
      
        if result in apps:
            return result
        return next((name for name in apps if name in result), None)
    except (requests.RequestException, KeyError, IndexError, ValueError) as error:
        print(f"App matching problem: {error}")
        return None


def ask_ai(user_input):
    if not API_KEY:
        return "API KEY isn't integrated bro"
    try:
        response = requests.post(
            API_URL,
            headers={"Authorization": f"Bearer {API_KEY}"},
            json={
                "model": MODEL,
                "messages": [
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": user_input},
                ],
                "temperature": 0.7,
                "max_tokens": 250,
            },
            timeout=20,
        )
        response.raise_for_status()
        return response.json()["choices"][0]["message"]["content"].strip()
    except (requests.RequestException, KeyError, IndexError, ValueError) as error:
        print(f"AI service problem: {error}")
        return "Can't Reach my ai services. Please try again."


OPEN_WORDS = {"open", "launch", "start", "run"}


def is_app_command(text):
    words = text.lower().split()
    while words and words[0] in {"please", "can", "you", "hey", "jarvis"}:
        words.pop(0)

    return bool(words and words[0] in OPEN_WORDS) or text.lower().strip() in apps


def handle_command(command):
    folder_query = " ".join(filter_user(command))
    words = command.lower().split()
    said_open = any(w in OPEN_WORDS for w in words)

    website_name = None
    if folder_query in web_url:
        website_name = folder_query
    if website_name:
        open_url(web_url[website_name], website_name)
        return

    if said_open and folder_query:
        candidate = folder_query.replace(" dot ", ".").replace(" slash ", "/")
        parsed_candidate = urlparse(candidate if "://" in candidate else f"https://{candidate}")
        if parsed_candidate.hostname and "." in parsed_candidate.hostname:
            open_url(candidate)
            return

    if said_open:
        website_match = difflib.get_close_matches(
            folder_query, web_url.keys(), n=1, cutoff=0.55
        )
        if website_match:
            website_name = website_match[0]
    if website_name:
        open_url(web_url[website_name], website_name)
        return

    nickname = None
    if folder_query in folders:
        nickname = folder_query
    elif said_open:
        folder_match = difflib.get_close_matches(folder_query, folders.keys(), n=1, cutoff=0.55)
        if folder_match:
            nickname = folder_match[0]
    if nickname:
        open_folder(nickname,folders)
        return
        
        

    if is_app_command(command):
        name = find_app(command)
        if not name:
            name = understand_app(command)
        if name:
            try:
                os.startfile(apps[name])
                print(f"Opening {name}")
                speak(f"Opening {name}")
            except OSError as error:
                print(f"Could not open {name}: {error}")
        else:
            print("I couldn't find that app in the Start Menu.")
            speak("I couldn't find that app in the Start Menu.")
        return

    answer = ask_ai(command)
    speak(answer)
    print(f"Jarvis: {answer}")
    


def main():
    active = False
    try:
        with sr.Microphone() as source:
            print("Calibrating microphone. Please stay quiet for a moment...")
            recognizer.adjust_for_ambient_noise(source, duration=1)
            print(f"Microphone ready (sensitivity threshold: {recognizer.energy_threshold:.0f}).")
    except (OSError, AttributeError) as error:
        print(f"Microphone setup problem: {error}")
        speak(f"Microphone setup problem: {error}")
        return
    print(f"Found {len(apps)} Start Menu apps. Say 'hello' to activate, 'sleep' to pause, or 'exit' to quit.")
    while True:
        user = listen()
        if not user:
            continue

        words = user.split()
        if user in {"exit", "quit", "shutdown"}:
            print("Shutting down assistant.")
            speak("Shutting down")
            break

        if not active:
            if "hello" not in words and "jarvis" not in words and "satel" not in words:
                continue
            active = True
            print("Assistant activated!")
            speak('Yo what do i do?')
            command = " ".join(word for word in words if word not in {"hello", "jarvis", "satel"}).strip()
            if not command:
                continue
        else:
            command = user

        if command in {"sleep", "go to sleep", "stop listening"}:
            active = False
            print("Assistant is sleeping.")
            speak("by")
            continue

        handle_command(command)


if __name__ == "__main__":
    main()
