# Paso 04 — Herramienta de búsqueda web (Serper)

## Objetivo
Crear `app/tools/serper.py`: una función robusta que consulta la API de Serper (Google) para que el
agente pueda traer protocolos actuales, noticias del sismo, lecciones de terremotos análogos, etc.

## Especificación

### `app/tools/serper.py`
```python
import requests
from app.config import Settings

SERPER_URL = "https://google.serper.dev/search"

def buscar_web(query: str, num: int = 6, gl: str = "ve", hl: str = "es") -> dict:
    """
    Busca en Google vía Serper. Devuelve resultados limpios y compactos para el agente.
    gl=país (ve=Venezuela), hl=idioma (es). Subir num solo si hace falta.
    """
    s = Settings()
    payload = {"q": query, "num": num, "gl": gl, "hl": hl}
    headers = {"X-API-KEY": s.serper_api_key, "Content-Type": "application/json"}
    try:
        r = requests.post(SERPER_URL, json=payload, headers=headers, timeout=20)
        r.raise_for_status()
        data = r.json()
    except Exception as e:
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
```

Requisitos adicionales:
- Timeout y manejo de errores que **nunca** rompa el loop del agente (devolver `error` en el dict).
- Limitar `num` a un máximo razonable (p. ej. 10) para no inflar el contexto.
- **No** reproducir texto extenso de las páginas: devolver solo título, url, snippet y fecha. El
  agente parafraseará y citará la `url`. (Respeto a derechos de autor.)
- Opcional: una variante `buscar_noticias(query)` que use el endpoint `/news` de Serper
  (`https://google.serper.dev/news`) para noticias recientes del sismo.

## Criterios de aceptación
- `python -c "from app.tools.serper import buscar_web; print(buscar_web('protocolo INSARAG búsqueda y rescate urbano', num=3))"`
  devuelve un dict con `resultados` (lista de hasta 3 items con `url`).
- Si la API key es inválida, devuelve `{"error": ...}` sin lanzar excepción.
