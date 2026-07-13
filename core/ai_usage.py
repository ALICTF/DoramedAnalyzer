from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from core.settings import get_settings


@dataclass
class AIUsageRecord:
    provider: str
    operation: str
    model: str
    input_tokens: int = 0
    output_tokens: int = 0
    total_tokens: int = 0
    estimated_cost_usd: float = 0.0
    pricing_configured: bool = False


@dataclass
class AIUsageTracker:
    provider: str = "gapgpt"
    records: List[AIUsageRecord] = field(default_factory=list)

    def record_response(self, response: Any, *, operation: str, requested_model: str) -> None:
        usage = getattr(response, "usage", None)
        response_model = getattr(response, "model", None)
        model = str(response_model or requested_model)

        input_tokens = _read_int(usage, "prompt_tokens")
        output_tokens = _read_int(usage, "completion_tokens")
        total_tokens = _read_int(usage, "total_tokens") or input_tokens + output_tokens

        cost, pricing_configured = self._estimate_cost(
            model=model,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
        )

        self.records.append(
            AIUsageRecord(
                provider=self.provider,
                operation=operation,
                model=model,
                input_tokens=input_tokens,
                output_tokens=output_tokens,
                total_tokens=total_tokens,
                estimated_cost_usd=cost,
                pricing_configured=pricing_configured,
            )
        )

    def to_dict(self) -> Dict[str, Any]:
        by_model: Dict[str, Dict[str, Any]] = {}
        total_input_tokens = 0
        total_output_tokens = 0
        total_tokens = 0
        total_cost = 0.0
        pricing_configured = True

        for record in self.records:
            model_bucket = by_model.setdefault(
                record.model,
                {
                    "provider": record.provider,
                    "model": record.model,
                    "calls": 0,
                    "input_tokens": 0,
                    "output_tokens": 0,
                    "total_tokens": 0,
                    "estimated_cost_usd": 0.0,
                    "pricing_configured": record.pricing_configured,
                    "operations": [],
                },
            )
            model_bucket["calls"] += 1
            model_bucket["input_tokens"] += record.input_tokens
            model_bucket["output_tokens"] += record.output_tokens
            model_bucket["total_tokens"] += record.total_tokens
            model_bucket["estimated_cost_usd"] += record.estimated_cost_usd
            model_bucket["pricing_configured"] = (
                bool(model_bucket["pricing_configured"]) and record.pricing_configured
            )
            model_bucket["operations"].append(
                {
                    "operation": record.operation,
                    "input_tokens": record.input_tokens,
                    "output_tokens": record.output_tokens,
                    "total_tokens": record.total_tokens,
                    "estimated_cost_usd": round(record.estimated_cost_usd, 8),
                    "pricing_configured": record.pricing_configured,
                }
            )

            total_input_tokens += record.input_tokens
            total_output_tokens += record.output_tokens
            total_tokens += record.total_tokens
            total_cost += record.estimated_cost_usd
            pricing_configured = pricing_configured and record.pricing_configured

        for model_bucket in by_model.values():
            model_bucket["estimated_cost_usd"] = round(model_bucket["estimated_cost_usd"], 8)

        return {
            "used_ai": bool(self.records),
            "provider": self.provider if self.records else None,
            "models": list(by_model.values()),
            "summary": {
                "calls": len(self.records),
                "input_tokens": total_input_tokens,
                "output_tokens": total_output_tokens,
                "total_tokens": total_tokens,
                "estimated_cost_usd": round(total_cost, 8),
                "pricing_configured": pricing_configured if self.records else False,
                "currency": "USD",
                "pricing_note": self._pricing_note(pricing_configured),
            },
        }

    def _estimate_cost(self, *, model: str, input_tokens: int, output_tokens: int) -> tuple[float, bool]:
        pricing = get_settings().model_pricing_usd_per_1m_tokens.get(model)
        if not pricing:
            return 0.0, False

        input_cost = input_tokens * pricing["input_per_1m"] / 1_000_000
        output_cost = output_tokens * pricing["output_per_1m"] / 1_000_000
        return input_cost + output_cost, True

    def _pricing_note(self, pricing_configured: bool) -> Optional[str]:
        if not self.records:
            return "AI was not used."
        if pricing_configured:
            return None
        return "Token usage is recorded, but model pricing is not configured or is incomplete."


def _read_int(obj: Any, key: str) -> int:
    if obj is None:
        return 0
    value = getattr(obj, key, None)
    if value is None and isinstance(obj, dict):
        value = obj.get(key)
    try:
        return int(value or 0)
    except (TypeError, ValueError):
        return 0


def aggregate_ai_usage(reports: List[Dict[str, Any]]) -> Dict[str, Any]:
    by_model: Dict[str, Dict[str, Any]] = {}
    total_calls = 0
    total_input_tokens = 0
    total_output_tokens = 0
    total_tokens = 0
    total_cost = 0.0
    used_ai = False
    pricing_configured = True
    provider: Optional[str] = None

    for report in reports:
        usage = report.get("ai_usage") or {}
        if not usage.get("used_ai"):
            continue

        used_ai = True
        provider = provider or usage.get("provider")
        summary = usage.get("summary") or {}
        total_calls += int(summary.get("calls") or 0)
        total_input_tokens += int(summary.get("input_tokens") or 0)
        total_output_tokens += int(summary.get("output_tokens") or 0)
        total_tokens += int(summary.get("total_tokens") or 0)
        total_cost += float(summary.get("estimated_cost_usd") or 0.0)
        pricing_configured = pricing_configured and bool(summary.get("pricing_configured"))

        for model_usage in usage.get("models") or []:
            model = model_usage.get("model") or "unknown"
            model_bucket = by_model.setdefault(
                model,
                {
                    "provider": model_usage.get("provider"),
                    "model": model,
                    "calls": 0,
                    "input_tokens": 0,
                    "output_tokens": 0,
                    "total_tokens": 0,
                    "estimated_cost_usd": 0.0,
                    "pricing_configured": True,
                    "operations": [],
                },
            )
            model_bucket["calls"] += int(model_usage.get("calls") or 0)
            model_bucket["input_tokens"] += int(model_usage.get("input_tokens") or 0)
            model_bucket["output_tokens"] += int(model_usage.get("output_tokens") or 0)
            model_bucket["total_tokens"] += int(model_usage.get("total_tokens") or 0)
            model_bucket["estimated_cost_usd"] += float(model_usage.get("estimated_cost_usd") or 0.0)
            model_bucket["pricing_configured"] = (
                bool(model_bucket["pricing_configured"]) and bool(model_usage.get("pricing_configured"))
            )
            model_bucket["operations"].extend(model_usage.get("operations") or [])

    for model_bucket in by_model.values():
        model_bucket["estimated_cost_usd"] = round(model_bucket["estimated_cost_usd"], 8)

    return {
        "used_ai": used_ai,
        "provider": provider if used_ai else None,
        "models": list(by_model.values()),
        "summary": {
            "calls": total_calls,
            "input_tokens": total_input_tokens,
            "output_tokens": total_output_tokens,
            "total_tokens": total_tokens,
            "estimated_cost_usd": round(total_cost, 8),
            "pricing_configured": pricing_configured if used_ai else False,
            "currency": "USD",
            "pricing_note": _aggregate_pricing_note(used_ai, pricing_configured),
        },
    }


def _aggregate_pricing_note(used_ai: bool, pricing_configured: bool) -> Optional[str]:
    if not used_ai:
        return "AI was not used."
    if pricing_configured:
        return None
    return "Token usage is recorded, but model pricing is not configured or is incomplete."
