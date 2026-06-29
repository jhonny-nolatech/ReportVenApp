"""Prueba de humo: conexión y conteo del evento Terremoto 24J."""
import sys
from pathlib import Path

# Permite ejecutar `python scripts/smoke_db.py` desde la raíz del proyecto.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.db.mongo import ping, get_reports_collection, build_event_query  # noqa: E402

print("ping:", ping())
col = get_reports_collection()
print("Reportes Terremoto 24J:", col.count_documents(build_event_query()))
