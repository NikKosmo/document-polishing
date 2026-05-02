"""Tests for the openai_compat HTTP model transport.

Covers acceptance criteria AC-31 through AC-37 from the OpenRouter integration
PRD: response parity with CLIModel, fail-loud env-var enforcement, and
provider-agnosticism (swapping base_url + api_key_env in config alone).

No live HTTP is performed — every requests.post call is mocked.
"""

import sys
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

import pytest

# Make scripts/src importable
project_root = Path(__file__).resolve().parents[1]
scripts_src = project_root.joinpath("scripts", "src")
sys.path.insert(0, scripts_src.as_posix())


import model_interface  # noqa: E402
import requests  # noqa: E402
from model_interface import (  # noqa: E402
    _GUARD,
    ModelFactory,
    ModelManager,
    OpenAICompatConfigError,
    OpenAICompatModel,
)


def _make_response(status_code: int, content: str, *, raw_text: str | None = None):
    """Build a fake requests.Response-like object for monkeypatching."""

    body = {
        "choices": [
            {"message": {"content": content}},
        ]
    }

    class FakeResponse(SimpleNamespace):
        def json(self):
            return self._body

    text = raw_text if raw_text is not None else "ok"
    return FakeResponse(status_code=status_code, _body=body, text=text)


def _make_raw_response(status_code: int, text: str):
    """Build a fake non-2xx response (no JSON body required)."""

    class FakeResponse(SimpleNamespace):
        def json(self):
            raise ValueError("no json body")

    return FakeResponse(status_code=status_code, text=text)


@pytest.fixture
def env_with_key(monkeypatch):
    monkeypatch.setenv("FAKE_KEY", "sk-test-token")
    return "FAKE_KEY"


# ---------------------------------------------------------------------------
# AC-31: HTTP 200 + JSON content -> parsed dict
# ---------------------------------------------------------------------------
def test_http_200_json_content_returns_parsed_dict(monkeypatch, env_with_key):
    captured = {}

    def fake_post(url, headers=None, json=None, timeout=None):
        captured["url"] = url
        captured["headers"] = headers
        captured["json"] = json
        captured["timeout"] = timeout
        return _make_response(200, '{"interpretation": "all good", "n": 1}')

    monkeypatch.setattr(model_interface.requests, "post", fake_post)

    model = OpenAICompatModel(
        base_url="https://api.example.com/v1",
        api_key_env=env_with_key,
        model_id="example/model",
    )
    result = model.query("hello")

    assert result == {"interpretation": "all good", "n": 1}
    assert captured["url"] == "https://api.example.com/v1/chat/completions"
    assert captured["headers"]["Authorization"] == "Bearer sk-test-token"
    assert captured["json"]["model"] == "example/model"
    # The shared _GUARD preamble is prepended to the user content for parity
    # with CLIModel — keeps JSON-output behavior consistent across transports.
    # Asserting against the imported constant means the test follows the
    # canonical guard text automatically if it ever changes.
    assert captured["json"]["messages"] == [{"role": "user", "content": _GUARD + "hello"}]
    # max_tokens not configured -> not in payload
    assert "max_tokens" not in captured["json"]


# ---------------------------------------------------------------------------
# AC-32: HTTP 200 + JSON-in-code-fences -> parsed dict
# ---------------------------------------------------------------------------
def test_http_200_json_in_code_fences_returns_parsed_dict(monkeypatch, env_with_key):
    fenced = '```json\n{"interpretation": "fenced ok", "n": 2}\n```'

    def fake_post(url, headers=None, json=None, timeout=None):
        return _make_response(200, fenced)

    monkeypatch.setattr(model_interface.requests, "post", fake_post)

    model = OpenAICompatModel(
        base_url="https://api.example.com/v1/",  # trailing slash tolerated
        api_key_env=env_with_key,
        model_id="example/model",
    )
    result = model.query("hello")

    assert result == {"interpretation": "fenced ok", "n": 2}


# ---------------------------------------------------------------------------
# AC-33: HTTP 200 non-JSON -> {error: False, raw_response: ...}
# ---------------------------------------------------------------------------
def test_http_200_non_json_returns_raw_response(monkeypatch, env_with_key):
    plain = "this is not json at all"

    def fake_post(url, headers=None, json=None, timeout=None):
        return _make_response(200, plain)

    monkeypatch.setattr(model_interface.requests, "post", fake_post)

    model = OpenAICompatModel(
        base_url="https://api.example.com/v1",
        api_key_env=env_with_key,
        model_id="example/model",
    )
    result = model.query("hello")

    assert result.get("error") is False
    assert result.get("raw_response") == plain


