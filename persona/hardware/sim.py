# PersonaAI - hardware/sim.py
#
# A fake body for testing. It just prints what the robot would do.

import os
import threading

from persona.hardware.base import Expression, Pose


class SimExpression(Expression):
    def __init__(self, verbose: bool = True):
        self.verbose = verbose
        self.show_jaw = os.getenv("PERSONA_SIM_JAW", "0") == "1"
        self._lock = threading.Lock()
        self._mouth_open = False

    def _log(self, msg: str) -> None:
        if self.verbose:
            with self._lock:
                print(f"    \033[2m[body] {msg}\033[0m")

    def pose(self, pose: Pose) -> None:
        self._log(f"pose -> {pose.value}")

    def blink(self) -> None:
        self._log("blink")

    def look(self, x: float, y: float) -> None:
        self._log(f"look x={x:+.2f} y={y:+.2f}")

    def mouth(self, openness: float) -> None:
        # only print when it changes
        is_open = openness > 0.5
        if is_open != self._mouth_open:
            self._mouth_open = is_open
            if self.show_jaw:
                self._log("mouth open" if is_open else "mouth closed")

    def gesture(self, name: str) -> None:
        self._log(f"gesture -> {name}")
