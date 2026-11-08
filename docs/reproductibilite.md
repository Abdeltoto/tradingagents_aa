# Reproductibilité

Deux runs du même ticker et de la même date **peuvent différer**. C’est le régime d’un outil LLM, pas un bug.

## Sources de variance

1. **Échantillonnage.** Même `temperature=0`, les APIs ne garantissent pas le bit-à-bit. Les modèles *reasoning* (GPT-6, thinking mode) varient plus.  
2. **Données live.** News, StockTwits, Reddit bougent. La date d’analyse fige la fenêtre de prix, pas le social « maintenant ».  
3. **Outils.** Un timeout vendor, un retry, un article de moins.

## Ce qui ne varie plus

- L’identité de la société est résolue **avant** les agents (fini les « mauvaises compagnies » d’un run à l’autre).  
- Les prix et indicateurs du market analyst passent par un snapshot vérifié.  
- Point-in-time : pas de filing futur, pas de restatement anachronique.

## Resserrer

```python
config["temperature"] = 0.0
# Les modèles reasoning ignorent souvent temperature.
# Nommez un modèle non-reasoning dans quick_think_llm / deep_think_llm.
```

```
TRADINGAGENTS_TEMPERATURE=0.0
```

Traitez le framework comme un **échafaudage de recherche**, pas une stratégie au rendement fixe.