# ---------------------------------------------------------------------------
# AC-34: HTTP non-2xx -> {error: True, stderr: ..., raw_response: ...}
# ---------------------------------------------------------------------------
def test_http_non_2xx_returns_error_with_stderr(monkeypatch, env_with_key):
    body_text = '{"error": {"message": "rate limit"}}'

    def fake_post(url, headers=None, json=None, timeout=None):
        return _make_raw_response(429, body_text)

    monkeypatch.setattr(model_interface.requests, "post", fake_post)

    model = OpenAICompatModel(
        base_url="https://api.example.com/v1",
        api_key_env=env_with_key,
        model_id="example/model",
    )
    result = model.query("hello")

    assert result.get("error") is True
    assert result.get("stderr") == body_text
    assert result.get("raw_response") == body_text


# ---------------------------------------------------------------------------
# AC-35: network exception -> {error: True, message: ...}
# ---------------------------------------------------------------------------
def test_network_exception_returns_error_message(monkeypatch, env_with_key):
    def fake_post(url, headers=None, json=None, timeout=None):
        raise requests.exceptions.ConnectionError("network down")

    monkeypatch.setattr(model_interface.requests, "post", fake_post)

    model = OpenAICompatModel(
        base_url="https://api.example.com/v1",
        api_key_env=env_with_key,
        model_id="example/model",
    )
    result = model.query("hello")

    assert result.get("error") is True
    assert "network down" in result.get("message", "")


def test_timeout_exception_returns_error_message(monkeypatch, env_with_key):
    def fake_post(url, headers=None, json=None, timeout=None):
        raise requests.exceptions.Timeout("timed out")

    monkeypatch.setattr(model_interface.requests, "post", fake_post)

    model = OpenAICompatModel(
        base_url="https://api.example.com/v1",
        api_key_env=env_with_key,
        model_id="example/model",
    )
    result = model.query("hello")

    assert result.get("error") is True
    assert "timed out" in result.get("message", "")


# ---------------------------------------------------------------------------
# AC-36: missing env var with enabled openai_compat model -> fatal startup
# ---------------------------------------------------------------------------
def test_missing_env_var_fatal_when_model_enabled(monkeypatch):
    # Ensure the env var is *not* set
    monkeypatch.delenv("MISSING_KEY_FOR_TEST", raising=False)

    models_config = {
        "or_test": {
            "type": "openai_compat",
            "base_url": "https://api.example.com/v1",
            "api_key_env": "MISSING_KEY_FOR_TEST",
            "model_id": "example/model",
            "enabled": True,
        }
    }

    with pytest.raises(SystemExit) as exc_info:
        ModelManager(models_config, {})

    assert exc_info.value.code != 0


def test_missing_env_var_error_message_names_env_var(monkeypatch, capsys):
    monkeypatch.delenv("THE_MISSING_TOKEN_VAR", raising=False)

    models_config = {
        "or_test": {
            "type": "openai_compat",
            "base_url": "https://api.example.com/v1",
            "api_key_env": "THE_MISSING_TOKEN_VAR",
            "model_id": "example/model",
            "enabled": True,
        }
    }

    with pytest.raises(SystemExit):
        ModelManager(models_config, {})

    captured = capsys.readouterr()
    combined = captured.out + captured.err
    assert "THE_MISSING_TOKEN_VAR" in combined


def test_disabled_openai_compat_model_does_not_require_env_var(monkeypatch):
    """Disabled models are not constructed, so missing env var is harmless."""
    monkeypatch.delenv("UNSET_KEY", raising=False)

    models_config = {
        "or_disabled": {
            "type": "openai_compat",
            "base_url": "https://api.example.com/v1",
            "api_key_env": "UNSET_KEY",
            "model_id": "example/model",
            "enabled": False,
        }
    }

    # Should not raise / exit
    manager = ModelManager(models_config, {})
    assert "or_disabled" not in manager.list_available()


