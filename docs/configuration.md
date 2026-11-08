# Configuration

Tout passe par `DEFAULT_CONFIG` (`tradingagents/default_config.py`) puis les variables `TRADINGAGENTS_*`. Le CLI, le desk et `propagate()` lisent le même objet.

## Fichiers

| Fichier | Rôle |
|---|---|
| `.env` | Clés + overrides. Copier `.env.example` |
| `.env.enterprise` | Azure OpenAI (Docker : mettre les clés dans `.env`) |
| `~/.tradingagents/cli_prefs.json` | Dernières réponses CLI (pas ticker/date) |
| `~/.tradingagents/chatgpt-auth.json` | Session ChatGPT |

`load_dotenv` au import du package : le cwd gagne, les variables déjà exportées ne sont pas écrasées.

## Variables de run

| Variable | Clé config | Défaut |
|---|---|---|
| `TRADINGAGENTS_LLM_PROVIDER` | `llm_provider` | `openai` |
| `TRADINGAGENTS_QUICK_THINK_LLM` | `quick_think_llm` | `gpt-6-luna` |
| `TRADINGAGENTS_DEEP_THINK_LLM` | `deep_think_llm` | `gpt-6-sol` |
| `TRADINGAGENTS_QUICK_THINK_PROVIDER` | palier quick | = provider principal |
| `TRADINGAGENTS_DEEP_THINK_PROVIDER` | palier deep | = provider principal |
| `TRADINGAGENTS_LLM_BACKEND_URL` | `backend_url` | endpoint du provider |
| `TRADINGAGENTS_OUTPUT_LANGUAGE` | `output_language` | `English` |
| `TRADINGAGENTS_MAX_DEBATE_ROUNDS` | `max_debate_rounds` | `1` |
| `TRADINGAGENTS_MAX_RISK_ROUNDS` | `max_risk_discuss_rounds` | `1` |
| `TRADINGAGENTS_MAX_TOOL_ROUNDS` | `max_tool_rounds` | `20` |
| `TRADINGAGENTS_CHECKPOINT_ENABLED` | `checkpoint_enabled` | `false` |
| `TRADINGAGENTS_TEMPERATURE` | `temperature` | unset |
| `TRADINGAGENTS_LLM_MAX_RETRIES` | `llm_max_retries` | SDK default |
| `TRADINGAGENTS_MAX_TOKENS` | `max_tokens` | unset |
| `TRADINGAGENTS_OPENAI_REASONING_EFFORT` | | |
| `TRADINGAGENTS_GOOGLE_THINKING_LEVEL` | | |
| `TRADINGAGENTS_ANTHROPIC_EFFORT` | | |
| `TRADINGAGENTS_NO_UPDATE_CHECK` | | checks Tauric 1×/jour |

## Chemins

| Variable | Défaut |
|---|---|
| `TRADINGAGENTS_RESULTS_DIR` | `~/.tradingagents/logs` |
| `TRADINGAGENTS_CACHE_DIR` | `~/.tradingagents/cache` |
| `TRADINGAGENTS_MEMORY_LOG_PATH` | `~/.tradingagents/memory/trading_memory.md` |
| `TRADINGAGENTS_DATA_DIR` | Docker : volume |
| `TRADINGAGENTS_BENCHMARK_TICKER` | indice régional (ex. `SPY`) |

## Exemple `.env`

```
TRADINGAGENTS_LLM_PROVIDER=ollama
TRADINGAGENTS_QUICK_THINK_LLM=deepseek-r1:8b
TRADINGAGENTS_DEEP_THINK_LLM=gpt-oss:20b
TRADINGAGENTS_OUTPUT_LANGUAGE=English
TRADINGAGENTS_MAX_DEBATE_ROUNDS=1
TRADINGAGENTS_MAX_RISK_ROUNDS=1
OLLAMA_BASE_URL=http://localhost:11434/v1
SEC_EDGAR_USER_AGENT=Your Name your@email.com
```

Un booléen mal tapé (`treu`) **plante** au démarrage — volontaire.

## Python

```python
config = DEFAULT_CONFIG.copy()
config["llm_provider"] = "anthropic"
config["deep_think_llm"] = "claude-opus-5-5"
config["quick_think_llm"] = "claude-sonnet-5"
config["max_debate_rounds"] = 2
config["temperature"] = 0.0
```

Paliers hétérogènes :

```python
config["llm_provider"] = "openai"
config["quick_think_llm"] = "gpt-6-luna"
config["deep_think_provider"] = "anthropic"
config["deep_think_llm"] = "claude-opus-5-5"
```
