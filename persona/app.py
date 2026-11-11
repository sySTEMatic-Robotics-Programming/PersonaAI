# PersonaAI - app.py
#
# The main loop. The robot sleeps until it hears the wake word, then
# listens, thinks and answers. Say "stop" to interrupt it and "goodbye" to
# put it back to sleep.

import random
import threading
import time
from collections import deque
from enum import Enum
from typing import Callable, Optional

from persona import hardware
from persona.audio import ConsoleVoice, KeyboardInput, SpeechIn, SpeechOut
from persona.brain import Brain
from persona.config import Settings, settings
from persona.hardware import Expression, Pose
from persona.skills import default_skills


class State(Enum):
    SLEEPING = "sleeping"
    AWAKE = "awake"


def _detect_lang(text: str) -> str:
    try:
        from langdetect import detect

        return detect(text)
    except Exception:
        return "en"


class Robot:
    def __init__(self, cfg: Settings, body: Expression, ears: SpeechIn, voice: SpeechOut,
                 brain: Brain, follower=None):
        self.cfg = cfg
        self.body = body
        self.ears = ears
        self.voice = voice
        self.brain = brain
        self.follower = follower
        self.state = State.SLEEPING
        self._pending: deque[str] = deque()
        self._awake = threading.Event()

    def _hear(self, timeout: float) -> Optional[str]:
        if self._pending:
            return self._pending.popleft()
        return self.ears.listen(timeout)

    def _matches(self, text: str, words: list[str]) -> bool:
        low = text.lower().strip(" .!?")
        return any(low == w or low.startswith(w + " ") for w in words)

    def _interruptible(self, fn: Callable, on_stop: Callable = lambda: None):
        """Run fn in the background, still listening for "stop"."""
        box: dict = {}
        worker = threading.Thread(target=lambda: box.setdefault("r", fn()), daemon=True)
        worker.start()
        while worker.is_alive():
            heard = self.ears.listen(0.05)
            if heard is None:
                continue
            if self._matches(heard, self.cfg.stop_words):
                on_stop()
                return None, True
            self._pending.append(heard)  # handle it after
        return box.get("r"), False

    def _blink_loop(self):
        while self._awake.is_set():
            time.sleep(random.uniform(3, 7))
            if self._awake.is_set():
                self.body.blink()

    def say(self, text: str) -> bool:
        self.body.pose(Pose.TALK)
        _, stopped = self._interruptible(lambda: self.voice.say(text, self.body.mouth),
                                         on_stop=self.voice.interrupt)
        self.body.mouth(0.0)
        self.body.pose(Pose.LISTEN)
        return not stopped

    def wake(self):
        self.state = State.AWAKE
        self._awake.set()
        self.body.pose(Pose.NEUTRAL)
        threading.Thread(target=self._blink_loop, daemon=True).start()
        if self.follower:
            self.follower.start()
        self.say(f"Hi, I'm {self.cfg.name}. How can I help?")

    def sleep(self):
        self.say("Goodbye!")
        self._awake.clear()
        if self.follower:
            self.follower.stop(center=True)
        self.brain.reset()
        self.body.pose(Pose.SLEEP)
        self.state = State.SLEEPING

    def handle(self, text: str):
        self.body.pose(Pose.THINK)
        lang = _detect_lang(text)
        answer, stopped = self._interruptible(lambda: self.brain.respond(text, lang))
        if stopped:
            self.body.pose(Pose.LISTEN)
            return
        self.say(answer)

    def run(self):
        self.body.pose(Pose.SLEEP)
        print(f"{self.cfg.name} is asleep. Say/type one of: {', '.join(self.cfg.wake_words)}"
              "   ('quit' to exit)")
        try:
            while True:
                text = self._hear(timeout=0.5)
                if not text:
                    continue
                if self._matches(text, self.cfg.quit_words):
                    break
                low = text.lower()
                if self.state is State.SLEEPING:
                    if any(w in low for w in self.cfg.wake_words):
                        self.wake()
                    continue
                if self._matches(text, self.cfg.sleep_words):
                    self.sleep()
                elif self._matches(text, self.cfg.stop_words):
                    continue
                else:
                    self.handle(text)
        except KeyboardInterrupt:
            pass
        finally:
            self._awake.clear()
            if self.follower:
                self.follower.stop(center=True)
            self.body.shutdown()
            print("bye.")


def main():
    body = hardware.create(settings.hardware)
    follower = None
    if settings.tracking:
        from persona.vision import FaceFollower

        follower = FaceFollower(body)
    brain = Brain(settings, default_skills())
    robot = Robot(settings, body, KeyboardInput(), ConsoleVoice(), brain, follower)
    if not brain.llm.online:
        print("No LLM configured (see .env.example) - running with placeholder answers.")
    robot.run()
