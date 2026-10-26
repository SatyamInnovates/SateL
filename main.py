import subprocess
import shutil
import speech_recognition as sr

recognizer = sr.Recognizer()


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




fillers = {"please", "open", "can", "you", "hey", "launch", "start","bro","satel"}

def filter_user(text):
    words = text.lower().split()
    return [w for w in words if w not in fillers]

def open_notepad():
    subprocess.Popen(['notepad'])

def open_vscode():
    path = shutil.which('code')
    if path is None:
        print('VS Code not found')
        return
    subprocess.Popen([path])

apps = {'vscode':open_vscode,"notepad":open_notepad}

while True:
    user = listen()
    if not user:
        continue
    if user == "exit":
        break
    
    words = filter_user(user)
    for w in words:
        if w in apps:
            apps[w]()
            break
    else:
        print("i don't know that")
    
             
