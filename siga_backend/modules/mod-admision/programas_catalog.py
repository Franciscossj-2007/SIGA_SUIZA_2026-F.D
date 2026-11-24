"""Compatibilidad: el catálogo oficial vive en `shared.programas_catalog`."""

from shared.programas_catalog import (
    PROGRAMAS,
    es_programa_valido,
    normalizar_texto,
    obtener_programa_oficial,
    resolver_programa_id,
)

__all__ = [
    "PROGRAMAS",
    "es_programa_valido",
    "normalizar_texto",
    "obtener_programa_oficial",
    "resolver_programa_id",
]
