import json
from unittest.mock import MagicMock, patch

import pytest
from testing_step import TestingStep


@pytest.fixture
def mock_models_config():
    return {
        "claude": {"type": "anthropic", "model": "claude-3-5-sonnet-20240620"},
        "gemini": {"type": "google", "model": "gemini-1.5-pro-002"},
    }


@pytest.fixture
def sample_sections():
    return [
        {"header": "Section 0", "content": "Content 0"},
        {"header": "Section 1", "content": "Content 1"},
        {"header": "Section 2", "content": "Content 2"},
    ]


@pytest.fixture
def temp_output(tmp_path):
    return tmp_path / "test_results.json"


@pytest.fixture
def partial_output(temp_output):
    return temp_output.with_name(f"{temp_output.stem}_partial{temp_output.suffix}")


def test_partial_file_deleted_after_success(mock_models_config, sample_sections, temp_output, partial_output):
    """1. Partial file is deleted after a successful full run"""
    step = TestingStep(mock_models_config)

    with patch.object(step.model_manager, "query_all", return_value={"claude": MagicMock(), "gemini": MagicMock()}):
        result = step.test_sections(sample_sections, ["claude", "gemini"], output_path=str(temp_output))
        result.save(str(temp_output))

    assert temp_output.exists()
    assert not partial_output.exists()


def test_partial_file_contains_results_mid_run(mock_models_config, sample_sections, temp_output, partial_output):
    """2. Partial file contains results mid-run"""
    step = TestingStep(mock_models_config)

    call_count = 0

    def side_effect(*args, **kwargs):
        nonlocal call_count
        res = {"claude": f"interpretation {call_count}"}
        call_count += 1
        return res

    # To test mid-run, we can raise an exception on the 2nd section
    def failing_side_effect(*args, **kwargs):
        nonlocal call_count
        # The saving happens AFTER query_all returns.
        # So we let it finish the first two sections, and then fail.
        res = side_effect(*args, **kwargs)

        if call_count == 2:  # Section 0 and 1 are done.
            # We need to make sure the loop continues to the save part but fails before section 2.
            # Wait, the save happens at the END of the loop body.
            # If we raise here, it won't save section 1.
            pass

        return res

    # New strategy: use a mock for json.dump to trigger the failure after it's called twice
    import json as json_module

    original_dump = json_module.dump
    dump_count = 0

    def failing_dump(*args, **kwargs):
        nonlocal dump_count
        original_dump(*args, **kwargs)
        dump_count += 1
        if dump_count == 2:
            raise RuntimeError("Interrupted after 2nd save")

    with patch.object(step.model_manager, "query_all", side_effect=side_effect):
        with patch("json.dump", side_effect=failing_dump):
            try:
                step.test_sections(sample_sections, ["claude"], output_path=str(temp_output))
            except RuntimeError:
                pass

    assert partial_output.exists()
    with open(partial_output, "r") as f:
        data = json.load(f)
        assert "section_0" in data
        assert "section_1" in data
        assert "section_2" not in data


def test_resume_skips_completed_sections(mock_models_config, sample_sections, temp_output, partial_output):
    """3. Resume skips already-completed sections"""
    # Pre-create partial file
    partial_data = {
        "section_0": {"section": sample_sections[0], "results": {"claude": "old result 0"}},
        "section_1": {"section": sample_sections[1], "results": {"claude": "old result 1"}},
    }
    partial_output.parent.mkdir(parents=True, exist_ok=True)
    with open(partial_output, "w") as f:
        json.dump(partial_data, f)

    step = TestingStep(mock_models_config)

    with patch.object(step.model_manager, "query_all", return_value={"claude": "new result"}) as mock_query:
        result = step.test_sections(sample_sections, ["claude"], output_path=str(temp_output), resume=True)

    # Should only call query_all for section_2
    assert mock_query.call_count == 1
    assert "section_0" in result.test_results
    assert result.test_results["section_0"]["results"]["claude"] == "old result 0"
    assert "section_2" in result.test_results
    assert result.test_results["section_2"]["results"]["claude"] == "new result"


def test_resume_false_ignores_partial_file(mock_models_config, sample_sections, temp_output, partial_output):
    """4. Resume=False ignores existing partial file"""
    # Pre-create partial file
    partial_data = {
        "section_0": {"section": sample_sections[0], "results": {"claude": "old result 0"}},
    }
    partial_output.parent.mkdir(parents=True, exist_ok=True)
    with open(partial_output, "w") as f:
        json.dump(partial_data, f)

    step = TestingStep(mock_models_config)

    with patch.object(step.model_manager, "query_all", return_value={"claude": "new result"}) as mock_query:
        result = step.test_sections(sample_sections, ["claude"], output_path=str(temp_output), resume=False)

    # Should call query_all for all sections
    assert mock_query.call_count == len(sample_sections)
    assert result.test_results["section_0"]["results"]["claude"] == "new result"


def test_no_partial_file_without_output_path(mock_models_config, sample_sections, partial_output):
    """5. No partial file when output_path is not given"""
    step = TestingStep(mock_models_config)

    with patch.object(step.model_manager, "query_all", return_value={"claude": "res"}):
        step.test_sections(sample_sections, ["claude"])

    assert not partial_output.exists()
