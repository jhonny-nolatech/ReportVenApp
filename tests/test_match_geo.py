"""Pruebas del emparejamiento geográfico MMI ↔ VenApp.

Funcionan offline (sin VPN/BD): las localidades de alta intensidad casan por el
mapa curado, con confianza no 'baja'.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.db.intensidad_mmi import cargar_mmi  # noqa: E402
from app.db.match_geo import emparejar_localidad  # noqa: E402


def test_mmi_altas_casan_con_estado_valido():
    locs = [l for l in cargar_mmi(solo_venezuela=True) if l.mmi >= 6.0]
    assert locs, "Debe haber localidades con MMI >= 6.0"
    fallos = []
    for l in locs:
        m = emparejar_localidad(l.localidad)
        if m.granularidad == "sin_match" or not m.estado or m.confianza == "baja":
            fallos.append((l.localidad, m.granularidad, m.confianza))
    assert not fallos, f"Localidades MMI>=6 sin match fiable: {fallos}"


def test_caraballeda_mapea_la_guaira():
    m = emparejar_localidad("Caraballeda")
    assert m.estado == "La Guaira"
    assert m.confianza == "alta"


if __name__ == "__main__":
    test_mmi_altas_casan_con_estado_valido()
    test_caraballeda_mapea_la_guaira()
    print("test_match_geo: OK")
