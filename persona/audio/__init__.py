# PersonaAI - audio/__init__.py
#
# Speech input and output.

from persona.audio.speech import ConsoleVoice, KeyboardInput, SpeechIn, SpeechOut

__all__ = ["SpeechIn", "SpeechOut", "KeyboardInput", "ConsoleVoice"]
