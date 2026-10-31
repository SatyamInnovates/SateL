# SateL

SateL is a Windows desktop voice assistant written in Python. It has a small Tkinter window for typed commands, a conversation log, face and focus status, and upcoming reminders. When a microphone is available, SateL listens for a wake word and can answer general questions through the Groq API. It can also open websites and Start Menu apps, adjust Windows volume, take screenshots, report battery status, run a timed focus session, set reminders, and use the camera for face verification or visual questions.

The app is designed for Windows: it uses Windows speech output, Windows audio controls, Start Menu shortcuts, and Windows paths. The camera features use the included YuNet and SFace OpenCV models.

## Features

- Wake by saying **hello**, **SateL**, or **Jarvis**. Face recognition can also activate the assistant when a registered face is seen.
- Type commands into the app window if you do not have a working microphone.
- Ask general questions using the Groq chat API.
- Open configured websites, installed Start Menu apps, and configured project folders in VS Code.
- Set, view, and receive timed reminders.
- Control Windows master volume and mute state.
- Start a 45-minute focus session that sets volume to 25%, opens the current project in VS Code, and opens Spotify. Stop it early to restore the previous audio settings.
- Take a screenshot, check battery percentage, verify a face, or ask a question about the camera view.

## Requirements

- Windows 10 or 11
- Python 3.10 or newer (64-bit recommended)
- A microphone for voice commands, and a webcam for face and camera features
- Internet access for speech recognition, Groq AI, and opening web services
- A Groq API key for AI questions, AI-assisted app matching, and camera image analysis
- VS Code installed and available as `code` on `PATH` to open project folders or use focus mode as configured

## Install and run from source

Open PowerShell in the project folder (`C:\SateL` in this checkout), then create and activate a virtual environment:

```powershell
py -3 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

If PowerShell blocks activation, either allow scripts for this terminal with `Set-ExecutionPolicy -Scope Process Bypass` and activate again, or skip activation and run the environment's Python directly:

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe main.py
```

Create a `.env` file beside `main.py` and set your own Groq key:

```text
GROQ_API_KEY=your_groq_api_key
```

Keep the key private. The app reads it when it starts. Without it, local commands such as volume control, reminders, screenshots, and configured website opening still work, but AI answers, AI-assisted app matching, and camera analysis will not.

Start the assistant:

```powershell
python main.py
```

The Tkinter window opens and the assistant tries to initialize the microphone. To exit, type `exit` in the command box or close the window. The assistant may also be started as a packaged application from a PyInstaller build; the checked-in spec files are `SateL.spec` and `FaceRegister.spec`.

## Register your face (optional)

Face registration stores face embeddings locally, not camera images. With the webcam available, run:

```powershell
python face_register.py
```

Follow the on-screen prompts. Keep only one person in frame, face the camera, use clear lighting, and follow prompts to turn your head slightly. Registration collects eight clear samples. Press **Esc** in the camera window to cancel. To compare a fresh camera sample with the registered face, run:

```powershell
python check_face.py
```

The models are in `models/`. The embedding is stored under `%LOCALAPPDATA%\SateL\face.npy` when launched from source or a packaged build. In the running assistant, face checks happen periodically; a registered face can activate it. You can also ask for a one-off check with `hello, verify my face`.

## Voice and text commands

Voice commands are available after the assistant starts listening. Say **hello**, **SateL**, or **Jarvis** to wake it; for example, “Hello, what time is it?” When it is awake, say the command without the wake word. Say **sleep** or **stop listening** to pause voice command handling; say the wake word again to resume. You can also type any command directly into the app's command box. Typed commands do not need a wake word and work if microphone setup fails.

Speech recognition uses the `en-IN` Google recognizer through SpeechRecognition, so it needs an internet connection. Speech output uses Windows SAPI with Edge TTS fallback behavior in the app.

### Wake and general conversation

