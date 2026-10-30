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
from datetime import datetime
import base64
# import winsound
# from google.cloud import texttospeech
import asyncio,uuid,tempfile
import edge_tts
import pygame
import cv2
import numpy as np
from PIL import Image



load_dotenv()

# SERVICE_ACCOUNT_PATH = Path(__file__).with_name("ttsprojecttest1-26be1c6f3488.json")
# tts_client = None

API_KEY = os.getenv("GROQ_API_KEY")
API_URL = "https://api.groq.com/openai/v1/chat/completions"
MODEL = "openai/gpt-oss-20b"
VISION_MODEL = "qwen/qwen3.8-27b"
SYSTEM_PROMPT = "You are Jarvis, a friendly voice assistant. Give concise, helpful answers."
OPEN_WORDS = {"open", "launch", "start", "run"}
VOICE = "en-US-RogerNeural"
pygame.mixer.init()
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
FACE_EMBEDDING_FILE = Path(__file__).with_name("data") / "face.npy"
FACE_DETECTOR_MODEL = Path(__file__).with_name("models") / "face_detection_yunet_2023mar.onnx"
FACE_RECOGNIZER_MODEL = Path(__file__).with_name("models") / "face_recognition_sface_2021dec.onnx"
FACE_MATCH_THRESHOLD = 0.363
FACE_PRESENCE_INTERVAL = 60
face_is_present = False
CONVERSATION_FILE = Path(__file__).with_name("conversations") / "conversation.txt"
MAX_HISTORY_MESSAGES = 12  


cap = None

def load_conversation():
    messages = [{"role": "system", "content": SYSTEM_PROMPT}]
    try:
        contents = CONVERSATION_FILE.read_text(encoding="utf-8")
    except FileNotFoundError:
        return messages
    

    for block in contents.split("=" * 60):
        
        lines = block.strip().splitlines()
        question = next((line[len("Question : "):] for line in lines
                         if line.startswith("Question : ")), None)
        answer_index = next((i for i, line in enumerate(lines)
                             if line.startswith("Answer: ")), None)
        if question is None or answer_index is None:
            continue
        answer_lines = [lines[answer_index][len("Answer: "):]]
        answer_lines.extend(lines[answer_index + 1:])
        answer = "\n".join(answer_lines).strip()
        if question.strip() and answer:
            messages.extend([
                {"role": "user", "content": question.strip()},
                {"role": "assistant", "content": answer},
            ])

    return [messages[0], *messages[-MAX_HISTORY_MESSAGES:]]


conversation_history = load_conversation()



def save_conversation(question,answer):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    CONVERSATION_FILE.parent.mkdir(parents=True, exist_ok=True)
    with CONVERSATION_FILE.open('a', encoding='utf-8') as f:
        f.write(f"\n{'='*60}\n")
        f.write(f"Timestamp: {timestamp}\n")
        f.write(f"Question : {question}\n")
        f.write(f"Answer: {answer}\n")
        f.write(f"{'='*60}\n")


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

async def _make_audio(text, path):
    await edge_tts.Communicate(text, VOICE,rate="-5%",pitch="-7Hz").save(path)
    
    
    
def speak(text):
    global last_spoken_at
    path = os.path.join(tempfile.gettempdir(), f"satel_{uuid.uuid4().hex}.mp3")
    if not text:
        return
    edge_spoken = False
    fallback_spoken = False
    try:
        asyncio.run(_make_audio(text,path))
        pygame.mixer.music.load(path)
        pygame.mixer.music.play()
        while pygame.mixer.music.get_busy():
            pygame.time.Clock().tick(10)
        edge_spoken = True
        pygame.mixer.music.unload()
        last_spoken_at = time.monotonic()
    except Exception as error:
        print(f"TTS PROBLEM  using Windows voice: {error}")
        if not edge_spoken:
            speaker.Speak(text)
            fallback_spoken = True
            last_spoken_at = time.monotonic()
    finally:
        try:
            os.remove(path)
        except OSError:
            pass 
        if not edge_spoken and not fallback_spoken:
            try:
                speaker.Speak(str(text))
                last_spoken_at = time.monotonic()
            except Exception as fallback_error:
                print(f"Speech output problem: {fallback_error}")


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
                recognizer.adjust_for_ambient_noise(source, duration=0.5)
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
        
        
        
