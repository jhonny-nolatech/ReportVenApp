"""Conexión a MongoDB de producción de VenApp — SOLO LECTURA.

Reglas de oro (guía oficial VenApp):
  * Colección de interés: `reports` en `venapp_db` (viene en la URI).
  * Solo el evento: `category == "Terremoto 24J"`.
  * SIEMPRE acotar por fecha: `createdAt >= 2026-06-24` (UTC).
  * Leer del SECUNDARIO (`SECONDARY_PREFERRED`) para no cargar el primario.
  * NUNCA `find()` sin filtro de fecha. NUNCA escribir en producción.

Toda query sobre `reports` DEBE construirse con `build_event_query()`.
"""
from __future__ import annotations

from functools import lru_cache

from pymongo import MongoClient, ReadPreference

from app.config import EVENT_CATEGORY, EVENT_START, Settings

# Métodos de lectura permitidos en la colección proxy.
_READ_METHODS = frozenset({
    "find", "find_one", "count_documents", "aggregate",
    "distinct", "estimated_document_count",
})
# Prefijos de métodos de escritura que quedan bloqueados explícitamente.
_WRITE_PREFIXES = ("insert", "update", "delete", "replace", "drop",
                   "find_one_and", "bulk_write", "rename", "create")


class ReadOnlyCollection:
    """Proxy ligero que solo expone operaciones de lectura sobre la colección.

    Cualquier intento de escritura (`insert*/update*/delete*/replace*/drop`, etc.)
    lanza `RuntimeError`. Es la única colección que devuelve `get_reports_collection`.
    """

    def __init__(self, collection):
        self._col = collection

    def __getattr__(self, name: str):
        if name in _READ_METHODS:
            return getattr(self._col, name)
        if name.startswith(_WRITE_PREFIXES):
            raise RuntimeError(
                "Operación de escritura bloqueada: producción es solo lectura"
            )
        # Atributos inofensivos (name, full_name, database...) se permiten.
        attr = getattr(self._col, name)
        if callable(attr):
            raise RuntimeError(
                "Operación de escritura bloqueada: producción es solo lectura"
            )
        return attr

    @property
    def name(self) -> str:
        return self._col.name


def assert_read_only() -> None:
    """Documenta la garantía de solo-lectura del módulo (no-op defensivo)."""
    # La garantía se materializa en ReadOnlyCollection; esta función existe para
    # que el código que llama pueda dejar constancia explícita de la intención.
    return None


@lru_cache(maxsize=1)
def get_client() -> MongoClient:
    s = Settings().validate()
    client = MongoClient(
        s.prod_db_url,
        tls=True,
        tlsCAFile=s.mongo_ca_file,
        tlsCertificateKeyFile=s.mongo_pem_file,
        serverSelectionTimeoutMS=15000,
        read_preference=ReadPreference.SECONDARY_PREFERRED,
        appname="copiloto-crisis-24j",
    )
    return client


def get_reports_collection():
    """Devuelve la colección `reports` (solo lectura).

    Si la BD de producción NO está accesible (sin red interna / VPN apagada) pero
    hay un export Excel de respaldo disponible, devuelve una colección emulada
    respaldada por ese Excel. Así el sistema genera informes igual, offline.
    """
    if not db_available():
        from app.db.excel_source import excel_available, get_excel_collection
        if excel_available():
            return get_excel_collection()
    client = get_client()
    db = client.get_default_database()  # venapp_db (de la URI)
    return ReadOnlyCollection(db["reports"])


def reports_source_available() -> bool:
    """True si hay ALGUNA fuente de reportes utilizable: BD o Excel de respaldo."""
    if db_available():
        return True
    try:
        from app.db.excel_source import excel_available
        return excel_available()
    except Exception:  # noqa: BLE001
        return False


def ping() -> dict:
    return get_client().admin.command("ping")


@lru_cache(maxsize=1)
def db_available() -> bool:
    """Sondeo único y rápido de disponibilidad de la BD (timeout corto).

    Evita que el análisis de puntos ciegos espere 15 s por cada consulta cuando
    no hay red interna. Cacheado: solo se paga una vez por proceso.
    """
    try:
        s = Settings().validate()
        probe = MongoClient(
            s.prod_db_url,
            tls=True,
            tlsCAFile=s.mongo_ca_file,
            tlsCertificateKeyFile=s.mongo_pem_file,
            serverSelectionTimeoutMS=2500,
            read_preference=ReadPreference.SECONDARY_PREFERRED,
            appname="copiloto-crisis-24j-probe",
        )
        probe.admin.command("ping")
        return True
    except Exception:  # noqa: BLE001
        return False


def build_event_query(province: str | None = None,
                      date_from=None,
                      date_to=None) -> dict:
    """ÚNICA forma autorizada de construir queries sobre `reports`.

    Siempre incluye el filtro base del evento (categoría + fecha mínima). Sin
    pasar por aquí no se debe consultar la colección.
    """
    q: dict = {
        "category": EVENT_CATEGORY,
        "createdAt": {"$gte": date_from or EVENT_START},
    }
    if date_to:
        q["createdAt"]["$lte"] = date_to
    if province:
        q["province.name"] = province
    return q
