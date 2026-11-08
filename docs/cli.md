# CLI

Le binaire `tradingagents` est le chemin d’origine du papier. TradingDesk l’enveloppe ; il ne le remplace pas.

## Lancer

```bash
tradingagents              # installé
python -m cli.main         # depuis les sources
```

**Windows.** Le CLI interactif a besoin d’un buffer console réel. Message d’erreur :

```
Error: no Windows console available. The interactive CLI needs a real console buffer
— run it from Windows Terminal, PowerShell, or cmd.exe
```

Ouvrez Windows Terminal dans le dossier du projet. Le desk (`python -m webui`) contourne cette contrainte.

## Questions

À l’ouverture : ticker, date, analystes, profondeur, fournisseur, modèles, langue. Les réponses stables sont mémorisées dans `~/.tradingagents/cli_prefs.json` (pas le ticker ni la date). Les variables `TRADINGAGENTS_*` **sautent** leur question.

## Flags

```bash
tradingagents --ticker NVDA --date 2026-09-23 --analysts market,news,fundamentals --save --no-show
tradingagents --checkpoint
tradingagents --clear-checkpoints
tradingagents --portfolio book.json
tradingagents --html / --no-html
```

Sans TTY, une question encore ouverte arrête la run et nomme le flag ou la variable manquante.

## Backtest

```bash
tradingagents backtest NVDA,AAPL --start 2026-06-01 --end 2026-08-01 --every 7
tradingagents backtest NVDA --start 2026-06-01 --end 2026-08-01 --run-id 20260601_120000
```

Voir [backtest.md](backtest.md).

## ChatGPT Plus / Pro

Pas de clé API. Une fois :

```bash
tradingagents login chatgpt
```

Le CLI imprime une URL. La session est dans `~/.tradingagents/chatgpt-auth.json`.

```bash
tradingagents logout chatgpt
```

Dans Docker, coller l’URL de callback. Les runs comptent dans le quota du forfait. `temperature` et `max_tokens` ne s’appliquent pas.

## Docker

```bash
cp .env.example .env
docker compose run --rm tradingagents
docker compose build          # après un pull
docker compose --profile ollama run --rm tradingagents-ollama
```

Données : volume `tradingagents_data`, ou `TRADINGAGENTS_DATA_DIR=./data`.

L’image n’embarque pas les fichiers `.env`.

## Sorties

Pour un ticker `NVDA` le `2026-09-01` :

```
~/.tradingagents/logs/NVDA/2026-09-01/reports/*.md
~/.tradingagents/logs/NVDA/TradingAgentsStrategy_logs/full_states_log_2026-09-01.json
~/.tradingagents/logs/reports/NVDA_<stamp>/complete_report.html
~/.tradingagents/memory/trading_memory.md
```

## Captures d’origine

<p align="center">
  <img src="../assets/cli/cli_init.png" width="100%" alt="CLI init">
</p>

<p align="center">
  <img src="../assets/cli/cli_news.png" width="100%" alt="CLI news">
</p>