# ---------------------------------------------------------------------------
# AC-37: switching base_url + api_key_env in config alone is provider-agnostic
# ---------------------------------------------------------------------------
def test_provider_swap_via_config_only(monkeypatch):
    monkeypatch.setenv("PROVIDER_ONE_KEY", "key-one")
    monkeypatch.setenv("PROVIDER_TWO_KEY", "key-two")

    captured = []

    def fake_post(url, headers=None, json=None, timeout=None):
        captured.append({"url": url, "auth": headers["Authorization"]})
        return _make_response(200, '{"ok": true}')

    monkeypatch.setattr(model_interface.requests, "post", fake_post)

    config_one = {
        "type": "openai_compat",
        "base_url": "https://provider-one.example.com/api/v1",
        "api_key_env": "PROVIDER_ONE_KEY",
        "model_id": "provider-one/model-x",
        "enabled": True,
    }
    config_two = {
        "type": "openai_compat",
        "base_url": "https://provider-two.example.org/v2",
        "api_key_env": "PROVIDER_TWO_KEY",
        "model_id": "provider-two/model-y",
        "enabled": True,
    }

    model_one = ModelFactory.create("first", config_one)
    model_one.query("hello")

    model_two = ModelFactory.create("second", config_two)
    model_two.query("hello")

    assert captured[0]["url"] == "https://provider-one.example.com/api/v1/chat/completions"
    assert captured[0]["auth"] == "Bearer key-one"
    assert captured[1]["url"] == "https://provider-two.example.org/v2/chat/completions"
    assert captured[1]["auth"] == "Bearer key-two"


# ---------------------------------------------------------------------------
# Extra: required-field validation (AC-4/5/6)
# ---------------------------------------------------------------------------
@pytest.mark.parametrize("missing_field", ["base_url", "api_key_env", "model_id"])
def test_factory_rejects_missing_required_field(monkeypatch, missing_field):
    monkeypatch.setenv("FAKE_KEY", "sk-test")
    config = {
        "type": "openai_compat",
        "base_url": "https://api.example.com/v1",
        "api_key_env": "FAKE_KEY",
        "model_id": "example/model",
        "enabled": True,
    }
    config.pop(missing_field)

    with pytest.raises(OpenAICompatConfigError) as exc_info:
        ModelFactory.create("broken", config)
    assert missing_field in str(exc_info.value)


# ---------------------------------------------------------------------------
# Extra: max_tokens is forwarded only when configured (AC-8/13)
# ---------------------------------------------------------------------------
def test_max_tokens_included_when_configured(monkeypatch, env_with_key):
    captured = {}

    def fake_post(url, headers=None, json=None, timeout=None):
        captured["json"] = json
        return _make_response(200, '{"ok": true}')

    monkeypatch.setattr(model_interface.requests, "post", fake_post)

    model = OpenAICompatModel(
        base_url="https://api.example.com/v1",
        api_key_env=env_with_key,
        model_id="example/model",
        max_tokens=512,
    )
    model.query("hi")
    assert captured["json"]["max_tokens"] == 512


def test_max_tokens_omitted_when_not_configured(monkeypatch, env_with_key):
    captured = {}

    def fake_post(url, headers=None, json=None, timeout=None):
        captured["json"] = json
        return _make_response(200, '{"ok": true}')

    monkeypatch.setattr(model_interface.requests, "post", fake_post)

    model = OpenAICompatModel(
        base_url="https://api.example.com/v1",
        api_key_env=env_with_key,
        model_id="example/model",
    )
    model.query("hi")
    assert "max_tokens" not in captured["json"]


# ---------------------------------------------------------------------------
# Sessions — must not crash when an openai_compat model is in the list (AC-26)
# ---------------------------------------------------------------------------
def test_session_init_skips_openai_compat_models(monkeypatch):
    """init_sessions_parallel must not raise the unknown-model ValueError when
    an openai_compat model is in the model list (AC-26)."""

    monkeypatch.setenv("FAKE_KEY", "sk-test")

    models_config = {
        "claude": {"type": "cli", "command": "claude", "args": ["-p"], "timeout": 60, "enabled": True},
        "or_test": {
            "type": "openai_compat",
            "base_url": "https://api.example.com/v1",
            "api_key_env": "FAKE_KEY",
            "model_id": "example/model",
            "enabled": True,
        },
    }
    session_config = {
        "enabled": True,
        "mode": "auto-recreate",
        "query_format": "resend-chunk",
        "purpose_prompt": "Test",
        "max_retries": 1,
        "retry_delay_seconds": 0,
    }

    from session_manager import SessionManager

    manager = SessionManager(models_config, session_config)

    # Patch get_session_handler so the CLI side returns a fake handler that
    # records calls but never spawns a subprocess.
    fake_handler_calls = []

    class FakeHandler:
        def create_session(self, document, purpose):
            fake_handler_calls.append("created")
            return "fake-session-id"

        def query_session(self, session_id, prompt):
            return {"interpretation": "fake"}

    def fake_get_handler(name, cfg):
        if name == "claude":
            return FakeHandler()
        # If anything other than claude is asked for, the original ValueError
        # would surface — failing the test.
        raise ValueError(f"would crash for {name}")

    monkeypatch.setattr("session_manager.get_session_handler", fake_get_handler)

    # Must not raise even though "or_test" (openai_compat) is in the list.
    results = manager.init_sessions_parallel(["claude", "or_test"], "doc", "purpose")

    assert "claude" in results
    assert "or_test" not in results  # openai_compat models are skipped
    assert fake_handler_calls == ["created"]


