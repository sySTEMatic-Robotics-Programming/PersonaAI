# PersonaAI - brain.py
#
# Decides what to answer. It asks which skill fits and gets a normal chat
# reply at the same time, so plain conversation is faster.

import json
import re
from concurrent.futures import ThreadPoolExecutor
from typing import Optional

from persona.config import Settings
from persona.skills import Context, Skill


class LLM:
    """Any OpenAI-compatible chat API. Without a key it returns placeholder text."""

    def __init__(self, settings: Settings):
        self.s = settings
        self._client = None
        if settings.llm_enabled:
            from openai import OpenAI

            kwargs = {"api_key": settings.llm_api_key}
            if settings.llm_base_url:
                kwargs["base_url"] = settings.llm_base_url
            self._client = OpenAI(**kwargs)

    @property
    def online(self) -> bool:
        return self._client is not None

    def chat(self, messages: list[dict]) -> str:
        if not self.online:
            last = messages[-1]["content"]
            return f"(offline) You said: {last}"
        resp = self._client.chat.completions.create(model=self.s.llm_model, messages=messages)
        return resp.choices[0].message.content.strip()

    def phrase(self, instruction: str) -> str:
        if not self.online:
            return instruction.split(":", 1)[-1].strip()
        return self.chat([{"role": "user", "content": instruction}])


class Brain:
    def __init__(self, settings: Settings, skills: list[Skill], camera=None):
        self.s = settings
        self.skills = {sk.name: sk for sk in skills}
        self.llm = LLM(settings)
        self.camera = camera
        self.history: list[dict] = []
        self._pool = ThreadPoolExecutor(max_workers=2)

    def reset(self) -> None:
        """Forget the conversation."""
        self.history.clear()

    def respond(self, text: str, lang: str = "en") -> str:
        intent_job = self._pool.submit(self._classify, text)
        chat_job = self._pool.submit(self._chat_reply, text)

        intent, slots = intent_job.result()
        skill = self.skills.get(intent)
        if skill is not None:
            answer = skill.run(Context(text=text, lang=lang, slots=slots,
                                       llm=self.llm, camera=self.camera))
            if answer:
                chat_job.cancel()
                self._remember(text, answer)
                return answer

        answer = chat_job.result()
        self._remember(text, answer)
        return answer

    def _system(self) -> dict:
        return {"role": "system", "content": self.s.system_prompt.format(name=self.s.name)}

    def _chat_reply(self, text: str) -> str:
        return self.llm.chat([self._system(), *self.history, {"role": "user", "content": text}])

    def _remember(self, user: str, assistant: str) -> None:
        self.history += [{"role": "user", "content": user},
                         {"role": "assistant", "content": assistant}]
        self.history = self.history[-2 * self.s.history_turns:]

    def _classify(self, text: str) -> tuple[Optional[str], dict]:
        if not self.llm.online:
            return self._classify_offline(text)
        catalogue = "\n".join(
            f'- "{sk.name}": {sk.description}' + (f" (slots: {', '.join(sk.slots)})" if sk.slots else "")
            for sk in self.skills.values()
        )
        prompt = (
            "Classify the user's message. Choose one intent from this list, or "
            '"none" for ordinary conversation:\n'
            f"{catalogue}\n"
            'Reply with JSON only: {"intent": "...", "slots": {...}}'
        )
        raw = self.llm.chat([{"role": "system", "content": prompt},
                             {"role": "user", "content": text}])
        try:
            data = json.loads(re.search(r"\{.*\}", raw, re.S).group(0))
            return data.get("intent"), data.get("slots") or {}
        except (AttributeError, ValueError):
            return None, {}

    def _classify_offline(self, text: str) -> tuple[Optional[str], dict]:
        low = text.lower()
        for sk in self.skills.values():
            if any(k in low for k in sk.keywords):
                return sk.name, {}
        return None, {}