| Say or type | What it does |
| --- | --- |
| `hello` | Wake the voice assistant. |
| `hello, how are you?` | Wake and send the rest as a question. |
| `SateL, explain photosynthesis` | Same wake-word pattern using SateL's name. |
| `sleep` / `go to sleep` / `stop listening` | Pause voice command handling until the next wake word. |
| `exit` / `quit` / `shutdown` | Stop the assistant. |
| `What is a black hole?` | Ask a general question (when awake, or type it). Requires a valid Groq key and internet. |

### Reminders

Reminders are relative durations in seconds, minutes, or hours. Numbers can be digits or supported spoken numbers from zero through ninety-nine (for example, `one`, `twenty`, or `twenty one`).

| Say or type | What it does |
| --- | --- |
| `Set a reminder in 10 minutes to stretch` | Creates a reminder in one command. |
| `Remind me to call Mom in one hour` | Creates a reminder using the alternate phrasing. |
| `Remind me in 5 minutes` then `take the laundry out` | SateL asks what to remind you about; give the task as your next command within 30 seconds. |
| `Show reminders` / `List reminders` / `What are my reminders?` | Reads pending reminders aloud. They also appear in the app window. |
| `Cancel` | Cancels the pending two-step reminder prompt. |

Due reminders are spoken while SateL is running. Reminder data is saved locally and survives restarts; reminders are not delivered while the app is closed.

### Open websites, apps, and folders

| Say or type | What it does |
| --- | --- |
| `Open YouTube` / `Launch Google` | Opens a website listed in `websites.json`. The default list includes Google, YouTube, ChatGPT, GitHub, and others. |
| `Open example.com` | Opens a valid web address. |
| `Open Notepad` | Opens a matching Windows Start Menu app. Matching can use the Groq key when the app name is unclear. |
| `Open current project` | Opens the configured folder in VS Code. |

Edit `websites.json` to add site names and URLs. Edit `folders.json` to add folder nicknames and local paths. Folder opening requires VS Code's `code` command to be available. App discovery scans Start Menu shortcuts at launch, so an app that has no Start Menu entry may not be found.

### Windows and focus controls

| Say or type | What it does |
| --- | --- |
| `Volume up` / `Make it louder` | Raises master volume by 5 percentage points. |
| `Volume down` / `Make it quieter` | Lowers master volume by 5 percentage points. |
| `Set volume to 40 percent` | Sets master volume from 0 to 100. |
| `What is the volume?` | Reports current master volume and mute state. |
| `Mute` / `Unmute` | Mutes or unmutes Windows audio. |
| `Start focus mode` | Starts a 45-minute session, sets volume to 25%, opens the configured current project in VS Code, and opens Spotify. Restores the previous volume and mute state when stopped or when the timer ends. |
| `How much time left?` / `Time remaining` | Reports remaining focus time. |
| `Stop focus mode` / `End focus mode` | Ends focus mode and restores prior audio settings. |

### Camera, screenshot, and battery

| Say or type | What it does |
| --- | --- |
| `Take a screenshot` | Saves a PNG in your `Pictures\Screenshots` folder. |
| `Check my battery` | Reads the battery percentage when Windows exposes battery status (typically on laptops). |
| `Verify my face` / `Recognize me` | Compares the camera view with a face registered using `face_register.py`. |
| `What do you see?` / `What am I holding?` | Captures a camera image and asks the configured Groq vision model to describe it. Requires a webcam, internet, and a valid Groq key. |

## Project files and local data

- `main.py` — assistant startup, microphone loop, command routing, reminders, camera, audio, and AI API calls.
- `welcome.py` — Tkinter app window, conversation log, reminder list, and typed command input.
- `face_register.py`, `check_face.py` — face enrollment and standalone verification tools.
- `app_paths.py` — source/bundle resource paths and per-user data paths.
- `models/` — YuNet face detector and SFace face recognizer models required for face features.
- `websites.json`, `folders.json` — editable website shortcuts and folder nicknames.
- `requirements.txt` — Python package dependencies.
- `SateL.spec`, `FaceRegister.spec` — PyInstaller build specifications.

