# PersonaAI - skills/builtin.py
#
# Example skills: time, weather, "what is this?" and live info. The ones
# that need an outside service are left empty for you to plug in.

from datetime import datetime
from typing import Optional

from persona.skills.base import Context, Skill


class TimeSkill(Skill):
    name = "time"
    description = "the user asks what time or date it is"
    slots = ("location",)
    keywords = ("what time", "time is it", "what day")

    def run(self, ctx: Context) -> Optional[str]:
        if ctx.slots.get("location"):
            return None  # other cities: let search handle it
        now = datetime.now()
        return f"It is {now:%H:%M} on {now:%A, %d %B}."


class WeatherSkill(Skill):
    name = "weather"
    description = "the user asks about the weather somewhere"
    slots = ("location",)
    keywords = ("weather",)

    def run(self, ctx: Context) -> Optional[str]:
        location = ctx.slots.get("location")
        if not location:
            return "For which city?"
        try:
            report = self.fetch(location)
        except NotImplementedError:
            return "I don't have a weather provider configured yet."
        if ctx.llm:
            return ctx.llm.phrase(f"Say this weather report briefly in {ctx.lang}: {report}")
        return report

    def fetch(self, location: str) -> str:
        """Plug in a weather API here."""
        raise NotImplementedError


class DescribeObjectSkill(Skill):
    name = "object"
    description = "the user shows something and asks what it is, or asks for a photo"
    keywords = ("what is this",)

    def run(self, ctx: Context) -> Optional[str]:
        if ctx.camera is None:
            return "I can't see right now: my camera isn't connected."
        frame = ctx.camera()
        return self.describe(frame, ctx.lang)

    def describe(self, frame, lang: str) -> str:
        """Plug in a vision model here."""
        return "I would describe it here, but my vision model isn't connected."


class LiveInfoSkill(Skill):
    name = "search"
    description = ("the answer needs current real-world information: news, "
                   "prices, results, schedules, anything 'latest'")
    keywords = ("news", "latest")

    def run(self, ctx: Context) -> Optional[str]:
        """Plug in a search API here."""
        return "I can't look that up right now."
