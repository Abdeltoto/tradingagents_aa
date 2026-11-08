# Fournisseurs LLM

18 backends. Une clé **ou** Ollama **ou** un endpoint OpenAI-compatible.

## Tableau

| Provider | Variable de clé | Notes |
|---|---|---|
| OpenAI | `OPENAI_API_KEY` | défaut catalogue GPT-6 |
| Google | `GOOGLE_API_KEY` | Gemini |
| Anthropic | `ANTHROPIC_API_KEY` | Claude |
| ChatGPT Plus/Pro | (login) | `tradingagents login chatgpt` |
| xAI | `XAI_API_KEY` | Grok |
| DeepSeek | `DEEPSEEK_API_KEY` | |
| Qwen internat. | `DASHSCOPE_API_KEY` | |
| Qwen CN | `DASHSCOPE_CN_API_KEY` | |
| GLM internat. | `ZHIPU_API_KEY` | Z.AI |
| GLM CN | `ZHIPU_CN_API_KEY` | BigModel |
| MiniMax | `MINIMAX_API_KEY` | |
| MiniMax CN | `MINIMAX_CN_API_KEY` | |
| OpenRouter | `OPENROUTER_API_KEY` | |
| Mistral | `MISTRAL_API_KEY` | |
| Kimi | `MOONSHOT_API_KEY` | |
| Groq | `GROQ_API_KEY` | |
| NVIDIA NIM | `NVIDIA_API_KEY` | |
| Azure OpenAI | `.env.enterprise` | |
| Amazon Bedrock | AWS chain / bearer | `pip install ".[bedrock]"` |
| Ollama | aucune | `OLLAMA_BASE_URL` |
| OpenAI-compatible | `OPENAI_COMPATIBLE_API_KEY` optionnel | vLLM, LM Studio, llama.cpp |

Catalogue des IDs : `tradingagents/llm_clients/model_catalog.py`. « Custom model ID » accepte n’importe quel ID que le serveur sert.

## Ollama

```
TRADINGAGENTS_LLM_PROVIDER=ollama
OLLAMA_BASE_URL=http://localhost:11434/v1
```

Serveur distant : même variable, URL du `ollama-serve`. TradingDesk liste `GET /api/tags`.

## OpenAI-compatible

```
TRADINGAGENTS_LLM_PROVIDER=openai_compatible
TRADINGAGENTS_LLM_BACKEND_URL=http://localhost:1234/v1
TRADINGAGENTS_QUICK_THINK_LLM=mon-modele
TRADINGAGENTS_DEEP_THINK_LLM=mon-modele
```

vLLM : `http://localhost:8000/v1`. LM Studio : `http://localhost:1234/v1`.

## Bedrock

```bash
pip install ".[bedrock]"
```

```
TRADINGAGENTS_LLM_PROVIDER=bedrock
AWS_DEFAULT_REGION=us-west-2
# AWS_BEARER_TOKEN_BEDROCK=  ou ~/.aws/credentials
```

ID d’exemple : `us.anthropic.claude-opus-5-5`.

## Jev (sentiment)

`TYPESAFE_API_KEY` : le Sentiment Analyst filtre StockTwits/Reddit. Sans clé, les posts passent. `TYPESAFE_DEFAULT_MODEL=jev-1.13.0` pour figer. Via OpenRouter : `TYPESAFE_BASE_URL=https://openrouter.ai/api`.
