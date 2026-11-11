# PersonaAI - hardware/__init__.py
#
# Picks which body to use. Only the simulator is included here.

from persona.hardware.base import Expression, Pose
from persona.hardware.sim import SimExpression

_BACKENDS = {
    "sim": SimExpression,
}


def create(name: str) -> Expression:
    try:
        return _BACKENDS[name]()
    except KeyError:
        raise SystemExit(
            f"Unknown hardware backend '{name}'. Available: {', '.join(_BACKENDS)}"
        )


__all__ = ["Expression", "Pose", "create"]
