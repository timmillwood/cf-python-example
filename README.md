# Python FastAPI + LangChain Worker

A Cloudflare Python Worker using FastAPI and LangChain with Workers AI.

## Endpoints

- `GET /` - Health check
- `POST /chat` - Chat with AI
- `POST /summarize` - Summarize text  
- `POST /translate` - Translate text

## Development

```bash
uv run pywrangler dev
```

## Deploy

```bash
uv run pywrangler deploy
```
