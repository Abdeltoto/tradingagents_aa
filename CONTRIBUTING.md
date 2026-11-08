# Contribuer

Merci. Ce dépôt est un fork de [Tauric Research / TradingAgents](https://github.com/TauricResearch/TradingAgents) plus **TradingDesk**.

## Où ça va

| Changement | Dossier |
|---|---|
| Moteur, vendors, agents | `tradingagents/` — préférer aussi un PR **upstream** |
| CLI | `cli/` |
| Desk / API | `webui/` |
| Docs, README, visuels | `docs/`, `assets/marketing/` |

Les correctifs de graphe, de dates ou de vendors appartiennent d’abord à Tauric. Ce fork n’est pas le lieu pour diverger du contrat point-in-time.

## Dev

```bash
python -m venv .venv
.\.venv\Scripts\activate   # Windows
pip install ".[dev,web]"
pytest
ruff check .
```

Tests d’intégration (réseau / clés) : `pytest -m integration`.

## Desk

```bash
python -m webui --no-browser
```

Ne commitez pas de `.env`. Les clés passent par `.env.example` (vide) et la page Réglages.

## Commits

Messages comme le changelog upstream : **pourquoi**, pas le diff. Ex. `desk: stream the same graph the CLI uses`.

## Licence

Apache 2.0. En envoyant un PR vous acceptez la même licence. Citer le papier si vous publiez des résultats.

```
Xiao et al., TradingAgents, arXiv:2412.20138
```
