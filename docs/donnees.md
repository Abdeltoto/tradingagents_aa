# Données et marchés

## Tickers

Tout ce que Yahoo Finance couvre, suffixe d’échange compris.

| Marché | Exemple |
|---|---|
| US | `AAPL`, `SPY` |
| Hong Kong | `0700.HK` |
| Tokyo | `7203.T` |
| Londres | `AZN.L` |
| Inde | `RELIANCE.NS`, `.BO` |
| Canada | `.TO` |
| Australie | `.AX` |
| A-shares | `600519.SS`, `.SZ` |
| Crypto | `BTC-USD`, `ETH-USD` |

L’identité société et le benchmark alpha (souvent `SPY`, sinon l’indice régional) se résolvent tout seuls. `BTCUSD` est normalisé en `BTC-USD`.

## Vendors

Le routeur (`tradingagents/dataflows/router.py`) enchaîne **exactement** les vendors configurés — pas de fallback silencieux hors liste.

Typiquement :

- Prix / indicateurs : Yahoo, optionnellement Alpha Vantage  
- News : Yahoo search (le feed Yahoo news a été instable), Alpha Vantage  
- Social : StockTwits, Reddit  
- Fondamentaux US : **SEC EDGAR** (pas de clé ; `SEC_EDGAR_USER_AGENT` recommandé)  
- Macro : FRED (`FRED_API_KEY`, gratuit)  
- Prédiction : Polymarket  

## SEC EDGAR

Les comptes US sont lus **tels que déposés** à la date du run. Une restatement ultérieure ne réécrit pas le passé. Apple 2008 : `$39.6B` déposé, `$36.2B` restated en 2010 — un run intercalaire lit `39.6B`.

Pas de compte EDGAR. La SEC exige un User-Agent joignable :

```
SEC_EDGAR_USER_AGENT=Votre Nom votre@email.com
```

Filings machine-readable ≈ 2009+. Un T4 non publié n’est pas interpolé. HK / A-shares tombent sur le vendor suivant.

Yahoo fundamentals datent la **période**, pas le dépôt : un run historique les refuse.

Les insider trades sont datés de l’événement, pas du dépôt : un run passé les refuse aussi.

## Alpha Vantage / FRED

```
ALPHA_VANTAGE_API_KEY=
FRED_API_KEY=
```

Alpha Vantage est filtré look-ahead sur les news.

## Crypto

Pas d’analyste fundamentals. Sentiment : sources crypto dédiées (corrigées en 0.3.x).
