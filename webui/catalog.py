"""Read-only catalog the desk UI uses: providers, models, keys, defaults."""

from __future__ import annotations

import os
from datetime import date

import requests

from cli.prompts import ANALYST_CHOICES, _llm_provider_table, detect_asset_type
from tradingagents.default_config import DEFAULT_CONFIG
from tradingagents.llm_clients.api_key_env import PROVIDER_API_KEY_ENV, get_api_key_env
from tradingagents.llm_clients.model_catalog import get_model_options


def _ollama_pulled() -> list[str]:
    url = (os.environ.get("OLLAMA_BASE_URL") or "http://localhost:11434/v1").rstrip("/")
    tags = url[:-3] + "/api/tags" if url.endswith("/v1") else url.rstrip("/") + "/api/tags"
    try:
        payload = requests.get(tags, timeout=1.5).json()
        return [m["name"] for m in payload.get("models", []) if m.get("name")]
    except Exception:
        return []


def _models_for(provider: str, mode: str) -> list[dict[str, str]]:
    options = []
    try:
        listed = get_model_options(provider, mode)
    except KeyError:
        listed = [("Custom model ID", "custom")]
    for label, value in listed:
        options.append({"label": label, "value": value})
    if provider == "ollama":
        known = {row["value"] for row in options}
        for name in _ollama_pulled():
            if name not in known:
                options.insert(0, {"label": f"{name} (installed)", "value": name})
    return options


def _key_status(provider: str) -> dict:
    env_name = get_api_key_env(provider)
    if env_name is None:
        return {"required": False, "env": None, "present": True}
    value = os.environ.get(env_name, "")
    return {"required": True, "env": env_name, "present": bool(value.strip())}


def meta() -> dict:
    providers = []
    for label, key, url in _llm_provider_table():
        providers.append({
            "label": label,
            "id": key,
            "backend_url": url,
            "key": _key_status(key),
            "models": {
                "quick": _models_for(key, "quick"),
                "deep": _models_for(key, "deep"),
            },
        })

    cfg = DEFAULT_CONFIG
    ollama = next((p for p in providers if p["id"] == "ollama"), None)
    default_provider = cfg.get("llm_provider") or "openai"
    if ollama and _ollama_pulled() and not os.environ.get("TRADINGAGENTS_LLM_PROVIDER"):
        default_provider = "ollama"

    return {
        "today": date.today().isoformat(),
        "defaults": {
            "ticker": "SPY",
            "date": date.today().isoformat(),
            "analysts": ["market", "social", "news", "fundamentals"],
            "research_depth": 1,
            "output_language": cfg.get("output_language") or "English",
            "llm_provider": default_provider,
            "quick_think_llm": cfg.get("quick_think_llm"),
            "deep_think_llm": cfg.get("deep_think_llm"),
            "checkpoint_enabled": bool(cfg.get("checkpoint_enabled")),
        },
        "analysts": [
            {"id": analyst.value, "label": label}
            for label, analyst in ANALYST_CHOICES
        ],
        "depths": [
            {"id": 1, "label": "Shallow — 1 debate round"},
            {"id": 3, "label": "Medium — 3 debate rounds"},
            {"id": 5, "label": "Deep — 5 debate rounds"},
        ],
        "languages": ["English", "Français", "中文", "日本語", "Español", "Deutsch"],
        "providers": providers,
        "ollama_models": _ollama_pulled(),
        "config": {
            "results_dir": cfg.get("results_dir"),
            "llm_provider": cfg.get("llm_provider"),
            "quick_think_llm": cfg.get("quick_think_llm"),
            "deep_think_llm": cfg.get("deep_think_llm"),
        },
        "key_env": {k: v for k, v in PROVIDER_API_KEY_ENV.items() if v},
    }


def detect_ticker_kind(ticker: str) -> str:
    return detect_asset_type(ticker).value
