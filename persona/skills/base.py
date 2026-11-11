# PersonaAI - skills/base.py
#
# What every skill looks like. A skill gets the user's sentence and
# returns what the robot should say.

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Optional


@dataclass
class Context:
    """Everything a skill gets."""

    text: str
    lang: str = "en"
    slots: dict[str, Any] = field(default_factory=dict)
    llm: Any = None
    camera: Any = None


class Skill(ABC):
    #: id the brain uses
    name: str = ""
    #: when to use this skill, in one line
    description: str = ""
    #: info to pull out of the sentence, e.g. location
    slots: tuple[str, ...] = ()
    #: used when there is no LLM
    keywords: tuple[str, ...] = ()

    @abstractmethod
    def run(self, ctx: Context) -> Optional[str]:
        """Return what to say, or None to let the chat answer."""
