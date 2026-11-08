# Démarrage

Trois portes vers le même graphe : **TradingDesk**, le **CLI**, ou `TradingAgentsGraph` en Python.

## Prérequis

- Python **3.11** ou plus (3.13 testé)  
- Un fournisseur LLM : **Ollama** en local, ou une clé (OpenAI, Anthropic, Gemini, …)  
- Windows, macOS ou Linux. Sur Windows, le CLI interactif exige une **vraie console** (Windows Terminal, PowerShell, cmd) — pas un terminal pipé.

## Installer

```bash
git clone https://github.com/Abdeltoto/tradingagents_aa.git
cd tradingagents_aa
python -m venv .venv
```

Windows :

```powershell
.\.venv\Scripts\activate
python -m pip install --upgrade pip
pip install ".[web]"
copy .env.example .env
```

macOS / Linux :

```bash
source .venv/bin/activate
pip install ".[web]"
cp .env.example .env
```

`[web]` installe FastAPI et Uvicorn pour TradingDesk. Sans UI : `pip install .`

Avec [uv](https://docs.astral.sh/uv/) :

```bash
uv venv --python 3.13
uv pip install ".[web]"
```

## Choisir un cerveau

### Option A — Ollama (aucune clé)

```bash
ollama pull gpt-oss:20b
ollama pull deepseek-r1:8b
```

TradingDesk détecte les modèles installés et présélectionne Ollama.  
Dans `.env` vous pouvez figer :

```
TRADINGAGENTS_LLM_PROVIDER=ollama
TRADINGAGENTS_QUICK_THINK_LLM=deepseek-r1:8b
TRADINGAGENTS_DEEP_THINK_LLM=gpt-oss:20b
```

### Option B — Clé cloud

Ouvrez `.env` et renseignez **une** clé. Voir [fournisseurs.md](fournisseurs.md).

```
OPENAI_API_KEY=sk-...
TRADINGAGENTS_LLM_PROVIDER=openai
```

Ou depuis TradingDesk → **Réglages** (écrit dans `.env`).

## Lancer TradingDesk

```bash
python -m webui
```

Le navigateur s’ouvre sur [http://127.0.0.1:8787](http://127.0.0.1:8787).

1. **Nouvelle analyse** — ticker (`SPY`, `NVDA`, `0700.HK`, `BTC-USD`), date, analystes, modèles  
2. **Lancer l’analyse** — la salle des marchés suit les cinq équipes  
3. **Rapports** — HTML `complete_report.html` comme le CLI  

Sans navigateur : `python -m webui --no-browser --port 8787`

## Lancer le CLI

```bash
python -m cli.main
# ou, une fois le package installé :
tradingagents
```

Sur Windows, si vous voyez `no Windows console available`, ouvrez **Windows Terminal** dans le dossier du projet et relancez la commande. Détail : [cli.md](cli.md).

Run non interactive :

```bash
set TRADINGAGENTS_LLM_PROVIDER=ollama
set TRADINGAGENTS_QUICK_THINK_LLM=deepseek-r1:8b
set TRADINGAGENTS_DEEP_THINK_LLM=gpt-oss:20b
set TRADINGAGENTS_OUTPUT_LANGUAGE=English
set TRADINGAGENTS_MAX_DEBATE_ROUNDS=1
set TRADINGAGENTS_MAX_RISK_ROUNDS=1
python -m cli.main --ticker NVDA --date 2026-09-23 --analysts market,news,fundamentals --save --no-show
```

## Première run Python

```python
from tradingagents.graph.trading_graph import TradingAgentsGraph
from tradingagents.default_config import DEFAULT_CONFIG

config = DEFAULT_CONFIG.copy()
config["llm_provider"] = "ollama"
config["quick_think_llm"] = "deepseek-r1:8b"
config["deep_think_llm"] = "gpt-oss:20b"

ta = TradingAgentsGraph(debug=True, config=config)
state, decision = ta.propagate("NVDA", "2026-09-01")
print(decision)
ta.save_reports(state, "NVDA")
```

Les rapports vivent sous `~/.tradingagents/` (surcharge : `TRADINGAGENTS_RESULTS_DIR`).

## Docker

```bash
cp .env.example .env   # clés
docker compose run --rm tradingagents
```

Ollama via le profil :

```bash
docker compose --profile ollama run --rm tradingagents-ollama
```

Après un `git pull` : `docker compose build`.

## Vérifier que ça tourne

| Test | Attendu |
|---|---|
| `python -m webui` | page TradingDesk, sidebar Desk / Analyse / … |
| Cotation `SPY` sur le desk | dernier prix Yahoo |
| CLI `--help` | Typer, options `--ticker`, `backtest`, `login` |
| Une run courte (1 round, 1–2 analystes) | rating à 5 paliers ou `REVIEW` |

Suite : [TradingDesk](tradingdesk.md) · [configuration](configuration.md)
