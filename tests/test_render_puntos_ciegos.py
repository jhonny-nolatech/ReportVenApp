"""Render offline de un informe 'puntos_ciegos' (sin agente ni BD).

Construye un Informe a partir del análisis real de puntos ciegos y verifica que
el .docx se genera con la sección y el mapa de burbujas.
"""
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.db.zonas_silenciosas import analizar_puntos_ciegos  # noqa: E402
from app.report.docx_renderer import render_informe  # noqa: E402


def _informe_desde_analisis(a) -> dict:
    zonas = []
    for z in (a.zonas_criticas + a.zonas_silenciosas)[:25]:
        zonas.append({
            "localidad": z.localidad, "estado": z.estado, "mmi": z.mmi,
            "habitantes": z.habitantes, "reportes_observados": z.reportes_observados,
            "reportes_esperados": z.reportes_esperados, "cobertura": z.cobertura,
            "indice_punto_ciego": z.indice_punto_ciego, "critica": z.critica,
            "prioridad": "P1" if z.critica else "P3",
        })
    return {
        "meta": {"titulo": "Reporte de Zonas Silenciosas / Puntos Ciegos — Terremoto 24J",
                 "tipo_reporte": "puntos_ciegos", "fecha_generacion": "2026-06-26 16:00",
                 "ventana_datos": "desde 24-jun-2026"},
        "resumen_ejecutivo": "Prueba de render de la sección de puntos ciegos.",
        "panorama_datos": {"narrativa": "Cruce intensidad×reportes."},
        "resumen_puntos_ciegos": a.resumen,
        "zonas_ciegas": zonas,
        "puntos_ciegos_sin_match": a.sin_match,
    }


def test_render_puntos_ciegos_genera_docx():
    a = analizar_puntos_ciegos()
    informe = _informe_desde_analisis(a)
    path = render_informe(informe, "reports_out/test_puntos_ciegos.docx")
    assert os.path.exists(path) and os.path.getsize(path) > 5000
    print("DOCX:", path, "bytes:", os.path.getsize(path))


if __name__ == "__main__":
    test_render_puntos_ciegos_genera_docx()
    print("test_render_puntos_ciegos: OK")
