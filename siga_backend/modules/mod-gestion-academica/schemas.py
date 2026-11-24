from pydantic import BaseModel, EmailStr, ConfigDict, Field, field_validator
from typing import Optional, List
import re
from datetime import date, datetime
from shared.validation import CodigoRequerido, DniPeruano, TextoRequerido

class EstudianteBase(BaseModel):
    codigo_estudiante: CodigoRequerido
    dni: DniPeruano
    nombres: TextoRequerido
    apellidos: TextoRequerido
    fecha_nacimiento: Optional[date] = None
    programa_id: Optional[int] = None
    email_institucional: Optional[EmailStr] = None
    email_personal: Optional[EmailStr] = None
    celular: Optional[str] = None
    direccion_domicilio: Optional[str] = None
    foto_url: Optional[str] = None
    pago_matricula: Optional[bool] = False
    documentos_completos: Optional[bool] = True
    fecha_limite_documentos: Optional[datetime] = None
    modalidad_admision: Optional[str] = "ORDINARIO"
    metadata_admision: Optional[dict] = {}

    @field_validator("fecha_nacimiento")
    @classmethod
    def validar_fecha_nacimiento(cls, valor):
        if valor is None:
            return valor
        if valor > date.today():
            raise ValueError("La fecha de nacimiento no puede ser futura")
        if valor.year < 1900:
            raise ValueError("La fecha de nacimiento no es válida")
        return valor

class EstudianteCreate(EstudianteBase):
    pass

class EstudianteUpdate(BaseModel):
    codigo_estudiante: Optional[CodigoRequerido] = None
    dni: Optional[DniPeruano] = None
    nombres: Optional[TextoRequerido] = None
    apellidos: Optional[TextoRequerido] = None
    fecha_nacimiento: Optional[date] = None
    programa_id: Optional[int] = None
    email_institucional: Optional[EmailStr] = None
    email_personal: Optional[EmailStr] = None
    celular: Optional[str] = None
    direccion_domicilio: Optional[str] = None
    estado_academico: Optional[str] = None
    foto_url: Optional[str] = None
    observaciones: Optional[str] = None
    pago_matricula: Optional[bool] = None
    documentos_completos: Optional[bool] = None
    fecha_limite_documentos: Optional[datetime] = None
    modalidad_admision: Optional[str] = "ORDINARIO"
    metadata_admision: Optional[dict] = {}

    @field_validator("fecha_nacimiento")
    @classmethod
    def validar_fecha_nacimiento(cls, valor):
        if valor is not None and valor > date.today():
            raise ValueError("La fecha de nacimiento no puede ser futura")
        return valor

class EstudianteResponse(EstudianteBase):
    id: int
    estado_academico: Optional[str] = "regular"
    foto_url: Optional[str] = None
    observaciones: Optional[str] = None
    pago_matricula: Optional[bool] = False
    documentos_completos: Optional[bool] = True
    fecha_limite_documentos: Optional[datetime] = None
    modalidad_admision: Optional[str] = "ORDINARIO"
    metadata_admision: Optional[dict] = {}
    model_config = ConfigDict(from_attributes=True)

class MatriculaDetalleBase(BaseModel):
    unidad_didactica_id: int
    creditos: int = Field(..., ge=1, le=40)

class MatriculaDetalleCreate(MatriculaDetalleBase):
    pass

class MatriculaDetalleResponse(MatriculaDetalleBase):
    id: int
    estado_curso: str
    model_config = ConfigDict(from_attributes=True)

class MatriculaBase(BaseModel):
    estudiante_id: int
    programa_id: int
    periodo_id: int
    tipo_ingreso: Optional[str] = "Ordinario"
    observaciones: Optional[str] = None

class MatriculaCreate(MatriculaBase):
    detalles: List[MatriculaDetalleCreate]

class MatriculaResponse(MatriculaBase):
    id: int
    estado_matricula: str
    detalles: List[MatriculaDetalleResponse] = []
    model_config = ConfigDict(from_attributes=True)

