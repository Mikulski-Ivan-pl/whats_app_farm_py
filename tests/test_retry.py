"""Tests for Cerebras retry logic in llm.py."""
import sys
import time
from pathlib import Path
from unittest.mock import MagicMock, call, patch

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

# Patch settings and Cerebras client before importing llm
_mock_settings = MagicMock()
_mock_settings.llm_api_key = "test-key"
_mock_settings.cerebras_model = "test-model"
_mock_settings.system_prompt = "You are a helpful assistant."

with patch("config.settings", _mock_settings), patch("cerebras.cloud.sdk.Cerebras"):
    import llm


def _status_error(status_code: int):
    """Create a fake APIStatusError with the given status_code."""
    from cerebras.cloud.sdk import APIStatusError

    response = MagicMock()
    response.status_code = status_code
    return APIStatusError(
        message=f"HTTP {status_code}",
        response=response,
        body=None,
    )


def _make_response(content: str):
    resp = MagicMock()
    resp.choices[0].message.content = content
    return resp


# ---------------------------------------------------------------------------
# _call_with_retry
# ---------------------------------------------------------------------------


def test_succeeds_on_first_attempt():
    fn = MagicMock(return_value=_make_response("ok"))
    result = llm._call_with_retry(fn, model="m", messages=[])
    assert result.choices[0].message.content == "ok"
    assert fn.call_count == 1


def test_retries_on_503_then_succeeds(monkeypatch):
    monkeypatch.setattr(llm.time, "sleep", lambda _: None)

    fn = MagicMock(
        side_effect=[
            _status_error(503),
            _status_error(503),
            _make_response("recovered"),
        ]
    )
    result = llm._call_with_retry(fn, model="m", messages=[])
    assert result.choices[0].message.content == "recovered"
    assert fn.call_count == 3


def test_raises_after_all_retries_exhausted(monkeypatch):
    monkeypatch.setattr(llm.time, "sleep", lambda _: None)

    fn = MagicMock(side_effect=_status_error(503))
    with pytest.raises(Exception) as exc_info:
        llm._call_with_retry(fn, model="m", messages=[])
    assert fn.call_count == 4  # 1 initial + 3 retries
    assert "503" in str(exc_info.value)


def test_does_not_retry_on_4xx(monkeypatch):
    monkeypatch.setattr(llm.time, "sleep", lambda _: None)

    fn = MagicMock(side_effect=_status_error(429))
    with pytest.raises(Exception):
        llm._call_with_retry(fn, model="m", messages=[])
    assert fn.call_count == 1  # no retries


def test_retries_on_connection_error(monkeypatch):
    monkeypatch.setattr(llm.time, "sleep", lambda _: None)

    from cerebras.cloud.sdk import APIConnectionError

    class _FakeConnError(APIConnectionError):
        def __init__(self):
            Exception.__init__(self, "connection refused")

    fn = MagicMock(
        side_effect=[
            _FakeConnError(),
            _make_response("ok after conn error"),
        ]
    )
    result = llm._call_with_retry(fn, model="m", messages=[])
    assert result.choices[0].message.content == "ok after conn error"
    assert fn.call_count == 2


def test_backoff_delays_are_correct(monkeypatch):
    """Verify that sleep is called with 2, 4, 8 seconds in order."""
    slept = []
    monkeypatch.setattr(llm.time, "sleep", slept.append)

    fn = MagicMock(side_effect=_status_error(503))
    with pytest.raises(Exception):
        llm._call_with_retry(fn, model="m", messages=[])

    assert slept == [2, 4, 8]


def test_no_sleep_on_success(monkeypatch):
    slept = []
    monkeypatch.setattr(llm.time, "sleep", slept.append)

    fn = MagicMock(return_value=_make_response("ok"))
    llm._call_with_retry(fn, model="m", messages=[])
    assert slept == []
