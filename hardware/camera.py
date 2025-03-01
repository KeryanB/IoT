import cv2

class Camera:
    def __init__(self):
        self.cap = cv2.VideoCapture(0)

    def scan_face(self):
        while True:
            ret, frame = self.cap.read()
            if not ret:
                break
            cv2.imshow('Camera', frame)
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break
        self.cap.release()
        cv2.destroyAllWindows()