class IngestaAdmitido(BaseModel):
    dni: DniPeruano
    nombres: TextoRequerido
    apellidos: TextoRequerido
    programa_id: Optional[int] = None
    programa_nombre: Optional[str] = None
    periodo_id: Optional[int] = 1
    celular: Optional[str] = None
    email_personal: Optional[str] = None
    fecha_nacimiento: Optional[str] = None
    modalidad: Optional[str] = "ORDINARIO"
    metadata_completa: Optional[dict] = {}

    @field_validator("email_personal")
    @classmethod
    def normalizar_email_personal(cls, valor):
        if not valor:
            return None
        correo = str(valor).strip()
        return correo if re.fullmatch(r"[^@\s]+@[^@\s]+\.[^@\s]+", correo) else None

class IngestaMasivaRequest(BaseModel):
    proceso_admision_id: Optional[str] = "ADM-2026-I"
    admitidos: List[IngestaAdmitido]

# ================================
# BOLETIN DE NOTAS
class BoletinCurso(BaseModel):
    unidad_nombre: str
    creditos: int
    nota_c1: Optional[int] = None
    nota_c2: Optional[int] = None
    nota_c3: Optional[int] = None
    nota_final: Optional[int] = None
    estado: str = "cursando"

class BoletinHistorial(BaseModel):
    periodo_codigo: str
    promedio: Optional[int] = None
    cursos_aprobados: int = 0
    cursos_desaprobados: int = 0

class BoletinResponse(BaseModel):
    estudiante: dict
    matricula_estado: dict
    estado_academico: str
    progreso_creditos: dict
    cursos_periodo: List[BoletinCurso]
    resumen: dict
    historial: List[BoletinHistorial]
    observaciones: Optional[str] = None

# FASE 4: CASUISTICAS Y TRAMITES
# ================================

class HistorialAcademicoCreate(BaseModel):
    estudiante_id: int
    periodo_id: int
    estado: TextoRequerido
    resolucion: Optional[str] = None
    observaciones: Optional[str] = None

class HistorialAcademicoResponse(HistorialAcademicoCreate):
    id: int
    fecha_registro: date
    model_config = ConfigDict(from_attributes=True)

class BeneficioEstudianteCreate(BaseModel):
    estudiante_id: int
    tipo_beneficio: TextoRequerido
    porcentaje_descuento: float = Field(..., gt=0, le=100)
    condicion_mantenimiento: Optional[str] = None
    periodo_validez_inicio_id: int
    periodo_validez_fin_id: Optional[int] = None
    activo: bool = True

class BeneficioEstudianteResponse(BeneficioEstudianteCreate):
    id: int
    model_config = ConfigDict(from_attributes=True)

class SolicitudTramiteCreate(BaseModel):
    estudiante_id: int
    tipo_tramite: TextoRequerido
    observaciones: Optional[str] = None

class SolicitudTramiteResponse(SolicitudTramiteCreate):
    id: int
    estado: str
    fecha_solicitud: date
    fecha_resolucion: Optional[date] = None
    documento_url: Optional[str] = None
    model_config = ConfigDict(from_attributes=True)

class ConvalidacionDetalleCreate(BaseModel):
    unidad_destino_id: int
    curso_origen: TextoRequerido
    nota_reconocida: Optional[float] = Field(None, ge=0, le=20)
    creditos_reconocidos: Optional[int] = Field(None, ge=0, le=40)

class ConvalidacionDetalleResponse(ConvalidacionDetalleCreate):
    id: int
    resolucion_id: int
    model_config = ConfigDict(from_attributes=True)

class ResolucionConvalidacionCreate(BaseModel):
    estudiante_id: int
    numero_resolucion: TextoRequerido
    fecha_emision: date
    tipo_convalidacion: TextoRequerido
    institucion_origen: Optional[str] = None
    detalles: List[ConvalidacionDetalleCreate]

    @field_validator("fecha_emision")
    @classmethod
    def validar_fecha_emision(cls, valor):
        if valor > date.today():
            raise ValueError("La fecha de emisión no puede ser futura")
        return valor

class ResolucionConvalidacionResponse(BaseModel):
    id: int
    estudiante_id: int
    numero_resolucion: str
    fecha_emision: date
    tipo_convalidacion: str
    institucion_origen: Optional[str] = None
    estado: str
    detalles: List[ConvalidacionDetalleResponse] = []
    model_config = ConfigDict(from_attributes=True)

