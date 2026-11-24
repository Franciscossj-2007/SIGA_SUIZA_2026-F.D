"""Catálogo oficial de programas de estudio (IDs 1..11).

Fuente única para crear, sincronizar y validar programas de estudio.
Los identificadores son fijos: nunca se generan con la secuencia de la BD.
"""

import re
from unicodedata import normalize

PROGRAMAS = (
    {"id": 1, "codigo": "AOT", "nombre": "Administración de Operaciones Turísticas"},
    {"id": 2, "codigo": "ASI-ADM", "nombre": "Asistencia Administrativa"},
    {"id": 3, "codigo": "CON", "nombre": "Contabilidad"},
    {"id": 4, "codigo": "CON-CIV", "nombre": "Construcción Civil"},
    {"id": 5, "codigo": "GAS-ADM", "nombre": "Gestión Administrativa"},
    {"id": 6, "codigo": "DSI", "nombre": "Desarrollo de Sistemas de Información"},
    {"id": 7, "codigo": "ELT", "nombre": "Electricidad Industrial"},
    {"id": 8, "codigo": "ENF", "nombre": "Enfermería Técnica"},
    {"id": 9, "codigo": "MAN-FOR", "nombre": "Manejo Forestal"},
    {"id": 10, "codigo": "MET", "nombre": "Mecatrónica Automotriz"},
    {"id": 11, "codigo": "PRO-AG", "nombre": "Producción Agropecuaria"},
)

_PROGRAMAS_POR_ID = {programa["id"]: programa for programa in PROGRAMAS}


def normalizar_texto(valor):
    texto = normalize("NFD", str(valor if valor is not None else ""))
    texto = "".join(caracter for caracter in texto if not 0x0300 <= ord(caracter) <= 0x036F)
    return re.sub(r"\s+", " ", texto).strip().lower()


def obtener_programa_oficial(valor):
    """Resuelve un ID, código CNOF o denominación al programa oficial."""
    if valor is None:
        return None
    texto = normalizar_texto(valor)
    if not texto:
        return None
    if texto.isdigit():
        return _PROGRAMAS_POR_ID.get(int(texto))
    return next(
        (
            programa
            for programa in PROGRAMAS
            if texto in (normalizar_texto(programa["nombre"]), normalizar_texto(programa["codigo"]))
        ),
        None,
    )


def resolver_programa_id(valor):
    programa = obtener_programa_oficial(valor)
    return programa["id"] if programa else None


def es_programa_valido(programa_id):
    try:
        return int(programa_id) in _PROGRAMAS_POR_ID
    except (TypeError, ValueError):
        return False
