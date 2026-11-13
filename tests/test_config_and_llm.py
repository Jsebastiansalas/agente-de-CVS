"""Pruebas para la configuración y el cliente encapsulado de Gemini (HU-0.1)."""

from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest
from google.genai.errors import APIError
from pydantic import BaseModel

from src.config import ScoringWeights, Settings
from src.llm.gemini_client import GeminiClient, GeminiClientError, _compute_retry_delay


class _DummyOutput(BaseModel):
    label: str
    score: int


def test_scoring_weights_must_sum_to_one() -> None:
    weights = ScoringWeights()
    assert weights.relevant_experience == 0.40

    with pytest.raises(ValueError, match="sumar 1.0"):
        ScoringWeights(
            relevant_experience=0.5,
            must_have_skills=0.5,
            nice_to_have_skills=0.2,
            education_and_languages=0.1,
        )


def test_settings_validate_thresholds() -> None:
    with pytest.raises(ValueError, match="acceptable_threshold"):
        Settings(acceptable_threshold=55.0, reservations_threshold=60.0)


def test_gemini_client_requires_api_key() -> None:
    settings = Settings(gemini_api_key="")
    with pytest.raises(GeminiClientError, match="GEMINI_API_KEY"):
        GeminiClient(settings=settings)


def test_gemini_client_generate_structured_success() -> None:
    mock_sdk_client = MagicMock()
    mock_sdk_client.models.generate_content.return_value = SimpleNamespace(
        parsed=_DummyOutput(label="ACEPTABLE", score=88),
        text='{"label": "ACEPTABLE", "score": 88}',
    )

    settings = Settings(gemini_api_key="test-key", gemini_flash_model="gemini-2.5-flash")
    client = GeminiClient(settings=settings, client=mock_sdk_client)

    result = client.generate_structured(
        contents="Evaluar candidato",
        response_schema=_DummyOutput,
    )

    assert result == _DummyOutput(label="ACEPTABLE", score=88)
    mock_sdk_client.models.generate_content.assert_called_once()


def test_gemini_client_retries_on_rate_limit(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr("src.llm.gemini_client.time.sleep", lambda _: None)

    mock_sdk_client = MagicMock()
    rate_limit_error = APIError(429, {"error": {"message": "Rate limit"}})
    mock_sdk_client.models.generate_content.side_effect = [
        rate_limit_error,
        SimpleNamespace(
            parsed=None,
            text='{"label": "ACEPTABLE", "score": 91}',
        ),
    ]

    settings = Settings(
        gemini_api_key="test-key",
        gemini_max_retries=3,
        gemini_retry_base_delay=0.01,
    )
    client = GeminiClient(settings=settings, client=mock_sdk_client)

    result = client.generate_structured(
        contents="Evaluar con reintento",
        response_schema=_DummyOutput,
    )

    assert result.score == 91
    assert mock_sdk_client.models.generate_content.call_count == 2


def test_compute_retry_delay_respects_rpm_and_fails_fast_on_daily_quota() -> None:
    rpm_err = APIError(429, {"error": {"message": "Rate limit. Please retry in 12.5s"}})
    assert _compute_retry_delay(rpm_err, attempt=1, base_delay=1.0) == 13.5

    daily_err = APIError(
        429,
        {
            "error": {
                "message": "GenerateRequestsPerDayPerProjectPerModel-FreeTier. "
                "Please retry in 53881s"
            }
        },
    )
    assert _compute_retry_delay(daily_err, attempt=1, base_delay=1.0) is None
