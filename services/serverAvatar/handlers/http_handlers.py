"""
HTTP Handlers
=============
Handlers para servir páginas HTML estáticas.
"""

from aiohttp import web


async def index(request):
    """Servir página principal (LiveKit)"""
    with open("static_hybrid/index_livekit.html", "r") as f:
        html = f.read()
    return web.Response(text=html, content_type="text/html")


async def index_public(request):
    """Servir página pública (auto-detecta localhost/ngrok)"""
    with open("static_hybrid/index_public.html", "r") as f:
        html = f.read()
    return web.Response(text=html, content_type="text/html")
