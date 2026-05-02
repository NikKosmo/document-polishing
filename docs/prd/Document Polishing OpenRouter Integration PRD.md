# OpenAI-Compatible HTTP Model Integration — PRD

> Add a provider-agnostic OpenAI Chat Completions HTTP transport to document_polishing as a new model `type: openai_compat`, alongside the existing `type: cli`. The first wired instance points at OpenRouter and uses `google/gemma-4-31b-it:free`, but the same class serves any OpenAI-compatible endpoint (OR, OpenAI direct, Together, Groq, Ollama, vLLM, etc.) via per-instance `base_url` and `api_key_env` config — no code change needed to swap providers.

## Problem

document_polishing reaches LLMs only via CLI subprocesses today (`claude`, `gemini`, `codex`; see `scripts/src/model_interface.py`, `scripts/src/session_handlers.py`). Each requires a local CLI install, carries CLI-specific session quirks, and is one of three fixed perspectives. There is no path to use any HTTP-API model — for example, a free OpenRouter model — in the same pipeline (query, judge, profile).

## Goal

Introduce an OpenAI Chat Completions HTTP transport as a new model `type: openai_compat` next to `cli` in `scripts/config.yaml`. The dispatch is on the **API contract** (OpenAI Chat Completions), not on a specific provider. Provider URL and auth env-var name are per-instance config, so swapping from OpenRouter to OpenAI direct (or any other compatible endpoint) is a config edit, not a code change.

The new transport satisfies the same `ModelInterface` contract `CLIModel` already satisfies (`scripts/src/model_interface.py:16-22`), so the testing/judging pipeline picks it up without changes to callers. It is opt-in: not added to any default profile, disabled in config by default.

The first wired instance:
- Short name: **`openrouter_gemma`**
- `base_url`: `https://openrouter.ai/api/v1`
- `api_key_env`: `OPENROUTER_API_KEY`
- `model_id`: `google/gemma-4-31b-it:free`

## External Facts (informational, not acceptance scope)

These describe the upstream API contract and the first wired provider; validated by a live call on 2026-05-01. They explain why the spec looks the way it does; they are not testable inside this repo.

- API contract: OpenAI Chat Completions. Endpoint suffix `/chat/completions`. Used by OpenAI proper, OpenRouter, Together, Groq, Anyscale, Azure OpenAI, Ollama, vLLM, llama.cpp server, and most "OpenAI-compatible" providers.
- First wired provider: OpenRouter. Base URL `https://openrouter.ai/api/v1`. Auth `Authorization: Bearer <key>` from `OPENROUTER_API_KEY`.
- First wired model: `google/gemma-4-31b-it:free`, $0/M, 262144 context, 32768 max output. Live call returned HTTP 200.
- Response: text in `choices[0].message.content`. Free-tier responses include `cost: 0` and `cached_tokens: 0`.
- The model emits JSON inside ```json``` code fences for analytical prompts. The same shape `CLIModel._strip_markdown_code_blocks()` already handles.
- Sessions: OpenRouter (and the OpenAI Chat Completions contract generally) is stateless. No server-side conversation API. Document context is re-sent in `messages` per query. Prompt caching exists for some providers but is out of scope here.

## Repo Facts (acceptance-relevant, verified in code)

- `ModelInterface` ABC and `CLIModel` live in `scripts/src/model_interface.py:16-99`.
- `ModelFactory.create()` dispatches on the config `type` field at `scripts/src/model_interface.py:114-119`.
- `ModelManager.__init__` currently swallows model construction failures with a `print` at `scripts/src/model_interface.py:133-139`. AC-9 below requires changing that for `openai_compat` models.
- `ModelManager` is constructed in five sites: `scripts/polish.py:53`, `scripts/src/testing_step.py:105`, `scripts/src/detection_step.py:172`, `scripts/src/questioning_step.py:481`, `scripts/src/questioning_step.py:540`.
- `--judge <name>` is parsed in four entry points: `scripts/polish.py:488`, `scripts/detect_ambiguities.py:31`, `scripts/generate_report.py:32`, `scripts/test_questions.py:31`.
- `session_manager.SessionManager.init_session` calls `get_session_handler(name, config)` (`scripts/src/session_manager.py:69-72`), which raises `ValueError` for unknown model names (`scripts/src/session_handlers.py:297-320`); `init_sessions_parallel` only catches `SessionCreationError` (`session_manager.py:101-113`). AC-26/27 require this to not crash when an `openai_compat` model is in the model list.
- No `python-dotenv` import exists anywhere in `scripts/` and `python-dotenv` is not in `requirements.txt`.

