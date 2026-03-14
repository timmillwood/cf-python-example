# Python FastAPI + Langchain Worker with Workers AI

A Cloudflare Python Worker that combines FastAPI with Langchain, using Workers AI as the LLM backend.

## Features

- **FastAPI**: Modern, fast web framework with automatic OpenAPI documentation
- **Langchain**: LLM framework for building AI applications
- **Workers AI**: Cloudflare's serverless GPU-powered AI inference

## Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/` | GET | Health check and list available endpoints |
| `/chat` | POST | Chat with the AI model |
| `/summarize` | POST | Summarize text |
| `/translate` | POST | Translate text to another language |

## Setup

### Prerequisites

- [Node.js](https://nodejs.org/) (v18+)
- [Wrangler CLI](https://developers.cloudflare.com/workers/wrangler/install-and-update/)
- [uv](https://docs.astral.sh/uv/) (Python package manager)

### Install Dependencies

```bash
# Install wrangler globally (if not already installed)
npm install -g wrangler

# Install Python dependencies with uv
uv sync
```

### Development

Run the worker locally:

```bash
npx wrangler dev
```

### Deploy

Deploy to Cloudflare:

```bash
npx wrangler deploy
```

## Usage Examples

### Chat

```bash
curl -X POST http://localhost:8787/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "What is the capital of France?"}'
```

### Summarize

```bash
curl -X POST http://localhost:8787/summarize \
  -H "Content-Type: application/json" \
  -d '{"text": "Long text to summarize...", "max_length": 50}'
```

### Translate

```bash
curl -X POST http://localhost:8787/translate \
  -H "Content-Type: application/json" \
  -d '{"text": "Hello, world!", "target_language": "French"}'
```

## Available Models

You can specify different Workers AI models in the `/chat` endpoint:

- `@cf/meta/llama-3.1-8b-instruct` (default)
- `@cf/meta/llama-3.1-70b-instruct`
- `@cf/mistral/mistral-7b-instruct-v0.1`
- `@hf/thebloke/llama-2-13b-chat-awq`

See the [Workers AI Models](https://developers.cloudflare.com/workers-ai/models/) page for all available models.

## Project Structure

```
├── src/
│   └── main.py          # FastAPI app with Langchain integration
├── pyproject.toml       # Python dependencies
├── wrangler.toml        # Cloudflare Worker configuration
└── README.md
```

## How It Works

1. **Custom LLM Wrapper**: The `CloudflareWorkersAI` class extends Langchain's `LLM` base class to use Workers AI bindings
2. **ASGI Adapter**: The `on_fetch` function converts Cloudflare Worker requests to ASGI format for FastAPI
3. **Langchain Chains**: Each endpoint uses Langchain's prompt templates and chains for structured LLM interactions
