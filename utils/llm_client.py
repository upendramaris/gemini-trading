import json
import os
from typing import Any, Dict, Optional

import requests


class LLMClient:
    """
    Minimal wrapper around an OpenAI-compatible chat completion endpoint.
    Supports DeepSeek (default) and generic OpenAI-compatible providers.
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        model: Optional[str] = None,
        timeout: int = 30,
        temperature: float = 0.2,
    ) -> None:
        self.provider = os.getenv("LLM_PROVIDER", "deepseek").lower()
        self.api_key = api_key or self._resolve_api_key()
        self.base_url = base_url or self._resolve_base_url()
        self.model = model or self._resolve_model()
        self.timeout = timeout
        self.temperature = temperature

    def _resolve_api_key(self) -> Optional[str]:
        if self.provider == "deepseek":
            return os.getenv("DEEPSEEK_API_KEY") or os.getenv("API_KEY")
        return os.getenv("OPENAI_API_KEY") or os.getenv("API_KEY")

    def _resolve_base_url(self) -> str:
        env_url = os.getenv("LLM_BASE_URL")
        if env_url:
            return env_url.rstrip("/")
        if self.provider == "deepseek":
            return "https://api.deepseek.com/v1"
        return "https://api.openai.com/v1"

    def _resolve_model(self) -> str:
        env_model = os.getenv("LLM_MODEL")
        if env_model:
            return env_model
        if self.provider == "deepseek":
            return os.getenv("DEEPSEEK_MODEL", "deepseek-chat")
        return os.getenv("OPENAI_MODEL", "gpt-4o-mini")

    def is_available(self) -> bool:
        return bool(self.api_key and self.model and self.base_url)

    def chat(self, system_prompt: str, user_prompt: str, temperature: Optional[float] = None) -> str:
        """
        Sends a chat completion request and returns the raw message content.
        """
        if not self.is_available():
            raise RuntimeError("LLMClient is not configured with an API key or model.")

        payload: Dict[str, Any] = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            "temperature": temperature if temperature is not None else self.temperature,
        }

        url = f"{self.base_url}/chat/completions"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

        response = requests.post(url, headers=headers, json=payload, timeout=self.timeout)
        try:
            response.raise_for_status()
        except requests.HTTPError as exc:
            raise RuntimeError(f"LLM request failed with status {response.status_code}: {response.text}") from exc

        data = response.json()
        choices = data.get("choices")
        if not choices:
            raise RuntimeError("LLM response did not include any choices.")

        message = choices[0].get("message", {})
        content = message.get("content")
        if not content:
            raise RuntimeError("LLM response did not include message content.")

        return content.strip()

    def chat_json(self, system_prompt: str, user_prompt: str) -> Dict[str, Any]:
        """
        Convenience helper that expects the LLM to return a JSON object.
        Attempts to coerce loosely formatted JSON into a dictionary.
        """
        content = self.chat(system_prompt, user_prompt)
        return self._coerce_json(content)

    def _coerce_json(self, content: str) -> Dict[str, Any]:
        try:
            return json.loads(content)
        except json.JSONDecodeError:
            start = content.find("{")
            end = content.rfind("}")
            if start != -1 and end != -1:
                try:
                    return json.loads(content[start : end + 1])
                except json.JSONDecodeError as exc:
                    raise RuntimeError(f"Failed to parse JSON from LLM response: {content}") from exc
            raise RuntimeError(f"Failed to parse JSON from LLM response: {content}")
