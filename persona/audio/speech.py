# PersonaAI - audio/speech.py
#
# Listening and talking. In this version you type instead of speaking, and
# the answer is printed.

import queue
import re
import threading
import time
from abc import ABC, abstractmethod
from typing import Callable, Optional

from persona.audio.jaw import envelope_to_openness


class SpeechIn(ABC):
    @abstractmethod
    def listen(self, timeout: float) -> Optional[str]:
        """Return what was said, or None."""

    def inject(self, text: str) -> None:
        """Add text from somewhere else."""


class SpeechOut(ABC):
    @abstractmethod
    def say(self, text: str, on_level: Callable[[float], None]) -> bool:
        """Speak and call on_level(0..1) for the jaw. False if interrupted."""

    @abstractmethod
    def interrupt(self) -> None:
        """Stop talking."""


class KeyboardInput(SpeechIn):
    """Type instead of talking."""

    def __init__(self):
        self._q: "queue.Queue[str]" = queue.Queue()
        threading.Thread(target=self._reader, daemon=True).start()

    def _reader(self):
        while True:
            try:
                line = input()
            except EOFError:
                self._q.put("quit")
                return
            if line.strip():
                self._q.put(line.strip())

    def listen(self, timeout: float) -> Optional[str]:
        try:
            return self._q.get(timeout=timeout)
        except queue.Empty:
            return None

    def inject(self, text: str) -> None:
        self._q.put(text)


class ConsoleVoice(SpeechOut):
    """Prints the reply and fakes the jaw movement."""

    FRAME_S = 0.08

    def __init__(self):
        self._stop = threading.Event()

    def say(self, text: str, on_level: Callable[[float], None]) -> bool:
        self._stop.clear()
        print(f"  \033[36mrobot:\033[0m {text}")
        envelope = _fake_envelope(text)
        for openness in envelope_to_openness(envelope):
            if self._stop.is_set():
                on_level(0.0)
                return False
            on_level(openness)
            time.sleep(self.FRAME_S)
        on_level(0.0)
        return True

    def interrupt(self) -> None:
        self._stop.set()


def _fake_envelope(text: str) -> list[float]:
    """Vowels loud, consonants quiet, spaces silent."""
    levels = []
    for ch in text.lower()[:200]:
        if re.match(r"[aeiouăâîy]", ch):
            levels.append(1.0)
        elif ch.isalpha():
            levels.append(0.4)
        else:
            levels.append(0.0)
    return levels
