# PersonaAI - vision/tracker.py
#
# Follows the closest person with the head. Simple version: find faces,
# pick the biggest one, turn toward it smoothly.

import threading
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Optional, Sequence

from persona.hardware.base import Expression


@dataclass
class Face:
    x: int  # top-left, pixels
    y: int
    w: int
    h: int

    @property
    def center(self) -> tuple[float, float]:
        return self.x + self.w / 2, self.y + self.h / 2

    @property
    def area(self) -> int:
        return self.w * self.h


class FaceDetector(ABC):
    @abstractmethod
    def detect(self, frame) -> Sequence[Face]:
        """Return all faces in the frame."""


class HaarDetector(FaceDetector):
    """OpenCV Haar detector. Not great, but needs nothing extra."""

    def __init__(self):
        import cv2

        self._cv2 = cv2
        self._cascade = cv2.CascadeClassifier(
            cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
        )

    def detect(self, frame) -> Sequence[Face]:
        gray = self._cv2.cvtColor(frame, self._cv2.COLOR_BGR2GRAY)
        found = self._cascade.detectMultiScale(gray, 1.1, 5)
        return [Face(int(x), int(y), int(w), int(h)) for (x, y, w, h) in found]


def pick_closest(faces: Sequence[Face]) -> Optional[Face]:
    """Biggest face = closest person."""
    return max(faces, key=lambda f: f.area, default=None)


def to_gaze(face: Face, frame_w: int, frame_h: int) -> tuple[float, float]:
    """Pixels to -1..1."""
    cx, cy = face.center
    return (2 * cx / frame_w - 1), -(2 * cy / frame_h - 1)


class FaceFollower:
    """Follows the closest face. Lower smoothing = slower, calmer."""

    def __init__(self, body: Expression, detector: Optional[FaceDetector] = None,
                 camera_index: int = 0, smoothing: float = 0.3):
        self.body = body
        self.detector = detector
        self.camera_index = camera_index
        self.smoothing = smoothing
        self._run = threading.Event()
        self._thread: Optional[threading.Thread] = None
        self._gaze = (0.0, 0.0)

    def start(self) -> None:
        if self._thread and self._thread.is_alive():
            return
        self._run.set()
        self._thread = threading.Thread(target=self._loop, daemon=True)
        self._thread.start()

    def stop(self, center: bool = True) -> None:
        self._run.clear()
        if self._thread:
            self._thread.join(timeout=2)
        if center:
            self.body.look(0.0, 0.0)

    def _loop(self) -> None:
        import cv2

        detector = self.detector or HaarDetector()
        cap = cv2.VideoCapture(self.camera_index)
        try:
            while self._run.is_set():
                ok, frame = cap.read()
                if not ok:
                    time.sleep(0.1)
                    continue
                target = pick_closest(detector.detect(frame))
                if target is None:
                    continue
                h, w = frame.shape[:2]
                tx, ty = to_gaze(target, w, h)
                gx, gy = self._gaze
                a = self.smoothing
                self._gaze = (gx + a * (tx - gx), gy + a * (ty - gy))
                self.body.look(*self._gaze)
        finally:
            cap.release()
