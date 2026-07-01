"""Mapa operacional interactivo (HTML/Leaflet) por parroquia — Terremoto 24J.

Genera un ARCHIVO HTML AUTÓNOMO (se abre en el navegador, sin servidor) con un
marcador por parroquia coloreado por severidad y un POPUP al hacer clic con toda la
info clave: reportes totales, personas a reubicar, edificios derrumbados / en riesgo,
viviendas, desaparecidos y necesidades de servicios (electricidad/agua/gas).

Datos AGREGADOS por parroquia (sin PII: no se muestran nombres/cédulas). Usa la
clasificación por IA (edificio derrumbado vs. en riesgo) ya cacheada.
"""
from __future__ import annotations

import json
import os
import re

from app.config import Settings
from app.db.mongo import build_event_query, get_reports_collection
from app.tools import clasificador_edificios as ce
from app.tools import logistica_albergues as la

_RE_DESAP = re.compile(r"desaparec|no aparece|no localiza|paradero", re.I)
_RE_ELEC = re.compile(r"electric|luz|corriente|apag[oó]n|poste|cable|transformador|sin luz", re.I)
_RE_AGUA = re.compile(r"\bagua|tuber[ií]a|acueducto|cloaca|aguas (blancas|negras|servidas)", re.I)
_RE_GAS = re.compile(r"\bgas\b|bombona|fuga de gas", re.I)


def _reportes_enriquecidos() -> list[dict]:
    col = get_reports_collection()
    cache = ce._cargar_cache()
    out = []
    for d in col.find(build_event_query()):
        num = d.get("number")
        c = cache.get(num, {})
        prov = (d.get("province") or {}).get("name") if isinstance(d.get("province"), dict) else None
        mun = (d.get("municipality") or {}).get("name") if isinstance(d.get("municipality"), dict) else None
        par = (d.get("parroquia") or {}).get("name") if isinstance(d.get("parroquia"), dict) else None
        out.append({
            "num": num, "estado": prov, "municipio": mun, "parroquia": par,
            "lat": d.get("latitude"), "lng": d.get("longitude"),
            "texto": f"{d.get('title') or ''} {d.get('description') or ''}",
            "addr": d.get("address") or "",
            "tipo": c.get("tipo"), "vertical": bool(c.get("vertical")),
        })
    return out


def datos_por_parroquia() -> list[dict]:
    """Agrega métricas por parroquia (centroide + conteos + personas a reubicar)."""
    reg = _reportes_enriquecidos()
    grupos: dict[tuple, dict] = {}
    for r in reg:
        key = (r["estado"] or "—", r["municipio"] or "—", r["parroquia"] or "Sin parroquia")
        g = grupos.setdefault(key, {"reg": [], "lat": [], "lng": []})
        g["reg"].append(r)
        if r["lat"] and r["lng"]:
            g["lat"].append(float(r["lat"]))
            g["lng"].append(float(r["lng"]))

    f_edif = la.APTOS_CENTRAL * la.PERSONAS_HOGAR_VERTICAL  # personas por edificio (central)
    f_viv = la.PERSONAS_HOGAR_VERTICAL                       # personas por vivienda
    filas = []
    for (est, mun, par), g in grupos.items():
        if not g["lat"]:
            continue  # sin coordenadas no se puede ubicar en el mapa
        regs = g["reg"]
        clat = sum(g["lat"]) / len(g["lat"])
        clng = sum(g["lng"]) / len(g["lng"])

        def _dedup(pred) -> int:
            seen, n = set(), 0
            for r in regs:
                if not pred(r):
                    continue
                ident = ce._edificio_id(r["addr"]) if r["vertical"] else None
                if ident:
                    k = ("n", ident)
                elif r["lat"] and r["lng"]:
                    k = ("g", round(float(r["lat"]), 4), round(float(r["lng"]), 4))
                else:
                    k = ("u", r["num"])
                if k in seen:
                    continue
                seen.add(k)
                n += 1
            return n

        edif_d = _dedup(lambda r: r["vertical"] and r["tipo"] == "derrumbado")
        edif_r = _dedup(lambda r: r["vertical"] and r["tipo"] == "riesgo")
        viv_d = sum(1 for r in regs if not r["vertical"] and r["tipo"] == "derrumbado")
        viv_r = sum(1 for r in regs if not r["vertical"] and r["tipo"] == "riesgo")
        desap = sum(1 for r in regs if _RE_DESAP.search(r["texto"]))
        elec = sum(1 for r in regs if _RE_ELEC.search(r["texto"]))
        agua = sum(1 for r in regs if _RE_AGUA.search(r["texto"]))
        gas = sum(1 for r in regs if _RE_GAS.search(r["texto"]))
        reubicar = edif_d * f_edif + viv_d * f_viv
        filas.append({
            "estado": est, "municipio": mun, "parroquia": par,
            "lat": round(clat, 5), "lng": round(clng, 5),
            "total": len(regs), "edif_d": edif_d, "edif_r": edif_r,
            "viv_d": viv_d, "viv_r": viv_r, "reubicar": reubicar,
            "desap": desap, "elec": elec, "agua": agua, "gas": gas,
        })
    filas.sort(key=lambda x: x["reubicar"], reverse=True)
    return filas


