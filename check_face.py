import cv2
import numpy as np
from app_paths import FACE_DETECTOR_MODEL, FACE_EMBEDDING_FILE, FACE_RECOGNIZER_MODEL



def main():
    for model_path in (FACE_DETECTOR_MODEL, FACE_RECOGNIZER_MODEL):
        if not model_path.is_file():
            raise FileNotFoundError(f"Face model not found: {model_path}")
    if not FACE_EMBEDDING_FILE.is_file():
        raise FileNotFoundError("Register a face first by running face_register.py")

    saved_faces = np.load(FACE_EMBEDDING_FILE, allow_pickle=False)
    saved_faces = saved_faces.reshape(-1, saved_faces.shape[-1])
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
        str(FACE_DETECTOR_MODEL), "", (width, height), score_threshold=0.4
    )
    recognizer = cv2.FaceRecognizerSF.create(str(FACE_RECOGNIZER_MODEL), "")
    _, faces = detector.detect(frame)
    if faces is None or len(faces) == 0:
        raise RuntimeError("No face detected.")


    aligned = recognizer.alignCrop(frame, faces[0])
    new_face = recognizer.feature(aligned)
    scores = [
        float(recognizer.match(
            saved_face.reshape(1, -1),
            new_face,
            cv2.FaceRecognizerSF_FR_COSINE,
        ))
        for saved_face in saved_faces
    ]
    print(f"Best similarity: {max(scores):.3f} (threshold: 0.363)")



if __name__ == "__main__":
    main()