def vision(question):
    camera = cv2.VideoCapture(0)
    
    try:
        if not camera.isOpened():
            return "I can't see a camera"

        frame = None
        for _ in range(3):
            ret, current_frame = camera.read()
            if ret:
                frame = current_frame
        if frame is None:
            return "I couldn't capture an image from the camera."
    finally:
        camera.release()

    encoded, image_buffer = cv2.imencode(
        ".jpg", frame, [cv2.IMWRITE_JPEG_QUALITY, 85]
    )
    
    if not encoded:
        return "I couldn't prepare the camera image."
    image_base64 = base64.b64encode(image_buffer.tobytes()).decode("ascii")

    if not API_KEY:
        return "The Groq API key isn't configured."

    try:
        payload = {
            "model": VISION_MODEL,
            "messages": [
                
                {
                    "role": "system",
                    "content": (
                        "You are Jarvis. Answer questions about the camera image "
                        "concisely. Describe only what is visible and say when unsure."
                    ),
                },
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": question},{"type": "image_url","image_url": {
                        "url": f"data:image/jpeg;base64,{image_base64}"},},],},
                ],
            "temperature": 0.4,
            "max_completion_tokens": 400,
        }
        response = requests.post(
            API_URL,
            headers={
                "Authorization": f"Bearer {API_KEY}",
                "Content-Type": "application/json",
            },
            json=payload,
            timeout=60,
        )
        response.raise_for_status()
        answer = response.json()["choices"][0]["message"]["content"]
        return answer.strip() if answer else "I couldn't understand the image response."
    except (requests.RequestException, KeyError, IndexError, TypeError, ValueError) as error:
        print(f"Groq vision problem: {error}")
        return "I couldn't analyze the camera image. Check the connection and Groq model access."


def check_registered_face():
    if not FACE_EMBEDDING_FILE.is_file():
        
        return None, "No face is registered yet. Run face_register.py first"
    if not FACE_DETECTOR_MODEL.is_file() or not FACE_RECOGNIZER_MODEL.is_file():
        return None, "The face recognition model files are missing."

    camera = cv2.VideoCapture(0)
    try:
        if not camera.isOpened():
            return None, "I can't access the camera for face verification light up your room."

        frame = None
        for _ in range(5):
            ok, current_frame = camera.read()
            if ok and current_frame is not None:
                frame = current_frame
        if frame is None:
            return None, "I couldn't capture an image for face verification."
    finally:
        camera.release()

    try:
        saved_feature = np.load(FACE_EMBEDDING_FILE, allow_pickle=False)
        if saved_feature.size == 0 or not np.isfinite(saved_feature).all():
            return None, "The saved face data is invalid. Register your face again."

        h, w = frame.shape[:2]
        detector = cv2.FaceDetectorYN.create(
            str(FACE_DETECTOR_MODEL), "", (w, h), score_threshold=0.5
        )
        recognizer = cv2.FaceRecognizerSF.create(str(FACE_RECOGNIZER_MODEL), "")
        detector.setInputSize((w, h))
        _, faces = detector.detect(frame)
        if faces is None or len(faces) == 0:
            return False, "I couldn't find a face. Please try again facing the camera."
        if len(faces) > 1:
            return False, "I see more than one face. Please have only one person in view."

        aligned = recognizer.alignCrop(frame, faces[0])
        current_feature = recognizer.feature(aligned)
        score = float(recognizer.match(
            saved_feature,
            current_feature,
            cv2.FaceRecognizerSF_FR_COSINE,
        ))
        print(f"Face similarity: {score:.3f}")
        if score >= FACE_MATCH_THRESHOLD:
            return True, "User has arrived."
        return False, "I couldn't verify that face."
    except (cv2.error, OSError, ValueError) as error:
        print(f"Face verification problem: {error}")
        return None, "Face verification failed. Check the saved face data and model files."



def verify_face():
    _, message = check_registered_face()
    return message
   
   
    
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
                "messages": [*conversation_history,
                             {"role": "user", "content": user_input}],
                "temperature": 0.7,
                "max_tokens": 250,
            },
            timeout=20,
        )
        response.raise_for_status()
        answer = response.json()["choices"][0]["message"]["content"].strip()
    
        conversation_history.extend([
            {'role':'user','content':user_input},
            {'role':'assistant',"content":answer}
        ])
        del conversation_history[1:-MAX_HISTORY_MESSAGES]
        return answer
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
    vision_phrases = (
        "what do you see",
        "what can you see",
        "describe what you see",
        "look at this",
        "what is in front of me",
        "what's in front of me",
        "analyze camera",
        "what's near me",
    )
    if any(phrase in command for phrase in vision_phrases):
        answer = vision(command)
        print(f"Jarvis: {answer}")
        speak(answer)
        return

    if command in {"verify face", "verify my face", "check my face", "recognize me"}:
        global face_is_present
        match, answer = check_registered_face()
        if match is not None:
            face_is_present = match
        print(f"Jarvis: {answer}")
        speak(answer)
        return



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
    if answer != "Can't reach my AI services. Please try again." and not answer.startswith("API KEY"):
        save_conversation(command, answer)
    speak(answer)
    print(f"Jarvis: {answer}")


def main():
    global face_is_present
    active = False
    last_presence_check = 0.0
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
        now = time.monotonic()
        if now - last_presence_check >= FACE_PRESENCE_INTERVAL:
            last_presence_check = now
            match, message = check_registered_face()
            if match is True and not face_is_present:
                face_is_present = True
                print(f"Jarvis: {message}")
                speak(message)
            elif match is False:
                face_is_present = False
            elif match is None:
                print(f"Presence check skipped: {message}")

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