# --------------------------------------------------------------------------- #
# Generación del HTML (Leaflet, autónomo)
# --------------------------------------------------------------------------- #
_HTML = """<!DOCTYPE html>
<html lang="es"><head>
<meta charset="utf-8"/><meta name="viewport" content="width=device-width, initial-scale=1"/>
<title>Mapa Operacional — Terremoto 24J</title>
<link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css"/>
<script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
<style>
  html,body{margin:0;height:100%;font-family:Segoe UI,Roboto,Arial,sans-serif}
  #map{position:absolute;top:64px;bottom:0;left:0;right:0}
  #bar{position:absolute;top:0;left:0;right:0;height:64px;background:#0B3C5D;color:#fff;
       display:flex;align-items:center;padding:0 18px;z-index:1000;box-shadow:0 2px 6px rgba(0,0,0,.3)}
  #bar h1{font-size:18px;margin:0}#bar small{opacity:.8;margin-left:12px;font-size:12px}
  .leaflet-popup-content{font-size:13px;line-height:1.5;min-width:240px}
  .pp h3{margin:0 0 6px;color:#0B3C5D;font-size:15px}
  .pp .sub{color:#777;font-size:11px;margin-bottom:8px}
  .pp table{width:100%;border-collapse:collapse}
  .pp td{padding:2px 4px;border-bottom:1px solid #eee}
  .pp td.k{color:#555}.pp td.v{text-align:right;font-weight:bold}
  .pp .big{color:#C0392B;font-size:15px}
  .legend{background:#fff;padding:10px 12px;border-radius:6px;box-shadow:0 1px 5px rgba(0,0,0,.3);font-size:12px;line-height:1.7}
  .legend i{display:inline-block;width:12px;height:12px;border-radius:50%;margin-right:6px;opacity:.85}
</style></head><body>
<div id="bar"><h1>Mapa Operacional — Terremoto 24J</h1>
  <small>__CORTE__ · __N__ parroquias · marcador = parroquia · color = personas a reubicar · tamaño = nº de reportes</small></div>
<div id="map"></div>
<script>
const DATA = __DATA__;
const map = L.map('map').setView([10.3, -67.0], 8);
L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png',
  {maxZoom:19, attribution:'© OpenStreetMap'}).addTo(map);

function color(v){ return v>=2000?'#7b241c': v>=500?'#C0392B': v>=100?'#E67E22': v>=1?'#F1C40F':'#95A5A6'; }
function radius(t){ return Math.min(28, 5 + Math.sqrt(t)*1.3); }
function fmt(n){ return (n||0).toLocaleString('es-VE'); }

const bounds = [];
DATA.forEach(p => {
  bounds.push([p.lat, p.lng]);
  const needs = [];
  if(p.elec) needs.push('Electricidad: '+fmt(p.elec));
  if(p.agua) needs.push('Agua: '+fmt(p.agua));
  if(p.gas)  needs.push('Gas: '+fmt(p.gas));
  const html = `<div class="pp"><h3>${p.parroquia}</h3>
    <div class="sub">${p.municipio} · ${p.estado}</div>
    <table>
      <tr><td class="k">Personas a reubicar</td><td class="v big">${fmt(p.reubicar)}</td></tr>
      <tr><td class="k">Reportes totales</td><td class="v">${fmt(p.total)}</td></tr>
      <tr><td class="k">Edificios derrumbados</td><td class="v">${fmt(p.edif_d)}</td></tr>
      <tr><td class="k">Edificios en riesgo</td><td class="v">${fmt(p.edif_r)}</td></tr>
      <tr><td class="k">Viviendas derrumbadas</td><td class="v">${fmt(p.viv_d)}</td></tr>
      <tr><td class="k">Reportes de desaparecidos</td><td class="v">${fmt(p.desap)}</td></tr>
    </table>
    ${needs.length? '<div style="margin-top:6px;color:#555">Servicios afectados — '+needs.join(' · ')+'</div>':''}
    </div>`;
  L.circleMarker([p.lat, p.lng], {radius: radius(p.total), color:'#fff', weight:1,
      fillColor: color(p.reubicar), fillOpacity:.82})
    .bindPopup(html)
    .bindTooltip(p.parroquia+' ('+fmt(p.reubicar)+' a reubicar)')
    .addTo(map);
});
if(bounds.length) map.fitBounds(bounds, {padding:[30,30]});

const lg = L.control({position:'bottomright'});
lg.onAdd = function(){ const d=L.DomUtil.create('div','legend');
  d.innerHTML = '<b>Personas a reubicar</b><br>'+
    '<i style="background:#7b241c"></i>2.000+<br>'+
    '<i style="background:#C0392B"></i>500–2.000<br>'+
    '<i style="background:#E67E22"></i>100–500<br>'+
    '<i style="background:#F1C40F"></i>1–100<br>'+
    '<i style="background:#95A5A6"></i>sin derrumbes'; return d; };
lg.addTo(map);
</script></body></html>
"""


def generar_mapa_html(out_path: str | None = None) -> str:
    """Genera el mapa operacional interactivo. Devuelve la ruta del HTML."""
    filas = datos_por_parroquia()
    out_path = out_path or os.path.join(Settings().reports_out_dir, "mapa_operacional.html")
    os.makedirs(os.path.dirname(out_path) or ".", exist_ok=True)
    try:
        import datetime as dt
        from zoneinfo import ZoneInfo
        corte = dt.datetime.now(ZoneInfo("America/Caracas")).strftime("Corte %d/%m/%Y %H:%M")
    except Exception:  # noqa: BLE001
        corte = "Corte del análisis"
    html = (_HTML.replace("__DATA__", json.dumps(filas, ensure_ascii=False))
                 .replace("__CORTE__", corte)
                 .replace("__N__", str(len(filas))))
    with open(out_path, "w", encoding="utf-8") as fh:
        fh.write(html)
    return out_path
