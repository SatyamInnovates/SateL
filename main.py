import difflib
import json
import os
import shutil
import subprocess
import time
import webbrowser
from pathlib import Path
from urllib.parse import urlparse
import requests
import speech_recognition as sr
import win32com.client
from dotenv import load_dotenv
import pyautogui
import psutil
from pycaw.pycaw import AudioUtilities
import threading
load_dotenv()

API_KEY = os.getenv("GROQ_API_KEY")
API_URL = "https://api.groq.com/openai/v1/chat/completions"
MODEL = "openai/gpt-oss-20b"
SYSTEM_PROMPT = "You are Jarvis, a friendly voice assistant. Give concise, helpful answers."
OPEN_WORDS = {"open", "launch", "start", "run"}

recognizer = sr.Recognizer()
recognizer.dynamic_energy_threshold = True
recognizer.pause_threshold = 0.8
recognizer.non_speaking_duration = 0.5
speaker = win32com.client.Dispatch("SAPI.SpVoice")
speaker.Volume = 100
speaker.Rate = 0
last_spoken_at = 0.0

FOLDERS_FILE = Path(__file__).with_name("folders.json")
WEBSITE_FILE = Path(__file__).with_name("websites.json")


def load_nicknames(path):
    try:
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {}
    return {k.lower(): v for k, v in data.items()}


def scan_apps():
    start_menus = [
        Path(os.environ.get("PROGRAMDATA", "C:/ProgramData"))
        / "Microsoft/Windows/Start Menu/Programs",
        Path(os.environ.get("APPDATA", str(Path.home() / "AppData/Roaming")))
        / "Microsoft/Windows/Start Menu/Programs",
    ]
    found = {}
    for menu in start_menus:
        if not menu.exists():
            continue
        try:
            for shortcut in menu.rglob("*.lnk"):
                name = shortcut.stem.lower()
                if "uninstall" in name:
                    continue
                found[name] = str(shortcut)
        except OSError as error:
            print(f"Couldn't scan {menu}: {error}")
    return found


apps = scan_apps()
folders = load_nicknames(FOLDERS_FILE)
web_url = load_nicknames(WEBSITE_FILE)


def speak(text):
    global last_spoken_at
    try:
        if not text:
            return
        speaker.Speak(str(text))
        last_spoken_at = time.monotonic()
    except Exception as e:
        print(f"Speech output problem: {e}")


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

def take_screenshots():
    folder = Path.home() / "Pictures" / "Screenshots"
    try:
        folder.mkdir(parents=True,exist_ok=True)
        path = folder / (time.strftime("SateL_%Y%m%d_%H%M%S") + ".png")
        pyautogui.screenshot().save(path)
    except Exception as e:
        print(f'some error occured while saving: {e}')
        speak(f'some error occured while saving: {e}')
        return
    print(f'Screenshot saved: {path}')
    speak('Screenshot saved')
    
def get_battery():
    battery = psutil.sensors_battery()
    if battery is None:
        print("i can't check battery")
        speak("Can't check that, some error occured")
        return None
    return battery.percent


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



devices = AudioUtilities.GetSpeakers()
volume_controller = devices.EndpointVolume

class VolumeControls:
    @staticmethod
    def volume_up():
        current = volume_controller.GetMasterVolumeLevelScalar()
        new_volume = min(1.0, current + 0.05)
        volume_controller.SetMasterVolumeLevelScalar(new_volume, None)
        print(f"Volume set to: {round(new_volume * 100)}%")
        speak("done")
    
    @staticmethod
    def volume_down():
        current = volume_controller.GetMasterVolumeLevelScalar()
        new_volume = max(0.0, current - 0.05)
        volume_controller.SetMasterVolumeLevelScalar(new_volume, None)
        print(f"Volume set to: {round(new_volume * 100)}%")
        speak("done")
        
    @staticmethod
    def mute():
        current_mute = volume_controller.GetMute()
        new_mute = not current_mute
        volume_controller.SetMute(new_mute, None)
        print("Muted" if new_mute else "Unmuted")
        speak("Muted" if new_mute else "Unmuted")
    
    @staticmethod
    def set_volume(level):
        if not 0 <= level <= 100:
            print("Enter a volume between 0 and 100.")
            return

        volume_controller.SetMasterVolumeLevelScalar(level / 100, None)
        print(f"Volume set to {level}%")
        speak("done")

    @staticmethod
    def get_volume():
        current = volume_controller.GetMasterVolumeLevelScalar()
        muted = volume_controller.GetMute()
        print(f"Current volume: {round(current * 100)}%" + (" (muted)" if muted else ""))
        speak(f"Volume is {round(current * 100)} percent" + (", muted" if muted else ""))
    
    
    
