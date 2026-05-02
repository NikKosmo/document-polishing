"""Model Interface - Handles communication with AI models via CLI"""

import json
import os
import subprocess
import sys
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any, Dict, Optional

import requests

_NOHOOKS_DIR = Path.home() / ".config" / "nohooks"

# Prepended to every model prompt (CLI and HTTP) to prevent wrapper formats
# (PAI, markdown fences, prose around the JSON object, etc.). Shared by all
# ModelInterface implementations so JSON-output behavior is consistent across
# transports.
_GUARD = (
    "CRITICAL: Output ONLY a single raw JSON object. No preamble, no explanation, "
    "no markdown code fences, no frameworks, no wrappers. Do not read any files. "
    "Do not use any tools. Your entire response must be parseable by json.loads().\n\n"
)

from session_handlers import SessionCreationError, SessionQueryError
from session_manager import SessionManager


class OpenAICompatConfigError(Exception):
    """Raised when an ``openai_compat`` model has invalid or missing configuration.

    This is a fatal startup error: callers should not swallow it. ``ModelManager``
    re-raises this exception so the process exits non-zero before any document
    query is issued (per AC-11).
    """


class ModelInterface(ABC):
    """Abstract base class for model interfaces"""

    @abstractmethod
    def query(self, prompt: str) -> Dict[str, Any]:
        """Send a query to the model and return response"""
        pass


class CLIModel(ModelInterface):
    """CLI-based model interface using subprocess"""

    def __init__(self, command: str, args: list = None, timeout: int = 30):
        self.command = command
        self.args = args or []
        self.timeout = timeout

    def query(self, prompt: str) -> Dict[str, Any]:
        """Execute CLI command with prompt and return parsed response"""
        try:
            # Build command
            cmd = [self.command] + self.args

            # Execute with prompt as stdin
            # Strip CLAUDECODE env var to allow Claude CLI inside Claude Code sessions
            env = {k: v for k, v in os.environ.items() if k != "CLAUDECODE"}

            # Inject --setting-sources local for Claude CLI to prevent loading
            # global ~/.claude/CLAUDE.md (which injects PAI context into responses)
            if cmd and cmd[0] == "claude" and "--setting-sources" not in cmd:
                cmd = cmd[:1] + ["--setting-sources", "local"] + cmd[1:]

            result = subprocess.run(
                cmd,
                input=_GUARD + prompt,
                capture_output=True,
                text=True,
                timeout=self.timeout,
                env=env,
                cwd=_NOHOOKS_DIR,
            )

            if result.returncode != 0:
                return {"error": True, "stderr": result.stderr, "raw_response": result.stdout}

            # Try to parse as JSON first
            try:
                return json.loads(result.stdout)
            except json.JSONDecodeError:
                # Try stripping markdown code blocks and parsing again
                stripped = self._strip_markdown_code_blocks(result.stdout)
                try:
                    return json.loads(stripped)
                except json.JSONDecodeError:
                    # Return as raw text if still not JSON
                    return {"error": False, "raw_response": result.stdout.strip()}

        except subprocess.TimeoutExpired:
            return {"error": True, "message": f"Timeout after {self.timeout}s"}
        except FileNotFoundError:
            return {"error": True, "message": f"Command '{self.command}' not found. Is it installed?"}
        except Exception as e:
            return {"error": True, "message": str(e)}

    def _strip_markdown_code_blocks(self, text: str) -> str:
        """Strip markdown code blocks from text (e.g., ```json ... ```)"""
        text = text.strip()
        # Remove ```json or ``` at start
        if text.startswith("```json"):
            text = text[7:]
        elif text.startswith("```"):
            text = text[3:]
        # Remove ``` at end
        if text.endswith("```"):
            text = text[:-3]
        return text.strip()


