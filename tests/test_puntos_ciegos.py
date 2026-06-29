"""Pruebas del motor de puntos ciegos (offline, sin VPN/BD).

Sin BD, el análisis usa exposición (MMI×población) como proxy y marca como
CRÍTICAS las zonas de alta intensidad y mucha población (cobertura 0).
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.db.zonas_silenciosas import analizar_puntos_ciegos  # noqa: E402
from app.agent.tools_def import ejecutar_tool  # noqa: E402


def test_analisis_devuelve_criticas_ordenadas():
    a = analizar_puntos_ciegos()
    assert a.zonas_criticas, "Debe detectar zonas críticas"
    indices = [z.indice_punto_ciego for z in a.zonas_criticas]
    assert indices == sorted(indices, reverse=True), "Críticas ordenadas por índice desc"
    for z in a.zonas_criticas:
        assert z.cobertura < a.parametros["umbral_cobertura"]
        assert z.cobertura >= 0
        assert z.critica is True


def test_localidad_alto_impacto_es_critica():
    a = analizar_puntos_ciegos()
    nombres = {z.localidad for z in a.zonas_criticas}
    # Caraballeda: MMI 6,4 / 48.622 hab → caso del cliente.
    assert "Caraballeda" in nombres or "Catia La Mar" in nombres


def test_tool_consultar_zonas_silenciosas():
    out = ejecutar_tool("consultar_zonas_silenciosas", {})
    assert "zonas_criticas" in out
    assert isinstance(out["zonas_criticas"], list) and out["zonas_criticas"]
    assert "ZONA DE ATENCIÓN" in out["resumen"] or "atención" in out["resumen"].lower()


if __name__ == "__main__":
    test_analisis_devuelve_criticas_ordenadas()
    test_localidad_alto_impacto_es_critica()
    test_tool_consultar_zonas_silenciosas()
    print("test_puntos_ciegos: OK")
