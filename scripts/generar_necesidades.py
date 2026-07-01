"""Genera el Termómetro de Necesidades Emergentes (.docx).

Sigue día a día qué necesidad está creciendo (rescate, agua, salud, albergue…) por su
% de reportes, para anticipar y pre-posicionar recursos. No usa IA.

Uso:
    python scripts/generar_necesidades.py
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.report.reporte_necesidades import generar_reporte  # noqa: E402


def main() -> int:
    print("⏳ Analizando evolución de necesidades día a día…")
    ruta = generar_reporte()
    print(f"✅ Reporte generado: {ruta}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