class OpenAICompatModel(ModelInterface):
    """OpenAI Chat Completions HTTP transport.

    Provider-agnostic: the URL, env-var name for the bearer token, and the model
    identifier are all sourced from configuration, never hardcoded. Any
    OpenAI-compatible endpoint (OpenRouter, OpenAI direct, Together, Groq,
    Anyscale, Azure OpenAI, Ollama, vLLM, llama.cpp server, …) can be served by
    this single class via per-instance ``base_url`` / ``api_key_env`` /
    ``model_id`` config fields.
    """

    def __init__(
        self,
        base_url: str,
        api_key_env: str,
        model_id: str,
        timeout: int = 60,
        max_tokens: Optional[int] = None,
    ):
        self.base_url = base_url
        self.api_key_env = api_key_env
        self.model_id = model_id
        self.timeout = timeout
        self.max_tokens = max_tokens

        # Read bearer token at construction time from the env var named in config.
        # The env var name is *not* hardcoded here — it lives entirely in config.
        self.api_key = os.environ.get(self.api_key_env)
        if not self.api_key:
            raise OpenAICompatConfigError(
                f"Environment variable '{self.api_key_env}' is not set "
                f"(required for openai_compat model with base_url={self.base_url})"
            )

    def _endpoint(self) -> str:
        """Build the chat completions endpoint, tolerating trailing slashes."""
        return f"{self.base_url.rstrip('/')}/chat/completions"

    def _build_payload(self, prompt: str) -> Dict[str, Any]:
        """Build the JSON request body. ``max_tokens`` is omitted when unset.

        Prepends the shared module-level ``_GUARD`` preamble to the user content
        for parity with ``CLIModel.query()`` — keeps JSON-output behavior
        consistent across transports so the same parser handles every response.
        """
        payload: Dict[str, Any] = {
            "model": self.model_id,
            "messages": [{"role": "user", "content": _GUARD + prompt}],
        }
        if self.max_tokens is not None:
            payload["max_tokens"] = self.max_tokens
        return payload

    def _strip_markdown_code_blocks(self, text: str) -> str:
        """Strip markdown code blocks from text (e.g., ```json ... ```)."""
        text = text.strip()
        if text.startswith("```json"):
            text = text[7:]
        elif text.startswith("```"):
            text = text[3:]
        if text.endswith("```"):
            text = text[:-3]
        return text.strip()

    def query(self, prompt: str) -> Dict[str, Any]:
        """Send the prompt to the configured chat completions endpoint."""
        url = self._endpoint()
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        payload = self._build_payload(prompt)

        try:
            response = requests.post(
                url,
                headers=headers,
                json=payload,
                timeout=self.timeout,
            )
        except requests.exceptions.RequestException as exc:
            return {"error": True, "message": str(exc)}
        except Exception as exc:  # pragma: no cover - defensive
            return {"error": True, "message": str(exc)}

        if not (200 <= response.status_code < 300):
            text = response.text
            return {"error": True, "stderr": text, "raw_response": text}

        # 2xx response — extract content from choices[0].message.content
        try:
            body = response.json()
            content = body["choices"][0]["message"]["content"]
        except (ValueError, KeyError, IndexError, TypeError) as exc:
            text = response.text
            return {"error": True, "message": f"Malformed OpenAI-compatible response: {exc}", "raw_response": text}

        # Try parsing content as JSON, then JSON-in-code-fences, then return raw.
        if not isinstance(content, str):
            return {"error": False, "raw_response": content}

        try:
            return json.loads(content)
        except json.JSONDecodeError:
            stripped = self._strip_markdown_code_blocks(content)
            try:
                return json.loads(stripped)
            except json.JSONDecodeError:
                return {"error": False, "raw_response": content.strip()}


class ModelFactory:
    """Factory for creating model instances"""

    @staticmethod
    def create_cli_model(name: str, config: Dict[str, Any]) -> CLIModel:
        """Create a CLI model from configuration"""
        return CLIModel(
            command=config.get("command", name), args=config.get("args", []), timeout=config.get("timeout", 30)
        )

    @staticmethod
    def create_openai_compat_model(name: str, config: Dict[str, Any]) -> "OpenAICompatModel":
        """Create an OpenAI-compatible HTTP model from configuration.

        Required fields (no defaults): ``base_url``, ``api_key_env``, ``model_id``.
        Optional fields: ``timeout`` (default 60), ``max_tokens`` (no default;
        omitted from the HTTP request body when unset).
        """
        missing: list = []
        for required in ("base_url", "api_key_env", "model_id"):
            if not config.get(required):
                missing.append(required)
        if missing:
            raise OpenAICompatConfigError(
                f"openai_compat model '{name}' is missing required config field(s): {', '.join(missing)}"
            )

        return OpenAICompatModel(
            base_url=config["base_url"],
            api_key_env=config["api_key_env"],
            model_id=config["model_id"],
            timeout=config.get("timeout", 60),
            max_tokens=config.get("max_tokens"),
        )

    @staticmethod
    def create(name: str, config: Dict[str, Any]) -> ModelInterface:
        """Create appropriate model interface based on config type"""
        model_type = config.get("type", "cli")

        if model_type == "cli":
            return ModelFactory.create_cli_model(name, config)
        elif model_type == "openai_compat":
            return ModelFactory.create_openai_compat_model(name, config)
        else:
            raise ValueError(f"Unsupported model type: {model_type}")


