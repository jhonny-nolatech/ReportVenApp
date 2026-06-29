"""Configuración central del Copiloto Estratégico de Crisis — Terremoto 24J.

Carga el `.env`, expone `Settings` con todas las variables, las constantes del
evento (que no cambian y por eso no van en `.env`) y una función `validate()`
que falla con mensaje claro si falta algo crítico.
"""
from __future__ import annotations

import datetime as dt
import os
from dataclasses import dataclass, field

from dotenv import load_dotenv

# Carga el .env una sola vez al importar el módulo.
load_dotenv()


def _get(*names: str, default: str | None = None) -> str | None:
    """Devuelve la primera variable de entorno encontrada (tolerante a alias)."""
    for n in names:
        v = os.environ.get(n)
        if v is not None and v.strip() != "":
            return v.strip()
    return default


# --------------------------------------------------------------------------- #
# Constantes del evento (no cambian → no van en .env)
# --------------------------------------------------------------------------- #
EVENT_CATEGORY = "Terremoto 24J"
EVENT_START = dt.datetime(2026, 6, 24, 0, 0, 0)  # UTC, naive
EVENT_NAME = "Terremoto 24J — Venezuela"
# Bounding box aproximado de Venezuela para validar coordenadas (lat, lng).
VEN_BBOX = {"lat_min": 0.6, "lat_max": 12.3, "lng_min": -73.4, "lng_max": -59.7}
# Estados de gestión posibles del campo `status`.
STATUS_VALUES = [
    "Generado", "Recibido", "Asignado", "En Proceso", "Atendido", "Devuelto", "Rechazado",
]


@dataclass
class Settings:
    """Configuración resuelta desde el entorno (.env)."""

    anthropic_api_key: str = field(default_factory=lambda: _get("ANTHROPIC_API_KEY", default="") or "")
    anthropic_model: str = field(default_factory=lambda: _get("ANTHROPIC_MODEL", default="claude-sonnet-4-6") or "claude-sonnet-4-6")
    anthropic_model_synthesis: str = field(default_factory=lambda: _get("ANTHROPIC_MODEL_SYNTHESIS", default="claude-opus-4-8") or "claude-opus-4-8")
    serper_api_key: str = field(default_factory=lambda: _get("SERPER_API_KEY", default="") or "")
    prod_db_url: str = field(default_factory=lambda: _get("PRODdbURL", "PROD_DB_URL", default="") or "")
    mongo_ca_file: str = field(default_factory=lambda: _get("mongoSslCAFile", "MONGO_SSL_CA_FILE", default="mongo_ssl_vevaprd_rs03_app/CA.pem") or "")
    mongo_pem_file: str = field(default_factory=lambda: _get("mongoSslPEMKeyFile", "MONGO_SSL_PEM_FILE", default="mongo_ssl_vevaprd_rs03_app/mclient.pem") or "")
    reports_out_dir: str = field(default_factory=lambda: _get("REPORTS_OUT_DIR", default="reports_out") or "reports_out")
    app_timezone: str = field(default_factory=lambda: _get("APP_TIMEZONE", default="America/Caracas") or "America/Caracas")

    def __post_init__(self) -> None:
        # Aseguramos el directorio de salida de informes.
        os.makedirs(self.reports_out_dir, exist_ok=True)

    def validate(self) -> "Settings":
        """Falla con mensaje claro si falta configuración crítica."""
        faltan: list[str] = []
        if not self.anthropic_api_key:
            faltan.append("ANTHROPIC_API_KEY")
        if not self.prod_db_url:
            faltan.append("PRODdbURL")
        if faltan:
            raise RuntimeError(
                "Faltan variables de entorno obligatorias: " + ", ".join(faltan)
                + ". Copia .env.example a .env y rellénalas."
            )
        for label, path in (("mongoSslCAFile", self.mongo_ca_file),
                             ("mongoSslPEMKeyFile", self.mongo_pem_file)):
            if not path or not os.path.exists(path):
                raise RuntimeError(
                    f"Certificado TLS no encontrado para {label}: '{path}'. "
                    "Coloca CA.pem y mclient.pem en mongo_ssl_vevaprd_rs03_app/."
                )
        return self


def validate() -> Settings:
    """Atajo: valida y devuelve un Settings listo para usar."""
    return Settings().validate()
