# SateL

SateL is a Windows desktop voice assistant written in Python. It has a small Tkinter window for typed commands, a conversation log, face and focus status, and upcoming reminders. When a microphone is available, SateL listens for a wake word and can answer general questions through the Groq API. It can also open websites and Start Menu apps, adjust Windows volume, take screenshots, report battery status, run a timed focus session, set reminders, and use the camera for face verification or visual questions.

The app is designed for Windows: it uses Windows speech output, Windows audio controls, Start Menu shortcuts, and Windows paths. The camera features use the included YuNet and SFace OpenCV models.

## Features

- **Talk to SateL:** Say “hello,” “SateL,” or “Jarvis” to get started. You can also type to SateL in its window. Or if you have runned face_register it would scan your face and start itself
- **Ask questions:** Ask SateL a question and hear its answer. This needs an internet connection and a Groq API key.
- **Open things quickly:** Ask SateL to open a website, an app on your computer, or one of your saved project folders.
- **Set reminders:** Ask SateL to remind you about something after a few seconds, minutes, or hours. Your reminders appear in the app window.
- **Control sound:** Turn the volume up or down, set a volume level, or mute and unmute your computer.
- **Focus with music:** Start a 45-minute focus session. SateL opens your project and Spotify, lowers the volume, and restores your previous sound settings when the session ends.
- **Use your camera:** Register your face to let SateL recognize you, or ask what it sees. Camera questions need an internet connection and a Groq API key.
- **Quick checks:** Ask for your battery level or take a screenshot of your screen.
- **User Chek:** It checks peridocially that is this you using or not by scanning your face and stops if someone else is working

## Install from a GitHub release

1. Open the [SateL Releases page](https://github.com/SatyamInnovates/SateL/releases/tag/v1.0.0).
2. Downlaod the SateL-v1.0.0-Windows.zip in your C:
3. Extract the downloaded archive to a folder you can write to, such as `C:\Satel` or `Documents\SateL`. Keep the extracted folder structure intact; the packaged build includes supporting files and the face models.
4. Run `FaceRegister` from the extracted folder. It will open your camera. Look at your camera move your head slowly left and right. It will auto close if requiremtns meet
5. Run `SateL.exe` from the extracted folder. Windows may ask you to confirm that you want to run an app downloaded from the internet.


### Configure the Groq API key

AI answers, AI-assisted app matching, and camera image analysis require a Groq API key. In the same folder as `SateL.exe`, create a text file named `.env` with this line:

```text
GROQ_API_KEY=your_groq_api_key
```

Save it as `.env` (not `.env.txt`), then restart SateL. Keep the key private and do not upload it to GitHub. Local commands such as reminders, volume control, screenshots, and configured website opening work without a key.

### Register your face from a release (optional)

If the release includes `FaceRegister.exe`, run it from its extracted folder and follow the camera window prompts. Keep only one person in frame, face the camera, use clear lighting, and turn your head slightly as prompted. Registration collects eight clear samples; press **Esc** to cancel. The saved face embedding is stored in `%LOCALAPPDATA%\SateL\face.npy`.


## Voice and text commands
Please talk patently and little loudly
Imp: if you have registerda your face then wait a little it will scan your face and start SateL if it matches othweise say Hello or type to start it
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
you just need to say set a reminder for _ minutes then satel will aks and tell what you want to make the reminder for.
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
