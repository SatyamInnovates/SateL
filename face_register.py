import time
import cv2
import numpy as np

from app_paths import FACE_DETECTOR_MODEL, FACE_EMBEDDING_FILE, FACE_RECOGNIZER_MODEL


SAMPLE_COUNT = 8
SAMPLE_INTERVAL = 0.6
CAPTURE_TIMEOUT = 30
MIN_FACE_SIZE = 90
MIN_SHARPNESS = 25.0


def main():
    if not FACE_DETECTOR_MODEL.is_file() or not FACE_RECOGNIZER_MODEL.is_file():
        raise FileNotFoundError("Face detection/recognition model file is missing.")

    camera = cv2.VideoCapture(0)
    if not camera.isOpened():
        camera.release()
        raise RuntimeError("Could not open the camera.")

    detector = None
    recognizer = cv2.FaceRecognizerSF.create(str(FACE_RECOGNIZER_MODEL), "")
    features = []
    started_at = time.monotonic()
    last_sample_at = 0.0
    status = "Look straight at the camera. Press Esc to cancel."

    print("Face registration started. Follow the instructions in the camera window.")
    try:
        while len(features) < SAMPLE_COUNT:
            if time.monotonic() - started_at >= CAPTURE_TIMEOUT:
                raise RuntimeError(
                    f"Only captured {len(features)} clear samples. Improve the lighting and try again."
                )

            ok, frame = camera.read()
            if not ok or frame is None:
                status = "Camera frame unavailable; checking again..."
                continue

            height, width = frame.shape[:2]
            if detector is None:
                detector = cv2.FaceDetectorYN.create(
                    str(FACE_DETECTOR_MODEL), "", (width, height), score_threshold=0.4
                )
            else:
                detector.setInputSize((width, height))

            _, faces = detector.detect(frame)
            face = faces[0] if faces is not None and len(faces) == 1 else None
            preview = frame.copy()

            if faces is not None and len(faces) > 1:
                status = "Only one person should be in the camera view."
            elif face is None:
                status = "No face found. Face the camera and improve the lighting."
            else:
                x, y, face_width, face_height = face[:4].astype(int)
                confidence = float(face[14])
                cv2.rectangle(
                    preview,
                    (x, y),
                    (x + face_width, y + face_height),
                    (0, 220, 0),
                    2,
                )

                if min(face_width, face_height) < MIN_FACE_SIZE:
                    status = "Move a little closer to the camera."
                elif confidence < 0.65:
                    status = "Face not clear enough; face the camera."
                elif time.monotonic() - last_sample_at >= SAMPLE_INTERVAL:
                    aligned = recognizer.alignCrop(frame, face)
                    sharpness = cv2.Laplacian(
                        cv2.cvtColor(aligned, cv2.COLOR_BGR2GRAY), cv2.CV_64F
                    ).var()
                    if sharpness < MIN_SHARPNESS:
                        status = "Hold still for a sharper sample."
                    else:
                        feature = recognizer.feature(aligned)
                        if feature.size and np.isfinite(feature).all():
                            features.append(feature.reshape(-1))
                            last_sample_at = time.monotonic()
                            if len(features) < 3:
                                status = "Good. Keep facing forward."
                            elif len(features) < 6:
                                status = "Good. Turn your head slightly left."
                            else:
                                status = "Good. Turn your head slightly right."
                        else:
                            status = "Could not read that sample; hold still and try again."

            cv2.putText(
                preview,
                status,
                (15, 30),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.65,
                (255, 255, 255),
                2,
                cv2.LINE_AA,
            )
            cv2.putText(
                preview,
                f"Clear samples: {len(features)}/{SAMPLE_COUNT}",
                (15, 60),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.65,
                (255, 255, 255),
                2,
                cv2.LINE_AA,
            )
            cv2.imshow("SateL Face Registration", preview)
            if cv2.waitKey(1) & 0xFF == 27:
                raise RuntimeError("Face registration cancelled.")
    finally:
        camera.release()
        cv2.destroyAllWindows()

    FACE_EMBEDDING_FILE.parent.mkdir(parents=True, exist_ok=True)
    np.save(FACE_EMBEDDING_FILE, np.stack(features).astype(np.float32))
    print(f"Saved {len(features)} face samples to {FACE_EMBEDDING_FILE}")


if __name__ == "__main__":
    main()
