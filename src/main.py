"""
Cloudflare Python Worker with Workers AI.
"""

from workers import WorkerEntrypoint, Response
import json
from urllib.parse import urlparse
from pyodide.ffi import to_js as _to_js
import js


def to_js(obj):
    """Convert Python dict to JavaScript Object."""
    return _to_js(obj, dict_converter=js.Object.fromEntries)


class Default(WorkerEntrypoint):
    async def fetch(self, request):
        url = urlparse(request.url)
        path = url.path
        method = request.method
        
        # Route requests
        if path == "/" and method == "GET":
            return self.json_response({
                "status": "ok",
                "service": "Python Workers AI API",
                "endpoints": ["POST /chat", "POST /summarize", "POST /translate"]
            })
        
        if path == "/chat" and method == "POST":
            return await self.handle_chat(request)
        
        if path == "/summarize" and method == "POST":
            return await self.handle_summarize(request)
        
        if path == "/translate" and method == "POST":
            return await self.handle_translate(request)
        
        return self.json_response({"error": "Not found"}, status=404)
    
    async def handle_chat(self, request):
        body = json.loads(await request.text())
        message = body.get("message", "")
        model = body.get("model", "@cf/meta/llama-3.1-8b-instruct")
        
        prompt = f"You are a helpful AI assistant. Be concise.\n\nUser: {message}\n\nAssistant:"
        response = await self.call_ai(prompt, model)
        
        return self.json_response({"response": response, "model": model})
    
    async def handle_summarize(self, request):
        body = json.loads(await request.text())
        text = body.get("text", "")
        max_length = body.get("max_length", 100)
        
        prompt = f"Summarize in {max_length} words or fewer:\n\n{text}\n\nSummary:"
        summary = await self.call_ai(prompt)
        
        return self.json_response({
            "summary": summary,
            "original_length": len(text.split())
        })
    
    async def handle_translate(self, request):
        body = json.loads(await request.text())
        text = body.get("text", "")
        target = body.get("target_language", "Spanish")
        
        prompt = f"Translate to {target}. Output only the translation:\n\n{text}"
        translation = await self.call_ai(prompt)
        
        return self.json_response({
            "translation": translation,
            "target_language": target
        })
    
    async def call_ai(self, prompt: str, model: str = "@cf/meta/llama-3.1-8b-instruct") -> str:
        response = await self.env.AI.run(model, to_js({"prompt": prompt}))
        return response.response
    
    def json_response(self, data, status=200):
        return Response(
            json.dumps(data),
            status=status,
            headers={"Content-Type": "application/json"}
        )
