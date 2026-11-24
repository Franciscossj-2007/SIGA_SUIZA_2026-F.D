"""Validaciones reutilizables para los esquemas de entrada de los microservicios."""

from typing import Annotated

from pydantic import StringConstraints


TextoRequerido = Annotated[
    str, StringConstraints(strip_whitespace=True, min_length=1, max_length=200)
]

CodigoRequerido = Annotated[
    str, StringConstraints(strip_whitespace=True, min_length=1, max_length=50)
]

DniPeruano = Annotated[
    str, StringConstraints(strip_whitespace=True, pattern=r"^\d{8}$")
]

ContrasenaSegura = Annotated[
    str, StringConstraints(min_length=8, max_length=128)
]
