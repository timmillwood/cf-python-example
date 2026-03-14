"""
Cloudflare Python Worker with Workers AI.
"""

from workers import Response
import json
from urllib.parse import urlparse
from pyodide.ffi import to_js as _to_js
import js


def to_js(obj):
    """Convert Python dict to JavaScript Object."""
    return _to_js(obj, dict_converter=js.Object.fromEntries)


def json_response(data, status=200):
    return Response(
        json.dumps(data),
        status=status,
        headers={"Content-Type": "application/json"}
    )


async def call_ai(env, prompt: str, model: str = "@cf/meta/llama-3.1-8b-instruct") -> str:
    response = await env.AI.run(model, to_js({"prompt": prompt}))
    return response.response


async def on_fetch(request, env):
    url = urlparse(request.url)
    path = url.path
    method = request.method
    
    # Route requests
    if path == "/" and method == "GET":
        return json_response({
            "status": "ok",
            "service": "Python Workers AI API",
            "endpoints": ["POST /chat", "POST /summarize", "POST /translate"]
        })
    
    if path == "/chat" and method == "POST":
        body = json.loads(await request.text())
        message = body.get("message", "")
        model = body.get("model", "@cf/meta/llama-3.1-8b-instruct")
        
        prompt = f"You are a helpful AI assistant. Be concise.\n\nUser: {message}\n\nAssistant:"
        response = await call_ai(env, prompt, model)
        
        return json_response({"response": response, "model": model})
    
    if path == "/summarize" and method == "POST":
        body = json.loads(await request.text())
        text = body.get("text", "")
        max_length = body.get("max_length", 100)
        
        prompt = f"Summarize in {max_length} words or fewer:\n\n{text}\n\nSummary:"
        summary = await call_ai(env, prompt)
        
        return json_response({
            "summary": summary,
            "original_length": len(text.split())
        })
    
    if path == "/translate" and method == "POST":
        body = json.loads(await request.text())
        text = body.get("text", "")
        target = body.get("target_language", "Spanish")
        
        prompt = f"Translate to {target}. Output only the translation:\n\n{text}"
        translation = await call_ai(env, prompt)
        
        return json_response({
            "translation": translation,
            "target_language": target
        })
    
    return json_response({"error": "Not found"}, status=404)
