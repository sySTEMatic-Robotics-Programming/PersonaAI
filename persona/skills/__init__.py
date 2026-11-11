# PersonaAI - skills/__init__.py
#
# The list of skills the robot can use.

from persona.skills.base import Context, Skill
from persona.skills.builtin import DescribeObjectSkill, LiveInfoSkill, TimeSkill, WeatherSkill


def default_skills() -> list[Skill]:
    """Skills the brain can pick, in order."""
    return [DescribeObjectSkill(), WeatherSkill(), TimeSkill(), LiveInfoSkill()]


__all__ = ["Context", "Skill", "default_skills"]
