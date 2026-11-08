# Positionnement

## Une phrase

**TradingDesk : le CLI est déjà une salle. Le desk en est l’image.**

## Catégorie

Pas un « AI stock picker ». Pas un copilot de courtage.

C’est un **banc d’essai de recherche** : une décision de trading décomposée en rôles LLM, avec intégrité point-in-time, et deux interfaces (CLI + desk).

## Pour qui

| Persona | Job-to-be-done | Message |
|---|---|---|
| Chercheur / étudiant quant × LLM | Reproduire le papier, varier modèles | Graphe ouvert, backtest, date contractuelle |
| Builder local-first | Tourner sans OpenAI | Ollama détecté, 18 providers |
| Démo interne | Montrer la firme en 2 min | Salle des marchés live |
| Quant curieux | Lire *pourquoi* Buy | Rapports HTML + débat bull/bear |

## Pas pour qui

- Qui veut un bouton « placer l’ordre ».  
- Qui attend un Sharpe publié et reproductible.  
- Qui refuse de lire un disclaimer.

## Différenciation

| | TradingAgents upstream | Ce fork |
|---|---|---|
| Moteur | LangGraph, 5 équipes | **le même** |
| Interface | CLI Rich (`Live` = salle) | le même tampon, levé en SPA |
| Windows IDE | console buffer | le desk s’en moque |
| Docs | README unique | landing + docs FR/EN + kit |

Concurrent « agents trading » : la plupart collent un LLM sur du Yahoo. Ici : **date**, **SEC as-filed**, **mémoire réglée**, **REVIEW ≠ Hold**.

## Promesses qu’on tient

1. Même graphe CLI et desk.  
2. Pas d’ordre réel.  
3. Un run passé ne lit pas un filing futur.  
4. Crédit Tauric / arXiv visible.

## Promesses qu’on ne fait pas

- Alpha stable.  
- Identité bit-à-bit entre deux runs.  
- Couverture réglementaire (MiFID, CIF, etc.).

## Vocabulaire

| Dire | Éviter |
|---|---|
| firme, salle des marchés, run, rating | bot, signal, holy grail, 10x |
| recherche, échafaudage | production trading, automated wealth |
| Ollama, point-in-time | « GPT qui trade pour vous » |

## Identité visuelle

- Charbon `#0b1013`, encre `#e7ecef`, émeraude `#14c290`, or muet `#c9b37a`  
- Sérif éditorial + mono pour les tickers  
- Fichiers : `assets/marketing/` (`hero`, `og`, `mark`, `architecture`, `warroom`, `cli-and-desk`, `screenshot-desk`)

GitHub → Settings → Social preview : `assets/marketing/og.jpg`
