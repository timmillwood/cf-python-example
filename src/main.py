"""
Cloudflare Python Worker with FastAPI and Langchain using Workers AI.

This worker exposes a FastAPI application that uses Langchain with 
Cloudflare Workers AI as the LLM backend.
"""

from fastapi import FastAPI, Request
from pydantic import BaseModel
from langchain_core.language_models.llms import LLM
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from typing import Any, List, Optional
import js
from pyodide.ffi import to_js as _to_js


def to_js(obj):
    """Convert Python dict to JavaScript Object."""
    return _to_js(obj, dict_converter=js.Object.fromEntries)


# Custom LLM wrapper for Cloudflare Workers AI
class CloudflareWorkersAI(LLM):
    """Custom Langchain LLM that uses Cloudflare Workers AI binding."""
    
    ai_binding: Any = None
    model: str = "@cf/meta/llama-3.1-8b-instruct"
    
    class Config:
        arbitrary_types_allowed = True
    
    @property
    def _llm_type(self) -> str:
        return "cloudflare-workers-ai"
    
    def _call(
        self,
        prompt: str,
        stop: Optional[List[str]] = None,
        **kwargs: Any,
    ) -> str:
        # Synchronous call not supported in Workers environment
        raise NotImplementedError("Use _acall for async operations")
    
    async def _acall(
        self,
        prompt: str,
        stop: Optional[List[str]] = None,
        **kwargs: Any,
    ) -> str:
        """Async call to Workers AI."""
        if self.ai_binding is None:
            raise ValueError("AI binding not set")
        
        response = await self.ai_binding.run(
            self.model,
            to_js({"prompt": prompt})
        )
        
        return response.response


# Create FastAPI app
app = FastAPI(
    title="Langchain + Workers AI API",
    description="A FastAPI application using Langchain with Cloudflare Workers AI",
    version="1.0.0"
)


# Request models
class ChatRequest(BaseModel):
    message: str
    model: str = "@cf/meta/llama-3.1-8b-instruct"


class SummarizeRequest(BaseModel):
    text: str
    max_length: int = 100


class TranslateRequest(BaseModel):
    text: str
    target_language: str = "Spanish"


# Store the AI binding globally for the request context
_ai_binding = None


def get_llm(model: str = "@cf/meta/llama-3.1-8b-instruct") -> CloudflareWorkersAI:
    """Get an LLM instance with the current AI binding."""
    return CloudflareWorkersAI(ai_binding=_ai_binding, model=model)


@app.get("/")
async def root():
    """Health check endpoint."""
    return {
        "status": "ok",
        "service": "Langchain + Workers AI API",
        "endpoints": ["/chat", "/summarize", "/translate"]
    }


@app.post("/chat")
async def chat(request: ChatRequest):
    """
    Chat endpoint using Langchain with Workers AI.
    
    Send a message and get an AI-generated response.
    """
    llm = get_llm(request.model)
    
    prompt_template = ChatPromptTemplate.from_messages([
        ("system", "You are a helpful AI assistant. Be concise and informative."),
        ("human", "{input}")
    ])
    
    # Format prompt manually and call LLM directly to avoid asyncio.create_task context issue
    formatted = prompt_template.format(input=request.message)
    response = await llm._acall(formatted)
    
    return {
        "response": response,
        "model": request.model
    }


@app.post("/summarize")
async def summarize(request: SummarizeRequest):
    """
    Summarize text using Langchain with Workers AI.
    """
    llm = get_llm()
    
    prompt_template = ChatPromptTemplate.from_messages([
        ("system", "You are a text summarization expert. Summarize the following text concisely in about {max_length} words or fewer."),
        ("human", "{text}")
    ])
    
    # Format prompt manually and call LLM directly to avoid asyncio.create_task context issue
    formatted = prompt_template.format(text=request.text, max_length=request.max_length)
    summary = await llm._acall(formatted)
    
    return {
        "summary": summary,
        "original_length": len(request.text.split()),
    }


@app.post("/translate")
async def translate(request: TranslateRequest):
    """
    Translate text to a target language using Langchain with Workers AI.
    """
    llm = get_llm()
    
    prompt_template = ChatPromptTemplate.from_messages([
        ("system", "You are a professional translator. Translate the following text to {target_language}. Only output the translation, nothing else."),
        ("human", "{text}")
    ])
    
    # Format prompt manually and call LLM directly to avoid asyncio.create_task context issue
    formatted = prompt_template.format(text=request.text, target_language=request.target_language)
    translation = await llm._acall(formatted)
    
    return {
        "translation": translation,
        "target_language": request.target_language
    }


# ASGI adapter for Cloudflare Workers
async def on_fetch(request, env):
    """
    Main entry point for the Cloudflare Worker.
    
    This function adapts the incoming Cloudflare Worker request to ASGI
    format that FastAPI can understand.
    """
    global _ai_binding
    _ai_binding = env.AI
    
    import json
    from urllib.parse import urlparse
    
    # Parse the request
    url = urlparse(request.url)
    path = url.path
    method = request.method
    
    # Build headers dict
    headers = []
    request_headers = request.headers
    for entry in request_headers.entries():
        headers.append((entry[0].lower().encode(), str(entry[1]).encode()))
    
    # Get request body
    body = b""
    if method in ["POST", "PUT", "PATCH"]:
        try:
            body = (await request.text()).encode()
        except:
            body = b""
    
    # Build ASGI scope
    scope = {
        "type": "http",
        "asgi": {"version": "3.0"},
        "http_version": "1.1",
        "method": method,
        "path": path,
        "query_string": (url.query or "").encode(),
        "headers": headers,
        "server": (url.hostname or "localhost", int(url.port or 443)),
    }
    
    # Response accumulator
    response_started = False
    response_status = 200
    response_headers = {}
    response_body = []
    
    async def receive():
        return {"type": "http.request", "body": body, "more_body": False}
    
    async def send(message):
        nonlocal response_started, response_status, response_headers
        if message["type"] == "http.response.start":
            response_started = True
            response_status = message["status"]
            for key, value in message.get("headers", []):
                response_headers[key.decode()] = value.decode()
        elif message["type"] == "http.response.body":
            body_content = message.get("body", b"")
            if body_content:
                response_body.append(body_content)
    
    # Call FastAPI
    await app(scope, receive, send)
    
    # Build response
    from workers import Response
    
    final_body = b"".join(response_body)
    
    return Response(
        final_body.decode(),
        status=response_status,
        headers=response_headers
    )
