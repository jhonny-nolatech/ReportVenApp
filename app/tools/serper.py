"""Herramienta de búsqueda web vía Serper (Google).

Permite al agente traer protocolos vigentes, noticias del sismo y lecciones de
terremotos análogos. Nunca rompe el loop del agente: ante cualquier error
devuelve un dict con `error`. Solo devuelve título/url/snippet/fecha (el agente
parafrasea y cita la url; respeto a derechos de autor).
"""
from __future__ import annotations

import requests

from app.config import Settings

SERPER_URL = "https://google.serper.dev/search"
SERPER_NEWS_URL = "https://google.serper.dev/news"
_MAX_NUM = 10


def _post(url: str, query: str, num: int, gl: str, hl: str) -> dict:
    s = Settings()
    num = max(1, min(num, _MAX_NUM))
    payload = {"q": query, "num": num, "gl": gl, "hl": hl}
    headers = {"X-API-KEY": s.serper_api_key, "Content-Type": "application/json"}
    r = requests.post(url, json=payload, headers=headers, timeout=20)
    r.raise_for_status()
    return r.json()


def buscar_web(query: str, num: int = 6, gl: str = "ve", hl: str = "es") -> dict:
    """Busca en Google vía Serper. Devuelve resultados limpios y compactos.

    gl=país (ve=Venezuela), hl=idioma (es). Sube `num` solo si hace falta
    (máximo 10 para no inflar el contexto del agente).
    """
    try:
        data = _post(SERPER_URL, query, num, gl, hl)
    except Exception as e:  # noqa: BLE001 — nunca romper el loop del agente
        return {"query": query, "error": str(e), "resultados": []}

    organicos = []
    for it in (data.get("organic") or [])[:num]:
        organicos.append({
            "titulo": it.get("title"),
            "url": it.get("link"),
            "snippet": it.get("snippet"),
            "fecha": it.get("date"),
        })
    return {
        "query": query,
        "answer_box": (data.get("answerBox") or {}).get("answer"),
        "knowledge_graph": (data.get("knowledgeGraph") or {}).get("description"),
        "resultados": organicos,
    }


def buscar_noticias(query: str, num: int = 6, gl: str = "ve", hl: str = "es") -> dict:
    """Variante para noticias recientes (endpoint /news de Serper)."""
    try:
        data = _post(SERPER_NEWS_URL, query, num, gl, hl)
    except Exception as e:  # noqa: BLE001
        return {"query": query, "error": str(e), "resultados": []}

    noticias = []
    for it in (data.get("news") or [])[:num]:
        noticias.append({
            "titulo": it.get("title"),
            "url": it.get("link"),
            "snippet": it.get("snippet"),
            "fecha": it.get("date"),
            "fuente": it.get("source"),
        })
    return {"query": query, "resultados": noticias}
