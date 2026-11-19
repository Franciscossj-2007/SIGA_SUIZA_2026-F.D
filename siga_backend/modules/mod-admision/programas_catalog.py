"""Catálogo oficial de programas de estudio (IDS 1..11).

Fuente única para la ingesta de admisión y la validación de estudiantes.
Los nombres y códigos corresponden al catálogo institucional/MINEDU.
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


def resolver_programa_id(valor):
    """Resuelve un ID, código CNOF o denominación a un programa_id oficial."""
    if valor is None:
        return None
    texto = normalizar_texto(valor)
    if not texto:
        return None
    if texto.isdigit():
        candidato = int(texto)
        return candidato if candidato in _PROGRAMAS_POR_ID else None
    for programa in PROGRAMAS:
        if texto in (normalizar_texto(programa["nombre"]), normalizar_texto(programa["codigo"])):
            return programa["id"]
    return None


def es_programa_valido(programa_id):
    try:
        return int(programa_id) in _PROGRAMAS_POR_ID
    except (TypeError, ValueError):
        return False
