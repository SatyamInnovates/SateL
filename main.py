# import subprocess
# import shutil
import speech_recognition as sr
import requests
import os,difflib
from dotenv import load_dotenv
from pathlib import Path


load_dotenv()
recognizer = sr.Recognizer()

api_key = os.getenv('GROQ_API_KEY')

def scan_apps():
    folders = [
        Path(os.environ["PROGRAMDATA"]) / "Microsoft/Windows/Start Menu/Programs",
        Path(os.environ["APPDATA"]) / "Microsoft/Windows/Start Menu/Programs",
    ]
    found = {}
    for folder in folders:
        for lnk in folder.rglob("*.lnk"):
            found[lnk.stem.lower()] = str(lnk)
    return found
apps = scan_apps()
print(list(apps.keys()))
def find_app(text):
    query = " ".join(filter_user(text))
    if not query:
        return None
    if query in apps:
        return query
    match = difflib.get_close_matches(query,apps.keys(),n=1,cutoff=0.6)
    return match[0] if match else None

def listen():
    text = ""
    with sr.Microphone() as source:
        print("Listening...")
        audio = recognizer.listen(source, timeout=5, phrase_time_limit=5)
    try:
        text = recognizer.recognize_google(audio).lower().strip()
        print(f"You said: {text}")
    except sr.UnknownValueError:
        print("Couldn't understand that.")
    except sr.RequestError as e:
        print(f"Service problem: {e}")
    return text


def understand(user_input):
    result = ""
    names = "; ".join(apps.keys())
    prompt = f'Pick the closest app from this list: {names}\nReply with exactly one name from the list, or none.\nText: "{user_input}"'
    try:
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Accept":"application/json"
        }
        
        response = requests.post("https://api.groq.com/openai/v1/chat/completions",json={"model":"openai/gpt-oss-20b","messages":[{"role":"user","content":prompt}]},headers=headers,timeout=10)
        response.raise_for_status()
        result = response.json()['choices'][0]["message"]['content'].strip()
        if not result:
            pass
    except Exception as e:
        print(f'groq error: {e}')

    return result
    




fillers = {"please", "open", "can", "you", "hey", "launch", "start","bro","satel"}

def filter_user(text):
    words = text.lower().split()
    return [w for w in words if w not in fillers]




active = False

while True:
    user = listen()

    if not user:
        continue

    user = user.lower().strip()
    words = user.split()

    if user == "exit":
        print("Shutting down assistant.")
        break

    if not active:
        if "hello" not in words:
            continue

        active = True
        print("Assistant activated!")


        command = " ".join(
            word for word in words if word != "hello"
        ).strip()

        if not command:
            continue
    else:
        command = user

 
    if "sleep" in command.split():
        active = False
        print("Assistant is sleeping.")
        continue

   
    name = find_app(command)

    if name is None:
        result = understand(command).lower().strip()
        if result in apps:
            name = result

    if name in apps:
        try:
            os.startfile(apps[name])
            print(f"Opening {name}")
        except OSError as e:
            print(f"Could not open {name}: {e}")
    else:
        print("I don't know that application.")