## Acceptance Criteria

**Config schema**

1. `scripts/config.yaml` recognizes the literal string value `openai_compat` as a valid model `type`.
2. `ModelFactory.create()` (`scripts/src/model_interface.py:114-119`) dispatches `type: openai_compat` to a new model class.
3. The new model class implements `ModelInterface.query(prompt) -> Dict[str, Any]`.
4. The new class accepts a REQUIRED config field `base_url` (string; no default). Example: `https://openrouter.ai/api/v1`.
5. The new class accepts a REQUIRED config field `api_key_env` (string; no default). Names the env var that holds the bearer token. Example: `OPENROUTER_API_KEY`.
6. The new class accepts a REQUIRED config field `model_id` (string). Example: `google/gemma-4-31b-it:free`.
7. The new class accepts a config field `timeout` (integer seconds; default 60 when absent).
8. The new class accepts an OPTIONAL config field `max_tokens` (integer). When the config field is absent, no default is applied and the field is omitted from the HTTP request body (AC-12), letting the upstream provider apply its own default.

**Auth and env loading**

9. The new class reads its bearer token from the env var named in its `api_key_env` config field, at construction time. The env var name is NOT hardcoded in the class.
10. `.env` in `document_polishing/` is loaded into process env before any `ModelManager` is constructed in any of the five constructor sites listed in Repo Facts.
11. When an `openai_compat` model is `enabled: true` in config and the env var named in its `api_key_env` is unset, the process exits non-zero before any document query is issued, and the error message visible to the user names the missing env var. (Today `ModelManager.__init__` swallows construction errors with a `print`; that path must change for `openai_compat` models so the absence is fatal at startup, not a swallowed warning.)

**Request shape**

12. The HTTP request goes to `POST <base_url>/chat/completions`, where `base_url` is the configured value (no trailing-slash assumption either way). `Authorization: Bearer <token>` header is set from the env var named in `api_key_env`.
13. The request body is JSON with these required fields: `model` (= configured `model_id`) and `messages` (a list with a single object `{"role": "user", "content": <prompt>}`). The `max_tokens` field is included ONLY when set in config (AC-8); otherwise it is omitted from the request body.
14. The prompt passed to the model produces JSON output suitable for the existing pipeline parsers — i.e., either a parseable JSON object or a string containing one (with or without ```json``` code fences).

**Response shape — return value parity with CLIModel**

15. HTTP 200 with body whose `choices[0].message.content` parses as JSON → `query()` returns the parsed dict.
16. HTTP 200 with `choices[0].message.content` wrapping JSON in ```json``` code fences → `query()` returns the parsed dict (same outcome as AC-15).
17. HTTP 200 with `choices[0].message.content` that is not JSON → `query()` returns `{"error": False, "raw_response": <content>}`.
18. HTTP non-2xx → `query()` returns `{"error": True, "stderr": <response_text>, "raw_response": <response_text>}` matching `CLIModel.query()` non-zero-exit shape (`model_interface.py:65-70`).
19. Connection error or HTTP timeout → `query()` returns `{"error": True, "message": <str>}` matching `CLIModel.query()` exception shape (`model_interface.py:80-85`).

**First wired instance: openrouter_gemma**

20. The first OR-pointing entry in `scripts/config.yaml` uses the short name `openrouter_gemma` with: `type: openai_compat`, `base_url: https://openrouter.ai/api/v1`, `api_key_env: OPENROUTER_API_KEY`, `model_id: google/gemma-4-31b-it:free`, `enabled: false`.
21. `openrouter_gemma` is referenceable by name in any profile's `models:` list.
22. `openrouter_gemma` can be passed to `polish.py --judge openrouter_gemma` and is used as the judge.
23. `openrouter_gemma` can be passed to `detect_ambiguities.py --judge openrouter_gemma` and is used as the judge.
24. `openrouter_gemma` can be passed to `generate_report.py --judge openrouter_gemma` and is used as the judge.
25. `openrouter_gemma` can be passed to `test_questions.py --judge openrouter_gemma` and is used as the judge.

**Sessions — must not crash when sessions are enabled**

