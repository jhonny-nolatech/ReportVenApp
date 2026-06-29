"""Cliente de la API pública de TerremotoVenezuela.com (edificios afectados).

Fuente ciudadana curada (NO oficial) que aporta foto, coordenadas y estado de
verificación de colapsos emblemáticos. Complementa el inventario; no lo reemplaza.
La API devuelve un máximo fijo de ~50 registros (ver docs/terremotovenezuela_api.md).
"""
from __future__ import annotations
import requests

BASE = "https://api.terremotovenezuela.com/api/v1"


def obtener_edificios(timeout: int = 20) -> list[dict]:
    """Devuelve la lista de edificios afectados (máx. ~50). [] si falla la red."""
    try:
        r = requests.get(f"{BASE}/edificios", timeout=timeout)
        r.raise_for_status()
        data = r.json()
        return data if isinstance(data, list) else []
    except Exception:
        return []


def edificios_verificados(solo_con_evidencia: bool = True) -> list[dict]:
    """Filtra a edificios verificados o con foto/atrapados (mayor confianza)."""
    out = []
    for b in obtener_edificios():
        if not solo_con_evidencia or b.get("status") == "verificado" \
                or b.get("media_urls") or b.get("trapped_names"):
            out.append(b)
    return out


def tabla_edificios_md(limite: int = 25) -> str:
    """Tabla markdown compacta de edificios con evidencia (para el contexto)."""
    bs = edificios_verificados()[:limite]
    if not bs:
        return "_(TerremotoVenezuela no disponible o sin datos en este momento.)_"
    out = ["| Edificio | Ciudad/Zona | Daño | Estado | Coordenadas | Evidencia |",
           "|---|---|---|---|---|---|"]
    for b in bs:
        coord = (f"{b['lat']:.4f}, {b['lng']:.4f}" if b.get("lat") and b.get("lng") else "—")
        ev = []
        if b.get("media_urls"):
            ev.append("foto")
        if b.get("trapped_names"):
            ev.append("atrapados")
        zona = (b.get("city") or "—") + (f" / {b['zone']}" if b.get("zone") else "")
        out.append(f"| {b.get('name','—')} | {zona} | {b.get('damage_level','—')} | "
                   f"{b.get('status','—')} | {coord} | {', '.join(ev) or '—'} |")
    return "\n".join(out)
