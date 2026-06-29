"""Backend FastAPI: orquesta todo y sirve el frontend.

La API solo orquesta; la lógica vive en las capas previas. Nunca devuelve la
cadena de conexión, claves ni PII en errores.
"""
from __future__ import annotations

import json
import os
import re
import time

from fastapi import FastAPI, HTTPException
from fastapi.concurrency import run_in_threadpool
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from app.agent.orchestrator import generar_informe_dict
from app.config import Settings
from app.db import data_service
from app.db.mongo import ping
from app.report.docx_renderer import render_informe

app = FastAPI(title="Copiloto Estratégico — Terremoto 24J")

# CORS: solo localhost en desarrollo.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:8000", "http://127.0.0.1:8000"],
    allow_methods=["*"],
    allow_headers=["*"],
)

_STATIC_DIR = os.path.join(os.path.dirname(__file__), "static")
os.makedirs(_STATIC_DIR, exist_ok=True)
app.mount("/static", StaticFiles(directory=_STATIC_DIR), name="static")

_REPORT_ID_RE = re.compile(r"^[A-Za-z0-9_]+$")

# Cache simple de estados (evita golpear la BD en cada carga del frontend).
_estados_cache: dict = {"data": None, "ts": 0.0}
_ESTADOS_TTL = 300  # segundos


class ReporteRequest(BaseModel):
    tipo: str
    estado: str | None = None
    instruccion_adicional: str | None = ""
    modelo: str | None = None


def _settings() -> Settings:
    return Settings()


@app.get("/api/health")
async def health():
    try:
        pong = await run_in_threadpool(ping)
        return {"ok": True, "db": pong, "evento": "Terremoto 24J"}
    except Exception as e:  # noqa: BLE001 — no filtrar credenciales
        return {"ok": False, "db": None, "evento": "Terremoto 24J", "error": _safe_err(e)}


@app.get("/api/tipos-reporte")
async def tipos_reporte():
    from app.agent.schema import TIPOS_REPORTE
    now = time.time()
    if _estados_cache["data"] is None or now - _estados_cache["ts"] > _ESTADOS_TTL:
        try:
            estados = await run_in_threadpool(data_service.listar_estados)
        except Exception:  # noqa: BLE001 — el frontend funciona aun sin estados
            estados = []
        _estados_cache["data"] = estados
        _estados_cache["ts"] = now
    return {"tipos": TIPOS_REPORTE, "estados": _estados_cache["data"]}


@app.post("/api/reportes")
async def crear_reporte(req: ReporteRequest):
    s = _settings()
    try:
        informe = await run_in_threadpool(
            generar_informe_dict,
            req.tipo,
            req.estado,
            req.instruccion_adicional or "",
            req.modelo,
        )
    except Exception as e:  # noqa: BLE001
        raise HTTPException(status_code=502, detail=f"Error generando el informe: {_safe_err(e)}")

    tipo = (req.tipo or "informe").replace(" ", "_")
    stamp = time.strftime("%Y%m%d_%H%M")
    report_id = f"informe_{tipo}_{stamp}"
    if not _REPORT_ID_RE.match(report_id):
        report_id = re.sub(r"[^A-Za-z0-9_]", "_", report_id)

    out_docx = os.path.join(s.reports_out_dir, f"{report_id}.docx")
    out_json = os.path.join(s.reports_out_dir, f"{report_id}.json")
    try:
        await run_in_threadpool(render_informe, informe, out_docx)
        with open(out_json, "w", encoding="utf-8") as fh:
            json.dump(informe, fh, ensure_ascii=False, indent=2)
    except Exception as e:  # noqa: BLE001
        raise HTTPException(status_code=500, detail=f"Error al renderizar/guardar: {_safe_err(e)}")

    panorama = informe.get("panorama_datos") or {}
    return {
        "report_id": report_id,
        "resumen_ejecutivo": informe.get("resumen_ejecutivo", ""),
        "kpis": panorama.get("kpis", []),
        "n_recomendaciones": len(informe.get("recomendaciones", [])),
        "n_riesgos": len(informe.get("analisis_riesgos", [])),
        "download_url": f"/api/reportes/{report_id}/docx",
    }


@app.get("/api/reportes/{report_id}/docx")
async def descargar_reporte(report_id: str):
    if not _REPORT_ID_RE.match(report_id):
        raise HTTPException(status_code=400, detail="report_id inválido")
    s = _settings()
    path = os.path.join(s.reports_out_dir, f"{report_id}.docx")
    if not os.path.exists(path):
        raise HTTPException(status_code=404, detail="Informe no encontrado")
    return FileResponse(
        path,
        media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        filename=f"{report_id}.docx",
    )


@app.get("/", response_class=HTMLResponse)
async def index():
    index_path = os.path.join(_STATIC_DIR, "index.html")
    if os.path.exists(index_path):
        with open(index_path, encoding="utf-8") as fh:
            return HTMLResponse(fh.read())
    return HTMLResponse("<h1>Copiloto Estratégico — Terremoto 24J</h1><p>Frontend no encontrado.</p>")


def _safe_err(e: Exception) -> str:
    """Mensaje de error sin credenciales ni cadenas de conexión."""
    msg = str(e)
    msg = re.sub(r"mongodb(\+srv)?://[^\s'\"]+", "mongodb://[REDACTADO]", msg)
    msg = re.sub(r"sk-ant-[A-Za-z0-9_\-]+", "[REDACTADO]", msg)
    return msg[:500]