# ---------------------------------------------------------------------------
# Sessions — querying an openai_compat model bypasses the session path (AC-27)
# ---------------------------------------------------------------------------
def test_session_enabled_query_for_openai_compat_uses_stateless_path(monkeypatch):
    monkeypatch.setenv("FAKE_KEY", "sk-test")

    models_config = {
        "or_test": {
            "type": "openai_compat",
            "base_url": "https://api.example.com/v1",
            "api_key_env": "FAKE_KEY",
            "model_id": "example/model",
            "enabled": True,
        },
    }
    session_config = {"enabled": True}

    def fake_post(url, headers=None, json=None, timeout=None):
        return _make_response(200, '{"interpretation": "stateless ok"}')

    monkeypatch.setattr(model_interface.requests, "post", fake_post)

    manager = ModelManager(models_config, session_config)
    # No session_manager attached (because no init_sessions call happened, or
    # because the openai_compat model was filtered out of session init); the
    # query should still succeed via the stateless path.
    result = manager.query("or_test", "hello")
    assert result == {"interpretation": "stateless ok"}


# ---------------------------------------------------------------------------
# Config dispatch (AC-1/2): "openai_compat" type routes to OpenAICompatModel
# ---------------------------------------------------------------------------
def test_factory_dispatches_openai_compat_type(monkeypatch):
    monkeypatch.setenv("FAKE_KEY", "sk-test")

    config = {
        "type": "openai_compat",
        "base_url": "https://api.example.com/v1",
        "api_key_env": "FAKE_KEY",
        "model_id": "example/model",
    }
    instance = ModelFactory.create("any_name", config)
    assert isinstance(instance, OpenAICompatModel)


# ---------------------------------------------------------------------------
# .env loading helper test (AC-10 mechanics)
# ---------------------------------------------------------------------------
def test_load_project_env_reads_dotenv(tmp_path, monkeypatch):
    """load_project_env should pull values from document_polishing/.env."""

    # Patch the env_loader's project root to a temp dir for isolation
    import env_loader

    fake_env = tmp_path / ".env"
    fake_env.write_text("OPENROUTER_TEST_KEY=value-from-dotenv\n")
    monkeypatch.setattr(env_loader, "_ENV_FILE", fake_env)
    monkeypatch.delenv("OPENROUTER_TEST_KEY", raising=False)

    env_loader.load_project_env()
    import os

    assert os.environ.get("OPENROUTER_TEST_KEY") == "value-from-dotenv"


# ---------------------------------------------------------------------------
# config.yaml contains openrouter_gemma per AC-20
# ---------------------------------------------------------------------------
def test_config_yaml_contains_openrouter_gemma_entry():
    import yaml

    config_path = project_root / "scripts" / "config.yaml"
    with open(config_path, "r", encoding="utf-8") as f:
        config = yaml.safe_load(f)

    entry = config["models"].get("openrouter_gemma")
    assert entry is not None, "openrouter_gemma must be defined in scripts/config.yaml"
    assert entry["type"] == "openai_compat"
    assert entry["base_url"] == "https://openrouter.ai/api/v1"
    assert entry["api_key_env"] == "OPENROUTER_API_KEY"
    assert entry["model_id"] == "google/gemma-4-31b-it:free"
    assert entry["enabled"] is False
    assert entry["model_id"].endswith(":free")


# Silence "unused import" warnings from helpers loaded conditionally
_ = patch
