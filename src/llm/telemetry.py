"""Telemetría de tokens, latencia y costo estimado por llamada a Gemini (HU-3.2)."""

import logging
import threading
from dataclasses import dataclass, field

from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)

# Tarifas aproximadas USD por 1M de tokens (referencia para monitoreo de costos)
MODEL_PRICING_PER_1M: dict[str, tuple[float, float]] = {
    "gemini-2.5-flash": (0.15, 0.60),
    "gemini-2.5-flash-lite": (0.075, 0.30),
    "gemini-2.5-pro": (1.25, 10.00),
    "gemini-3.1-pro-preview": (1.25, 10.00),
}


class CallUsageRecord(BaseModel):
    """Registro individual de consumo y latencia de una invocación LLM."""

    model: str
    operation: str
    prompt_tokens: int = Field(default=0, ge=0)
    output_tokens: int = Field(default=0, ge=0)
    cached_tokens: int = Field(default=0, ge=0)
    total_tokens: int = Field(default=0, ge=0)
    latency_ms: float = Field(default=0.0, ge=0.0)
    estimated_cost_usd: float = Field(default=0.0, ge=0.0)


class UsageSummary(BaseModel):
    """Resumen agregado de consumo de tokens, latencia y costo."""

    total_calls: int = 0
    total_prompt_tokens: int = 0
    total_output_tokens: int = 0
    total_cached_tokens: int = 0
    total_tokens: int = 0
    total_latency_ms: float = 0.0
    avg_latency_ms: float = 0.0
    total_estimated_cost_usd: float = 0.0


def estimate_cost_usd(
    model: str,
    prompt_tokens: int,
    output_tokens: int,
    cached_tokens: int = 0,
) -> float:
    """Estima el costo en USD considerando descuento aproximado del 75% en tokens cacheados."""
    input_rate, output_rate = MODEL_PRICING_PER_1M.get(model, (0.30, 2.50))
    uncached_input = max(0, prompt_tokens - cached_tokens)
    cached_cost = (cached_tokens / 1_000_000) * (input_rate * 0.25)
    input_cost = (uncached_input / 1_000_000) * input_rate
    output_cost = (output_tokens / 1_000_000) * output_rate
    return round(input_cost + cached_cost + output_cost, 6)


def extract_usage_from_response(
    response: object,
    *,
    model: str,
    operation: str,
    latency_ms: float,
) -> CallUsageRecord:
    """Extrae metadatos de uso de una respuesta del SDK google-genai."""
    metadata = getattr(response, "usage_metadata", None)
    prompt_tokens = int(getattr(metadata, "prompt_token_count", 0) or 0)
    output_tokens = int(getattr(metadata, "candidates_token_count", 0) or 0)
    cached_tokens = int(getattr(metadata, "cached_content_token_count", 0) or 0)
    total_tokens = int(
        getattr(metadata, "total_token_count", 0) or (prompt_tokens + output_tokens)
    )
    cost = estimate_cost_usd(model, prompt_tokens, output_tokens, cached_tokens)

    return CallUsageRecord(
        model=model,
        operation=operation,
        prompt_tokens=prompt_tokens,
        output_tokens=output_tokens,
        cached_tokens=cached_tokens,
        total_tokens=total_tokens,
        latency_ms=round(latency_ms, 2),
        estimated_cost_usd=cost,
    )


@dataclass
class UsageTracker:
    """Acumulador thread-safe de métricas de uso de Gemini."""

    records: list[CallUsageRecord] = field(default_factory=list)
    _lock: threading.Lock = field(default_factory=threading.Lock, repr=False)

    def record(self, item: CallUsageRecord) -> None:
        """Registra una llamada en memoria y emite un log estructurado."""
        with self._lock:
            self.records.append(item)
        logger.info(
            "gemini_call model=%s op=%s latency_ms=%.1f tokens_in=%d tokens_out=%d "
            "cached=%d cost_usd=%.6f",
            item.model,
            item.operation,
            item.latency_ms,
            item.prompt_tokens,
            item.output_tokens,
            item.cached_tokens,
            item.estimated_cost_usd,
        )

    def summary(self) -> UsageSummary:
        """Devuelve métricas agregadas del acumulador."""
        with self._lock:
            snapshot = list(self.records)

        if not snapshot:
            return UsageSummary()

        total_calls = len(snapshot)
        total_prompt = sum(r.prompt_tokens for r in snapshot)
        total_output = sum(r.output_tokens for r in snapshot)
        total_cached = sum(r.cached_tokens for r in snapshot)
        total_tokens = sum(r.total_tokens for r in snapshot)
        total_latency = round(sum(r.latency_ms for r in snapshot), 2)
        total_cost = round(sum(r.estimated_cost_usd for r in snapshot), 6)

        return UsageSummary(
            total_calls=total_calls,
            total_prompt_tokens=total_prompt,
            total_output_tokens=total_output,
            total_cached_tokens=total_cached,
            total_tokens=total_tokens,
            total_latency_ms=total_latency,
            avg_latency_ms=round(total_latency / total_calls, 2),
            total_estimated_cost_usd=total_cost,
        )

    def reset(self) -> None:
        """Limpia el historial de registros."""
        with self._lock:
            self.records.clear()
