import os
import shutil
import sys
from pathlib import Path


RESOURCE_DIR = Path(__file__).resolve().parent
APP_DIR = (
    Path(sys.executable).resolve().parent
    if getattr(sys, "frozen", False)
    else RESOURCE_DIR
)

LOCAL_APP_DATA = Path(
    os.environ.get(
        "LOCALAPPDATA",
        Path.home() / "AppData" / "Local",
    )
)
USER_DATA_DIR = LOCAL_APP_DATA / "SateL"
USER_DATA_DIR.mkdir(parents=True, exist_ok=True)


def user_data_file(filename, bundled_seed=None):
  
    destination = USER_DATA_DIR / filename
    if destination.exists() or bundled_seed is None:
        return destination

    source = RESOURCE_DIR / bundled_seed
    if source.is_file():
        try:
            shutil.copy2(source, destination)
        except OSError:
            pass
    return destination


FOLDERS_FILE = user_data_file("folders.json", Path("folders.json"))
WEBSITE_FILE = user_data_file("websites.json", Path("websites.json"))
FACE_EMBEDDING_FILE = user_data_file("face.npy", Path("data") / "face.npy")
REMINDERS_FILE = user_data_file("reminders.json", Path("reminders.json"))
CONVERSATION_FILE = user_data_file(
    "conversation.txt",
    Path("conversations") / "conversation.txt",
)

FACE_DETECTOR_MODEL = RESOURCE_DIR / "models" / "face_detection_yunet_2023mar.onnx"
FACE_RECOGNIZER_MODEL = RESOURCE_DIR / "models" / "face_recognition_sface_2021dec.onnx"
