import cv2
import numpy as np
from app_paths import FACE_DETECTOR_MODEL, FACE_EMBEDDING_FILE, FACE_RECOGNIZER_MODEL


def main():
    if not FACE_DETECTOR_MODEL.is_file() or not FACE_RECOGNIZER_MODEL.is_file():
        raise FileNotFoundError("Face detection/recognition model file is missing.")

    camera = cv2.VideoCapture(0)
    try:
        if not camera.isOpened():
            raise RuntimeError("Could not open the camera.")

        frame = None
        for _ in range(10):
            ok, current_frame = camera.read()
            if ok and current_frame is not None:
                frame = current_frame
    finally:
        camera.release()

    if frame is None:
        raise RuntimeError("Camera capture failed.")

    height, width = frame.shape[:2]
    detector = cv2.FaceDetectorYN.create(
        str(FACE_DETECTOR_MODEL), "", (width, height), score_threshold=0.5
    )
    recognizer = cv2.FaceRecognizerSF.create(str(FACE_RECOGNIZER_MODEL), "")
    _, faces = detector.detect(frame)
    if faces is None or len(faces) == 0:
        raise RuntimeError("No face detected. Try again facing the camera.")
    if len(faces) > 1:
        raise RuntimeError("More than one face detected. Make sure you are alone in view.")

    aligned = recognizer.alignCrop(frame, faces[0])
    feature = recognizer.feature(aligned)
    if feature.size == 0 or not np.isfinite(feature).all():
        raise RuntimeError("Could not create a valid face embedding.")

    FACE_EMBEDDING_FILE.parent.mkdir(parents=True, exist_ok=True)
    np.save(FACE_EMBEDDING_FILE, feature)
    print(f"Face embedding saved to {FACE_EMBEDDING_FILE}")


if __name__ == "__main__":
    main()