Mutable files are copied to `%LOCALAPPDATA%\SateL\` on first run (including reminders, conversation history, website/folder configuration, and registered face data). This lets the packaged app write user data without changing its install directory. When you edit the JSON configuration for an existing install, edit the copies in `%LOCALAPPDATA%\SateL\` as well.

## Common errors and fixes

### `ModuleNotFoundError` when starting

The dependencies are missing from the Python environment used to start SateL. Activate `.venv` and run `python -m pip install -r requirements.txt` again. Make sure the same Python runs both the install and `main.py` commands (`python -c "import sys; print(sys.executable)"`).

### PyAudio installation fails or `No Default Input Device Available`

SpeechRecognition needs PyAudio to access the microphone. Confirm Windows has a microphone selected and enabled in **Settings → System → Sound → Input**, then check Windows microphone privacy permissions. If `pip install -r requirements.txt` fails specifically on PyAudio, use a supported 64-bit Python version and resolve the PyAudio wheel/build requirement for that Python version before rerunning the install. SateL falls back to text commands when microphone initialization fails; use the command box in the meantime.

### Voice commands are ignored or transcribed incorrectly

Speak after SateL has started, wait for microphone calibration, and use a quiet room. Confirm the correct input device is the Windows default and that the computer is online. The recognizer is configured for Indian English (`en-IN`); noisy audio, a different spoken language/accent, or a network outage can cause empty or incorrect transcripts. Typed commands are a fallback.

### `GROQ_API_KEY` missing, unauthorized, or AI unavailable

Check that `.env` is next to `main.py` and contains `GROQ_API_KEY=...` with a valid key and no surrounding quotes or extra spaces. Restart SateL after changing it. Check internet access, key validity/permissions, and the Groq API/model availability. Basic local commands do not require the key. Do not commit or share `.env`.

### Camera cannot open, no face found, or model file missing

Close other camera apps, check Windows camera privacy permissions, and confirm the webcam works in the Camera app. Improve lighting, face the camera, move closer, hold still, and ensure only one face is in view during registration. Confirm both `.onnx` model files are present under `models/`; packaged runs also need those models included beside the executable as specified in `SateL.spec`.

### Face is not recognized

Run `python face_register.py` again in clear, even lighting. Make sure the active camera is the same and only one face is visible. Registration data lives at `%LOCALAPPDATA%\SateL\face.npy`; if it is stale or damaged, re-register to replace it. Face matching can vary with lighting, camera angle, and appearance.

### Reminder does not fire or is not saved

Use a positive relative duration with seconds, minutes, or hours, such as `remind me in 5 minutes to stretch`. If SateL asks what to remind you about, give the task within 30 seconds. Reminders only fire while the assistant is running. Check that `%LOCALAPPDATA%\SateL\reminders.json` is writable and contains valid JSON if saving fails.

### Website does not open

Check the URL in `websites.json`, include a valid domain, and make sure Windows has a default browser configured. For a custom site, say `open example.com` or add a name and URL to the configuration file. If the app has already run once, edit `%LOCALAPPDATA%\SateL\websites.json` rather than the project seed file.

### App or project folder cannot be opened

Apps must be discoverable from a Windows Start Menu shortcut. For folders, correct the path in `%LOCALAPPDATA%\SateL\folders.json` and make sure it exists. Install VS Code and ensure `code` is available on `PATH` to open folders. Restart SateL after changing configuration.

### Volume or focus mode fails

These controls use the Windows default audio endpoint. Check that a playback device is enabled and available. Focus mode also opens the configured `current project` in VS Code and Spotify; fix the folder path or install VS Code if those actions fail. It restores the prior volume and mute state when it completes normally.

### Battery command says it cannot check

Windows may not report battery status on a desktop or when the battery driver does not expose it. The command works only when the system returns battery information.

## Development notes

Run the assistant with `python main.py`. The face tools can be run independently as shown above. The repository does not currently define an automated test command. The application makes network requests for speech recognition and Groq AI; do not send private information in prompts unless you are comfortable with those services receiving it.
