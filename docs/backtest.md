# Backtest

Une run = une décision. Ça ne dit pas si le système **décide bien**. Le backtest rejoue le graphe sur une grille ticker × dates et score les décisions dont la fenêtre a coté.

Ce n’est **pas** un simulateur de portefeuille : pas de fills, pas de cash ledger. Les cellules sont indépendantes. Un JSON portfolio, s’il est passé, est le **même livre** pour chaque cellule.

## CLI

```bash
tradingagents backtest NVDA,AAPL --start 2026-06-01 --end 2026-08-01 --every 7
```

Reprise :

```bash
tradingagents backtest NVDA,AAPL --start 2026-06-01 --end 2026-08-01 --run-id 20260601_120000
```

Les cellules déjà dans le log de ce `run_id` sont sautées.

## Desk

Page **Backtest** : tickers, bornes, pas. Provider/modèles repris du formulaire d’analyse. Le fil affiche `[i/n] TICKER date` puis le résumé.

## Python

```python
from tradingagents.backtest import iter_grid, run_backtest, summarize

dates = iter_grid("2026-06-01", "2026-08-01", every_n_days=7)
result = run_backtest(["NVDA", "AAPL"], dates, config, selected_analysts=["market", "news"])
print(summarize(result).render())
print(result.run_id)
```

## Score

- Entrée au **premier close après** la date d’analyse (un run lit des news post-clôture).  
- Alpha vs benchmark régional.  
- Groupé par rating. Hold n’a pas de direction : pas de hit-rate.  
- `REVIEW` : unscored.  
- La mémoire **live** n’est pas écrite : chaque sweep a son log.

Les chiffres ne sont pas un track record publiable. Une cellule = un échantillon LLM + des flux non archivés. Voir [reproductibilite.md](reproductibilite.md).