26. With `session_management.enabled: true` and any `openai_compat` model in the active profile's `models:` list, `ModelManager.init_sessions(...)` does NOT raise (i.e., the unknown-model `ValueError` from `get_session_handler` is not surfaced).
27. With `session_management.enabled: true` and an `openai_compat` model queried, `ModelManager.query(<name>, prompt)` returns a normal response (the model is queried statelessly, bypassing the session path).
28. With `session_management.enabled: true`, the existing CLI handlers (`claude`, `gemini`, `codex`) continue to use sessions exactly as today — no behavior change observable in their tests.

**Dependencies**

29. `requirements.txt` gains an established HTTP client dependency (implementer's choice; pinned with a version specifier).
30. `requirements.txt` gains `python-dotenv`, pinned with a version specifier.

**Tests**

31. New tests cover: HTTP 200 JSON response → parsed dict.
32. New tests cover: HTTP 200 JSON-in-code-fences → parsed dict.
33. New tests cover: HTTP 200 non-JSON content → `{"error": False, "raw_response": ...}`.
34. New tests cover: HTTP non-2xx → `{"error": True, "stderr": ..., "raw_response": ...}`.
35. New tests cover: network exception → `{"error": True, "message": ...}`.
36. New tests cover: missing env var (named in `api_key_env`) with `openai_compat` model `enabled: true` → fatal startup error per AC-11.
37. New tests cover: switching `base_url` and `api_key_env` to a different provider in config produces a request to the new URL with the new bearer token, with no code change. (Demonstrates provider-agnosticism.)
38. The full existing test suite (`pytest tests/`) passes after the changes.

**Documentation**

39. `AGENTS.md` "Quick Commands" section gains a one-line example showing how to run a query against `openrouter_gemma`.

## Anti-criteria

- No changes to `ClaudeSessionHandler`, `GeminiSessionHandler`, `CodexSessionHandler`, or `CLIModel`.
- No new session handler subclass for `openai_compat`. (How `openai_compat` models are excluded from the session path — filtering before `get_session_handler`, returning a no-op, etc. — is the implementer's choice; the observable contract is AC-26/27.)
- No streaming responses. Single-response JSON only.
- No automatic retry loop. HTTP 429 surfaces via AC-18 like any other non-2xx.
- No `cache_control` fields in the request payload.
- No model auto-discovery from any provider's `/models` endpoint.
- No provider-specific URLs or env-var names hardcoded in the model class. Provider identity lives entirely in `config.yaml` per-instance fields (`base_url`, `api_key_env`, `model_id`).
- No paid models in this scope. The `model_id` value committed in `config.yaml` for `openrouter_gemma` must end in `:free`.
- No changes to default `quick`, `standard`, `thorough` profiles' `models:` lists.
- No orchestration changes in `polish.py` beyond the `.env` load call required by AC-10.
- No silent fallback when the configured env var is missing while an `openai_compat` model is enabled — fail loud (AC-11).
- No live API calls in unit tests. HTTP must be mocked.
- The `.env` value rename (`open_router_api_key` → `OPENROUTER_API_KEY`) is a one-line manual edit performed once before deploy; it is not an acceptance criterion the implementer can fail.

## Context Files

- `scripts/src/model_interface.py` — `ModelInterface` (the contract), `CLIModel` (the shape to mirror), `ModelFactory.create()` (the dispatch point), `ModelManager` (consumer).
- `scripts/src/session_handlers.py` — `get_session_handler` factory; do not add an `openai_compat` handler here.
- `scripts/src/session_manager.py` — `init_session` / `init_sessions_parallel`; AC-26 lives here.
- `scripts/config.yaml` — Add the new model entry per AC-20.
- `scripts/polish.py:53`, `scripts/src/testing_step.py:105`, `scripts/src/detection_step.py:172`, `scripts/src/questioning_step.py:481`, `scripts/src/questioning_step.py:540` — five `ModelManager` constructor sites; AC-10 requires `.env` load before each.
- `scripts/polish.py:488`, `scripts/detect_ambiguities.py:31`, `scripts/generate_report.py:32`, `scripts/test_questions.py:31` — four `--judge` flag sites; AC-22 through AC-25 each test one of these.
- `requirements.txt` — Add HTTP client and `python-dotenv`, both pinned.
- `tests/` — New test file covering AC-31 through AC-37.
- `AGENTS.md` — "Quick Commands" example.
- `.env` — Operator action: rename `open_router_api_key` to `OPENROUTER_API_KEY` (value preserved). Out of acceptance scope.
