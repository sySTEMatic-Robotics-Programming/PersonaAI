# PersonaAI - hardware/base.py
#
# What the body can do: poses, blinking, looking around and moving the
# mouth. The rest of the code only talks to the robot through this.

from abc import ABC, abstractmethod
from enum import Enum


class Pose(str, Enum):
    NEUTRAL = "neutral"
    SLEEP = "sleep"
    LISTEN = "listen"
    THINK = "think"
    TALK = "talk"


class Expression(ABC):
    """Must be safe to call from any thread."""

    @abstractmethod
    def pose(self, pose: Pose) -> None:
        """Go to a pose."""

    @abstractmethod
    def blink(self) -> None:
        """Blink once."""

    @abstractmethod
    def look(self, x: float, y: float) -> None:
        """x, y from -1 to 1. Positive is right/up."""

    @abstractmethod
    def mouth(self, openness: float) -> None:
        """0 closed, 1 fully open."""

    def gesture(self, name: str) -> None:
        """Optional: nod, shake, etc."""

    def shutdown(self) -> None:
        """Go to a safe position."""
        self.pose(Pose.NEUTRAL)
