"""Prueba end-to-end sin frontend: genera un informe real y lo renderiza a Word."""
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.agent.orchestrator import generar_informe_dict  # noqa: E402
from app.report.docx_renderer import render_informe  # noqa: E402

inf = generar_informe_dict("resumen_ejecutivo", modelo="claude-sonnet-4-6")
print("Resumen:", inf["resumen_ejecutivo"][:200])
print("Recomendaciones:", len(inf.get("recomendaciones", [])))
path = render_informe(inf, "reports_out/test_e2e.docx")
print("DOCX:", path, "existe:", os.path.exists(path))
