from types import SimpleNamespace

from core.ai_usage import AIUsageTracker, aggregate_ai_usage


def test_ai_usage_records_tokens_without_pricing():
    tracker = AIUsageTracker(provider="gapgpt")
    response = SimpleNamespace(
        model="gpt-test",
        usage=SimpleNamespace(prompt_tokens=100, completion_tokens=40, total_tokens=140),
    )

    tracker.record_response(response, operation="classification.text", requested_model="gpt-test")
    usage = tracker.to_dict()

    assert usage["used_ai"] is True
    assert usage["summary"]["calls"] == 1
    assert usage["summary"]["input_tokens"] == 100
    assert usage["summary"]["output_tokens"] == 40
    assert usage["summary"]["estimated_cost_usd"] == 0.0
    assert usage["summary"]["pricing_configured"] is False
    assert usage["models"][0]["operations"][0]["operation"] == "classification.text"


def test_ai_usage_calculates_default_model_cost():
    tracker = AIUsageTracker(provider="gapgpt")
    response = SimpleNamespace(
        model="gemini-2.5-flash-lite",
        usage=SimpleNamespace(prompt_tokens=1_000_000, completion_tokens=1_000_000, total_tokens=2_000_000),
    )

    tracker.record_response(response, operation="oxygen.vision_extraction", requested_model="gemini-2.5-flash-lite")
    usage = tracker.to_dict()

    assert usage["summary"]["pricing_configured"] is True
    assert usage["summary"]["estimated_cost_usd"] == 0.5
    assert usage["models"][0]["estimated_cost_usd"] == 0.5


def test_aggregate_ai_usage_combines_file_reports():
    first = {
        "ai_usage": {
            "used_ai": True,
            "provider": "gapgpt",
            "models": [
                {
                    "provider": "gapgpt",
                    "model": "gemini-2.5-flash-lite",
                    "calls": 1,
                    "input_tokens": 100,
                    "output_tokens": 50,
                    "total_tokens": 150,
                    "estimated_cost_usd": 0.00003,
                    "pricing_configured": True,
                    "operations": [{"operation": "oxygen.vision_extraction"}],
                }
            ],
            "summary": {
                "calls": 1,
                "input_tokens": 100,
                "output_tokens": 50,
                "total_tokens": 150,
                "estimated_cost_usd": 0.00003,
                "pricing_configured": True,
            },
        }
    }
    second = {
        "ai_usage": {
            "used_ai": True,
            "provider": "gapgpt",
            "models": [
                {
                    "provider": "gapgpt",
                    "model": "gemini-2.5-flash-lite",
                    "calls": 1,
                    "input_tokens": 200,
                    "output_tokens": 80,
                    "total_tokens": 280,
                    "estimated_cost_usd": 0.000052,
                    "pricing_configured": True,
                    "operations": [{"operation": "ecg.vision_extraction"}],
                }
            ],
            "summary": {
                "calls": 1,
                "input_tokens": 200,
                "output_tokens": 80,
                "total_tokens": 280,
                "estimated_cost_usd": 0.000052,
                "pricing_configured": True,
            },
        }
    }

    aggregate = aggregate_ai_usage([first, second])

    assert aggregate["summary"]["calls"] == 2
    assert aggregate["summary"]["input_tokens"] == 300
    assert aggregate["summary"]["output_tokens"] == 130
    assert aggregate["summary"]["estimated_cost_usd"] == 0.000082
    assert aggregate["models"][0]["calls"] == 2
