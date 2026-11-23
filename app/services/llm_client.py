"""
LLM Client Services for Socratic Tutoring.

Provides:
- BaseLLMClient: Abstract interface
- GeminiLLMClient: Google Gemini API client
- OpenAILLMClient: OpenAI / Ollama / Local API client
- MockLLMClient: Deterministic, hermetic mock client for testing
- get_default_llm_client: Client factory
"""
from abc import ABC, abstractmethod
import json
import os
import re
from typing import Any, Dict, List, Optional, Type
import urllib.request
import urllib.error

from pydantic import BaseModel


class BaseLLMClient(ABC):
    """Abstract interface for LLM completion and structured output."""

    @property
    @abstractmethod
    def provider_name(self) -> str:
        """Provider identifier."""
        pass

    @abstractmethod
    def complete(self, prompt: str, system_prompt: Optional[str] = None) -> str:
        """Generate unstructured text completion."""
        pass

    @abstractmethod
    def complete_structured(
        self,
        prompt: str,
        response_model: Type[BaseModel],
        system_prompt: Optional[str] = None,
    ) -> BaseModel:
        """Generate output strictly parsed into a Pydantic model."""
        pass


class GeminiLLMClient(BaseLLMClient):
    """Google Gemini API client using standard HTTPS REST calls."""

    def __init__(
        self,
        api_key: Optional[str] = None,
        model: str = "gemini-1.5-flash",
        timeout: float = 20.0,
    ):
        self.api_key = api_key or os.environ.get("GEMINI_API_KEY", "")
        self.model = os.environ.get("GEMINI_MODEL", model)
        self.timeout = timeout

    @property
    def provider_name(self) -> str:
        return f"gemini:{self.model}"

    def complete(self, prompt: str, system_prompt: Optional[str] = None) -> str:
        if not self.api_key:
            raise ValueError("GEMINI_API_KEY is not configured.")

        url = (
            f"https://generativelanguage.googleapis.com/v1beta/models/"
            f"{self.model}:generateContent?key={self.api_key}"
        )
        contents = []
        if system_prompt:
            contents.append({"role": "user", "parts": [{"text": f"SYSTEM INSTRUCTION: {system_prompt}"}]})
            contents.append({"role": "model", "parts": [{"text": "Understood. I will follow all instructions."}]})
        contents.append({"role": "user", "parts": [{"text": prompt}]})

        payload = {
            "contents": contents,
            "generationConfig": {"temperature": 0.2, "maxOutputTokens": 2048}
        }
        data = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(url, data=data, headers={"Content-Type": "application/json"})

        try:
            with urllib.request.urlopen(req, timeout=self.timeout) as resp:
                result = json.loads(resp.read().decode("utf-8"))
                candidates = result.get("candidates", [])
                if not candidates:
                    raise RuntimeError("No candidate response returned from Gemini API.")
                return candidates[0]["content"]["parts"][0]["text"]
        except Exception as exc:
            raise RuntimeError(f"Gemini LLM call failed: {exc}") from exc

    def complete_structured(
        self,
        prompt: str,
        response_model: Type[BaseModel],
        system_prompt: Optional[str] = None,
    ) -> BaseModel:
        schema_json = json.dumps(response_model.model_json_schema(), indent=2)
        instruction = (
            f"{system_prompt or ''}\n\n"
            f"IMPORTANT: You MUST return a valid JSON object strictly matching this JSON schema:\n"
            f"```json\n{schema_json}\n```\n"
            f"Respond ONLY with the JSON object. Do not wrap in markdown or commentary."
        )
        raw_text = self.complete(prompt, system_prompt=instruction)

        # Clean JSON if wrapped in markdown code blocks
        clean_json = raw_text.strip()
        if clean_json.startswith("```"):
            clean_json = re.sub(r"^```(?:json)?\s*", "", clean_json)
            clean_json = re.sub(r"\s*```$", "", clean_json)

        return response_model.model_validate_json(clean_json)


