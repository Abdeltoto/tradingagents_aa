# Security

TradingDesk binds **127.0.0.1** by default. Do not expose `--host 0.0.0.0` without an auth layer: `/api/settings` writes `.env`, and `/api/runs` spends LLM budget.

- Never commit `.env` or `chatgpt-auth.json`.  
- `SEC_EDGAR_USER_AGENT` should be a contact **you** own.  
- Report engine issues that are not UI-specific to [TauricResearch/TradingAgents](https://github.com/TauricResearch/TradingAgents/security).