class FocusMode:
    def __init__(self, duration=45, focus_volume=25):
        self.active = False
        self.original_volume = None
        self.focus_volume = focus_volume
        self.duration = duration
        self.timer = None 
        self.deadline = None
        self.lock = threading.RLock()
        
        
        
        
    def start(self):
        with self.lock:
            if self.active:
                speak("Focus mode is already on")
                return
            
            self.original_volume = volume_controller.GetMasterVolumeLevelScalar()
            self.original_mute = bool(volume_controller.GetMute())
            self.active = True
            self.deadline = time.monotonic() + self.duration * 60
            try:
                volume_controller.SetMasterVolumeLevelScalar(self.focus_volume / 100 ,None)
                volume_controller.SetMute(False,None)
                
                open_folder('current project', folders)
                
                webbrowser.open("https://open.spotify.com", new=2)
                self.timer = threading.Timer(self.duration * 60, self.timer_finished)
                self.timer.daemon = True 
                self.timer.start()
            except Exception as e:
                print(f'Focus mode erro: {e}')
                speak(f"Foucs mode error:{e}")
                self.restore_audio()
                self.active = False
                self.deadline = None
                speak("can't start")
                return
            
            
            
        speak(f'focus mode started for {self.duration} minutes')
        
    def restore_audio(self):
        if self.original_volume is not None: 
            volume_controller.SetMasterVolumeLevelScalar(self.original_volume, None)
        if self.original_mute is not None: 
            volume_controller.SetMute( self.original_mute, None ) 
            
    def timer_finished(self):
        with self.lock:
            if not self.active:
                return
            
            self.active = False
            self.deadline = None
            self.timer = None
            self.restore_audio()
        print("Focus timer finished.")
        
    def stop(self):
        with self.lock:
            if not self.active:
                speak('focus mdoe is not active')
                return
            
            self.active = False
            
            if self.timer is not None: 
                self.timer.cancel() 
                self.timer = None 
                self.deadline = None 
                self.restore_audio() 
                
    def remaining_time(self):
        with self.lock:
            if not self.active or self.deadline is None:
                return None
            return max(0,int(self.deadline - time.monotonic()))
            
         
               
                
focus = FocusMode()

        
def filter_user(text):
    fillers = {"please", "open", "can", "you", "hey", "launch", "start",
               "run", "bro", "satel", "jarvis", "the"}
    return [word for word in text.lower().split() if word not in fillers]


def closest(query, names, cutoff=0.6):
    match = difflib.get_close_matches(query, names, n=1, cutoff=cutoff)
    return match[0] if match else None



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
    return closest(query, apps.keys(), cutoff=0.68)


def understand_app(user_input):
    if not API_KEY or not apps:
        return None
    names = ", ".join(sorted(apps))
    prompt = (
        "Identify which application the user wants to open. Choose only from this list: "
        f"{names}\nReturn exactly the selected app name, or none if no app fits.\n"
        f"User request: {user_input}"
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
        return result if result in apps else None
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
        return "Can't reach my AI services. Please try again."


def is_app_command(text):
    words = text.lower().split()
    while words and words[0] in {"please", "can", "you", "hey", "jarvis"}:
        words.pop(0)
    return bool(words and words[0] in OPEN_WORDS) or text.lower().strip() in apps


def handle_command(command):
    query = " ".join(filter_user(command))
    said_open = any(w in OPEN_WORDS for w in command.lower().split())
    command = command.lower().strip()
    if "start focus mode" in command:
        focus.start()
        return
    if "end focus mode" in command or "stop focus mode" in command:
        focus.stop()
        return
    
    if "time remaining" in command or "how much time left" in command:
        seconds = focus.remaining_time()
        
        if seconds is None:
            speak("Focus mode is not active.")
        else:
            minutes, seconds = divmod(seconds, 60)
            speak(f"{minutes} minutes and {seconds} seconds remaining.")

        return
    
    words = command.lower().split()
    if any(word in {"volume", "mute", "unmute", "louder", "quieter"} for word in words):
        if "unmute" in words:
            volume_controller.SetMute(False, None)
            speak("Unmuted")
        elif "mute" in words:
            volume_controller.SetMute(True, None)
            speak("Muted")
        elif "up" in words or "increase" in words or "louder" in words:
            VolumeControls.volume_up()
        elif "down" in words or "decrease" in words or "quieter" in words:
            VolumeControls.volume_down()
        elif "set" in words:
            level = next((int(word.rstrip("%")) for word in words if word.rstrip("%").isdigit()), None)
            if level is None:
                speak("Tell me a volume from 0 to 100 percent")
            else:
                VolumeControls.set_volume(level)
        else:
            VolumeControls.get_volume()
        return

    if query in web_url:
        open_url(web_url[query], query)
        return
    if "screenshot" in command.lower():
        take_screenshots()
        return
    
    if "battery" in command.lower():
        battery = get_battery()
        if battery is not None:
            print(f"Battery: {battery}%")
            speak(f"Battery is at {battery} percent")
        return
        
    if said_open and query:
        address = query.replace(" dot ", ".").replace(" slash ", "/")
        host = urlparse(address if "://" in address else f"https://{address}").hostname
        if host and "." in host:
            open_url(address)
            return


    if said_open:
        site = closest(query, web_url.keys())
        if site:
            open_url(web_url[site], site)
            return

    nickname = query if query in folders else None
    if nickname is None and said_open:
        nickname = closest(query, folders.keys())
    if nickname:
        open_folder(nickname, folders)
        return

    if is_app_command(command):
        name = find_app(command) or understand_app(command)
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
            speak("Yo what do I do?")
            command = " ".join(w for w in words if w not in {"hello", "jarvis", "satel"}).strip()
            if not command:
                continue
        else:
            command = user

        if command in {"sleep", "go to sleep", "stop listening"}:
            active = False
            print("Assistant is sleeping.")
            speak("bye")
            continue

        handle_command(command)


if __name__ == "__main__":
    main()

