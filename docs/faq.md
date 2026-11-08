# FAQ

## Windows : `no Windows console available`

Le CLI interactif utilise prompt_toolkit, qui exige un buffer console. Lancez depuis **Windows Terminal**, PowerShell ou cmd, pas depuis un terminal pipé (certains panneaux d’IDE).  
TradingDesk n’a pas ce problème : `python -m webui`.

## Le desk ne s’ouvre pas

```bash
pip install ".[web]"
python -m webui --no-browser
```

Puis [http://127.0.0.1:8787](http://127.0.0.1:8787). Port pris : `--port 8788`.

## Aucune clé, ça tourne ?

Oui, avec **Ollama** (`ollama list` non vide). TradingDesk le présélectionne.

## `REVIEW` au lieu d’un rating

Le texte du portfolio manager n’a pas de ligne `Rating: …` lisible. Ce n’est **pas** un Hold. Relancez, ou lisez la décision.

## Reprendre une run crashée

CLI : `tradingagents --checkpoint`. Desk : case Checkpoints. Signature différente (modèle, analystes, date) → run neuve.

## Le backtest est lent

Chaque cellule = un graphe complet. Réduisez analystes, rounds, plage, ou `--every`. Reprenez avec `--run-id`.

## Docker et Azure

Les images n’incluent plus `.env` / `.env.enterprise`. Mettez les clés Azure dans `.env`.

## Mise à jour Tauric au boot du CLI

Check 1×/jour, rien sur vos runs. Couper : `TRADINGAGENTS_NO_UPDATE_CHECK=1`.

## Contribuer / citer

[CONTRIBUTING.md](../CONTRIBUTING.md). Citation du papier : [README](../README.md#crédits).