class ModelManager:
    """Manages multiple model instances with optional session support"""

    def __init__(self, models_config: Dict[str, Dict[str, Any]], session_config: Dict[str, Any] = None):
        self.models = {}
        self.config = models_config
        self.session_config = session_config or {}
        self.session_manager: Optional[SessionManager] = None
        self._sessions_enabled = self.session_config.get("enabled", False)

        # Initialize enabled models
        for name, config in models_config.items():
            if config.get("enabled", True):
                try:
                    self.models[name] = ModelFactory.create(name, config)
                    print(f"✓ Loaded model: {name}")
                except OpenAICompatConfigError as e:
                    # Fail loud for openai_compat config problems (AC-11): the
                    # process exits non-zero before any document query is issued
                    # and the user-visible error message names the missing env var.
                    print(f"✗ Failed to load model {name}: {e}", file=sys.stderr)
                    sys.exit(1)
                except Exception as e:
                    print(f"✗ Failed to load model {name}: {e}")

    def init_sessions(self, document: str, purpose: str = None, model_names: list = None) -> Dict[str, str]:
        """
        Initialize sessions for models with full document context.

        Args:
            document: Full markdown document content
            purpose: System prompt explaining document purpose
            model_names: List of models to init sessions for (defaults to all available)

        Returns:
            Dict of model_name -> session_id for successful inits
        """
        if not self._sessions_enabled:
            return {}

        if model_names is None:
            model_names = list(self.models.keys())

        self.session_manager = SessionManager(self.config, self.session_config)

        # Initialize sessions in parallel
        results = self.session_manager.init_sessions_parallel(model_names, document, purpose)

        for model, session_id in results.items():
            print(f"✓ Session created for {model}: {session_id[:8]}...")

        failed = set(model_names) - set(results.keys())
        for model in failed:
            print(f"✗ Session failed for {model}, will use stateless mode")

        return results

    def query(self, model_name: str, prompt: str, use_session: bool = True) -> Dict[str, Any]:
        """
        Query a specific model, optionally using session.

        Args:
            model_name: Model to query
            prompt: Query prompt
            use_session: Whether to use session if available (default True)

        Returns:
            Model response dict
        """
        if model_name not in self.models:
            return {"error": True, "message": f"Model '{model_name}' not available"}

        # Try session-based query if enabled and available
        if use_session and self.session_manager and self.session_manager.has_session(model_name):
            try:
                return self.session_manager.query_in_session(model_name, prompt)
            except (SessionQueryError, SessionCreationError) as e:
                print(f"  ⚠ Session query failed for {model_name}, falling back to stateless: {e}")
                # Fall through to stateless query

        # Stateless query (original behavior)
        return self.models[model_name].query(prompt)

    def query_all(self, prompt: str, model_names: list = None, use_session: bool = True) -> Dict[str, Dict[str, Any]]:
        """
        Query multiple models with the same prompt.

        Args:
            prompt: Query prompt
            model_names: List of models to query (defaults to all available)
            use_session: Whether to use sessions if available

        Returns:
            Dict of model_name -> response dict
        """
        if model_names is None:
            model_names = list(self.models.keys())

        results = {}
        for name in model_names:
            if name in self.models:
                print(f"  Querying {name}...")
                results[name] = self.query(name, prompt, use_session=use_session)
            else:
                results[name] = {"error": True, "message": f"Model '{name}' not found"}

        return results

    def cleanup_sessions(self):
        """Cleanup all active sessions"""
        if self.session_manager:
            self.session_manager.cleanup_sessions()
            print("✓ Sessions cleaned up")

    def sessions_enabled(self) -> bool:
        """Check if session management is enabled"""
        return self._sessions_enabled

    def has_active_sessions(self) -> bool:
        """Check if there are any active sessions"""
        return self.session_manager is not None and len(self.session_manager.sessions) > 0

    def list_available(self) -> list:
        """List available model names"""
        return list(self.models.keys())
