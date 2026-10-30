import cv2
import numpy as np


DETECTOR_MODEL = "face_detection_yunet_2023mar.onnx"
RECOGNIZER_MODEL = "face_recognition_sface_2021dec.onnx"


saved_face = np.load('satyam.npy')

cam = cv2.VideoCapture(0)

for _ in range(10):
    ok,frame = cam.read()    
cam.release()

if not ok or frame is None:
    raise RuntimeError("Camera capture failed")

h,w = frame.shape[:2]



detector = cv2.FaceDetectorYN.create(DETECTOR_MODEL,"",(w,h),score_threshold=0.4)
recognizer = cv2.FaceRecognizerSF.create(RECOGNIZER_MODEL,"")

_,faces = detector.detect(frame)
if faces is None:
    raise RuntimeError("No face")

aligned = recognizer.alignCrop(frame,faces[0])
new_face = recognizer.feature(aligned)


score = recognizer.match(
    saved_face,
    new_face,
    cv2.FaceRecognizerSF_FR_COSINE
)


print("Similarity:", score)
