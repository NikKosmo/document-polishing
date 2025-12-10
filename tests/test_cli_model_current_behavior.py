import sys
from types import SimpleNamespace


# Make scripts/src importable
project_root = __import__("pathlib").Path(__file__).resolve().parents[1]
scripts_src = project_root.joinpath("scripts", "src")
sys.path.insert(0, scripts_src.as_posix())


class FakeCompletedProcess(SimpleNamespace):
    pass


def test_query_parses_json_fenced(monkeypatch):
    model_interface = __import__("model_interface")
    CLIModel = getattr(model_interface, "CLIModel")

    payload = """```json\n{\"ok\": true,\"n\": 1}\n```"""

    def fake_run(cmd, input, capture_output, text, timeout):
        return FakeCompletedProcess(stdout=payload, stderr="", returncode=0)

    monkeypatch.setattr("subprocess.run", fake_run)

    model = CLIModel(command="gemini")
    res = model.query("prompt")
    assert res == {"ok": True, "n": 1}


def test_query_returns_raw_when_not_json(monkeypatch):
    model_interface = __import__("model_interface")
    CLIModel = getattr(model_interface, "CLIModel")

    payload = "not a json payload"

    def fake_run(cmd, input, capture_output, text, timeout):
        return FakeCompletedProcess(stdout=payload, stderr="", returncode=0)

    monkeypatch.setattr("subprocess.run", fake_run)

    model = CLIModel(command="gemini")
    res = model.query("prompt")
    assert res.get("error") is False
    assert res.get("raw_response") == payload


def test_query_handles_timeout(monkeypatch):
    model_interface = __import__("model_interface")
    CLIModel = getattr(model_interface, "CLIModel")

    def fake_run(cmd, input, capture_output, text, timeout):
        raise __import__("subprocess").TimeoutExpired(cmd=cmd, timeout=timeout)

    monkeypatch.setattr("subprocess.run", fake_run)

    model = CLIModel(command="gemini", timeout=1)
    res = model.query("prompt")
    assert res.get("error") is True
    assert "Timeout" in res.get("message", "")