class OpenAILLMClient(BaseLLMClient):
    """OpenAI-compatible chat completion client (supports OpenAI, Groq, Ollama)."""

    def __init__(
        self,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        model: str = "gpt-4o-mini",
        timeout: float = 20.0,
    ):
        self.api_key = api_key or os.environ.get("OPENAI_API_KEY", "")
        self.base_url = (
            base_url
            or os.environ.get("OPENAI_BASE_URL", "https://api.openai.com/v1")
        ).rstrip("/")
        self.model = os.environ.get("OPENAI_MODEL", model)
        self.timeout = timeout

    @property
    def provider_name(self) -> str:
        return f"openai:{self.model}"

    def complete(self, prompt: str, system_prompt: Optional[str] = None) -> str:
        if not self.api_key and "localhost" not in self.base_url and "127.0.0.1" not in self.base_url:
            raise ValueError("OPENAI_API_KEY is not configured.")

        url = f"{self.base_url}/chat/completions"
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        payload = {
            "model": self.model,
            "messages": messages,
            "temperature": 0.2,
        }
        data = json.dumps(payload).encode("utf-8")
        headers = {"Content-Type": "application/json"}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"

        req = urllib.request.Request(url, data=data, headers=headers)
        try:
            with urllib.request.urlopen(req, timeout=self.timeout) as resp:
                result = json.loads(resp.read().decode("utf-8"))
                return result["choices"][0]["message"]["content"]
        except Exception as exc:
            raise RuntimeError(f"OpenAI LLM call failed: {exc}") from exc

    def complete_structured(
        self,
        prompt: str,
        response_model: Type[BaseModel],
        system_prompt: Optional[str] = None,
    ) -> BaseModel:
        schema_json = json.dumps(response_model.model_json_schema(), indent=2)
        instruction = (
            f"{system_prompt or ''}\n\n"
            f"You MUST output raw JSON conforming to this JSON schema:\n"
            f"```json\n{schema_json}\n```\n"
            f"Respond ONLY with valid JSON."
        )
        raw_text = self.complete(prompt, system_prompt=instruction)
        clean_json = raw_text.strip()
        if clean_json.startswith("```"):
            clean_json = re.sub(r"^```(?:json)?\s*", "", clean_json)
            clean_json = re.sub(r"\s*```$", "", clean_json)

        return response_model.model_validate_json(clean_json)


class MockLLMClient(BaseLLMClient):
    """
    Deterministic Mock LLM Client for unit testing, offline development, and CI/CD.
    Allows exact response injection, function-based generation, and failure simulation.
    """

    def __init__(
        self,
        default_response: Optional[str] = None,
        default_model_instance: Optional[BaseModel] = None,
        model_instances: Optional[Dict[Type[BaseModel], BaseModel]] = None,
        simulate_error: bool = False,
    ):
        self.default_response = default_response or '{"status": "ok"}'
        self.default_model_instance = default_model_instance
        self.model_instances = model_instances or {}
        if default_model_instance:
            self.model_instances[type(default_model_instance)] = default_model_instance
        self.simulate_error = simulate_error
        self.call_history: List[Dict[str, Any]] = []

    @property
    def provider_name(self) -> str:
        return "mock_llm"

    def register_model_instance(self, instance: BaseModel) -> None:
        """Register a specific model instance to be returned when requested."""
        self.model_instances[type(instance)] = instance

    def complete(self, prompt: str, system_prompt: Optional[str] = None) -> str:
        self.call_history.append({"prompt": prompt, "system_prompt": system_prompt})
        if self.simulate_error:
            raise RuntimeError("Simulated LLM network/API connection failure.")
        return self.default_response

    def complete_structured(
        self,
        prompt: str,
        response_model: Type[BaseModel],
        system_prompt: Optional[str] = None,
    ) -> BaseModel:
        self.call_history.append({"prompt": prompt, "system_prompt": system_prompt, "schema": response_model})
        if self.simulate_error:
            raise RuntimeError("Simulated LLM structured output failure.")
        if response_model in self.model_instances:
            return self.model_instances[response_model]
        if self.default_model_instance is not None:
            if isinstance(self.default_model_instance, response_model):
                return self.default_model_instance
            try:
                return response_model.model_validate(self.default_model_instance.model_dump())
            except Exception:
                pass
        return response_model.model_validate_json(self.default_response)


def get_default_llm_client(force_mock: bool = False) -> Optional[BaseLLMClient]:
    """Acquire the configured LLM client, or None if offline/unconfigured."""
    if force_mock or os.environ.get("TUTOR_FORCE_MOCK_LLM") == "1":
        return MockLLMClient()
    if os.environ.get("GEMINI_API_KEY"):
        return GeminiLLMClient()
    if os.environ.get("OPENAI_API_KEY"):
        return OpenAILLMClient()
    return None
