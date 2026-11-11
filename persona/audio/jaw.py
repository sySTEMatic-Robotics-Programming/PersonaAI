# PersonaAI - audio/jaw.py
#
# Moves the mouth with the voice. Loud parts open it, quiet parts close
# it.

from typing import Iterable, Iterator


def loudness_envelope(samples: Iterable[float], frame_len: int) -> list[float]:
    """Loudness of each frame."""
    out, frame = [], []
    for s in samples:
        frame.append(s * s)
        if len(frame) == frame_len:
            out.append((sum(frame) / frame_len) ** 0.5)
            frame = []
    if frame:
        out.append((sum(frame) / len(frame)) ** 0.5)
    return out


def envelope_to_openness(envelope: list[float], threshold: float = 0.5) -> Iterator[float]:
    """Map a loudness envelope to mouth openness in [0, 1].

    Frames quieter than `threshold` × the clip's peak keep the mouth closed.
    """
    peak = max(envelope, default=0.0)
    if peak <= 0:
        yield from (0.0 for _ in envelope)
        return
    for level in envelope:
        rel = level / peak
        yield 0.0 if rel < threshold else min(1.0, rel)
