from fastapi import FastAPI, HTTPException, Request, UploadFile, File, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
import json
import os
import re
import uvicorn
from contextlib import asynccontextmanager
from io import BytesIO
import pandas as pd
from datetime import datetime

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import delete

from database import engine, Base, get_db
from models import PostulanteAdmitido
from programas_catalog import resolver_programa_id, normalizar_texto

import sys
sys.path.append("/app")

is_published = False

MAX_ARCHIVO_BYTES = 25 * 1024 * 1024
CODIGOS_PRUEBA = {"439"}
ALIAS_COLUMNAS = {
    "dni": ("nro de documento", "numero de documento", "dni", "documento"),
    "nombres": ("nombres", "nombre"),
    "paterno": ("apellido paterno", "paterno"),
    "materno": ("apellido materno", "materno"),
    "programa": ("programa de estudios", "programa"),
    "modalidad": ("modalidad",),
    "email": ("correo", "email"),
    "celular": ("celular",),
    "fecha_nacimiento": ("fecha nacimiento",),
    "codigo": ("codigo",),
}

@asynccontextmanager
async def lifespan(app: FastAPI):
    try:
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all, checkfirst=True)
    except Exception as e:
        print(f"init_db: tablas ya existen o error menor: {e}")
    yield

app = FastAPI(title="Módulo de Admisión", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/health")
async def health_check():
    return {"status": "ok", "module": "mod-admision"}

@app.get("/")
async def root():
    html_content = """
    <!DOCTYPE html>
    <html lang="es">
    <head>
        <meta charset="UTF-8">
        <title>Panel de Control - Admisión</title>
        <style>
            body { font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background-color: #f8fafc; display: flex; flex-direction: column; align-items: center; justify-content: center; height: 100vh; margin: 0; }
            .card { background: white; padding: 2.5rem; border-radius: 12px; box-shadow: 0 4px 6px -1px rgb(0 0 0 / 0.1); text-align: center; max-width: 550px; }
            .btn { background-color: #4f46e5; color: white; border: none; padding: 12px 24px; border-radius: 8px; font-weight: bold; font-size: 16px; cursor: pointer; transition: background-color 0.2s; margin-top: 15px;}
            .btn:hover { background-color: #4338ca; }
            .btn:disabled { background-color: #94a3b8; cursor: not-allowed; }
            .status { margin-top: 20px; font-weight: 500; color: #15803d; }
            .file-input-container { margin: 20px 0; padding: 20px; border: 2px dashed #cbd5e1; border-radius: 8px; background: #f1f5f9;}
        </style>
    </head>
    <body>
        <div class="card">
            <h1 style="color: #1e293b; margin-top:0;">Oficina de Admisión</h1>
            <p style="color: #64748b;">Carga el archivo Excel de resultados de admisión (ADMISION_2026.xlsx) para procesar e inyectar a los estudiantes en el sistema.</p>
            
            <form id="uploadForm">
                <div class="file-input-container">
                    <input type="file" id="excelFile" accept=".xlsx" required />
                </div>
                <button type="submit" id="pubBtn" class="btn">
                    Subir y Procesar Resultados
                </button>
            </form>
            <div id="status" class="status"></div>
        </div>
        <script>
            document.getElementById('uploadForm').addEventListener('submit', async (e) => {
                e.preventDefault();
                const btn = document.getElementById('pubBtn');
                const statusDiv = document.getElementById('status');
                const fileInput = document.getElementById('excelFile');
                
                if (!fileInput.files.length) return;
                
                btn.disabled = true;
                btn.innerText = "Procesando Excel...";
                statusDiv.innerText = "";
                
                const formData = new FormData();
                formData.append("file", fileInput.files[0]);
                
                try {
                    const res = await fetch('/api/mod-admision/upload', { 
                        method: 'POST',
                        body: formData
                    });
                    
                    const data = await res.json();
                    if(res.ok) {
                        btn.innerText = "¡Procesado Exitosamente!";
                        statusDiv.innerText = `✅ ${data.message}`;
                        statusDiv.style.color = '#15803d';
                    } else {
                        throw new Error(data.detail || "Error al procesar el archivo");
                    }
                } catch (err) {
                    btn.disabled = false;
                    btn.innerText = "Subir y Procesar Resultados";
                    statusDiv.innerText = `❌ ${err.message}`;
                    statusDiv.style.color = '#dc2626';
                }
            });
        </script>
    </body>
    </html>
    """
    return HTMLResponse(content=html_content)


def sanitize_row(row):
    result = {}
    for key, value in row.items():
        if value is None or (not isinstance(value, str) and pd.isna(value)):
            result[str(key)] = None
        elif isinstance(value, pd.Timestamp):
            result[str(key)] = value.isoformat()
        elif hasattr(value, "item") and not isinstance(value, str):
            result[str(key)] = value.item()
        else:
            result[str(key)] = value
    return result


def _normalizar_header(header):
    return normalizar_texto(header).rstrip(":")


def _resolver_columnas(df):
    normalizadas = {_normalizar_header(columna): columna for columna in df.columns}
    columnas = {}
    for campo, alias in ALIAS_COLUMNAS.items():
        for nombre in alias:
            if nombre in normalizadas:
                columnas[campo] = normalizadas[nombre]
                break
    faltantes = [campo for campo in ("dni", "nombres", "paterno", "materno", "programa") if campo not in columnas]
    if faltantes:
        raise ValueError(
            "Faltan columnas obligatorias en el Excel de admisión: "
            + ", ".join(faltantes)
            + ". Columnas encontradas: "
            + ", ".join(str(c) for c in df.columns)
        )
    return columnas


def _valor(row, columnas, campo):
    return row.get(columnas.get(campo)) if campo in columnas else None


def _texto(valor):
    if valor is None:
        return ""
    return str(valor).strip()


def _dni(valor):
    return re.sub(r"\D", "", _texto(valor))


def _procesar_filas(df, columnas, modalidad_por_defecto, resumen, dnis_vistos):
    admitidos = []
    for numero, (_, fila) in enumerate(df.iterrows(), start=2):
        row = sanitize_row(fila)
        dni = _dni(_valor(row, columnas, "dni"))
        codigo = _texto(_valor(row, columnas, "codigo")).replace(".0", "")
        if not dni and not codigo:
            continue
        resumen["filas_leidas"] += 1

        if codigo in CODIGOS_PRUEBA:
            resumen["omitidas"] += 1
            resumen["errores"].append(f"Fila {numero}: fila de prueba descartada (código {codigo}).")
            continue
        if not (5 <= len(dni) <= 12):
            resumen["omitidas"] += 1
            resumen["errores"].append(f"Fila {numero}: DNI inválido {dni!r}.")
            continue
        if dni in dnis_vistos:
            resumen["omitidas"] += 1
            resumen["errores"].append(f"Fila {numero}: DNI duplicado {dni}.")
            continue

        nombres = _texto(_valor(row, columnas, "nombres"))
        apellidos = " ".join(filter(None, [
            _texto(_valor(row, columnas, "paterno")),
            _texto(_valor(row, columnas, "materno")),
        ]))
        if not nombres or not apellidos:
            resumen["omitidas"] += 1
            resumen["errores"].append(f"Fila {numero}: nombres o apellidos incompletos.")
            continue

        nombre_programa = _texto(_valor(row, columnas, "programa"))
        programa_id = resolver_programa_id(nombre_programa)
        if programa_id is None:
            resumen["omitidas"] += 1
            resumen["errores"].append(
                f"Fila {numero}: programa no reconocido {nombre_programa!r}."
            )
            continue

        dnis_vistos.add(dni)
        celular = _dni(_valor(row, columnas, "celular"))
        fecha = _valor(row, columnas, "fecha_nacimiento")
        admitidos.append(PostulanteAdmitido(
            dni=dni,
            nombres=nombres,
            apellidos=apellidos,
            programa_nombre=nombre_programa,
            modalidad_admision=_texto(_valor(row, columnas, "modalidad")) or modalidad_por_defecto,
            email=_texto(_valor(row, columnas, "email")) or None,
            celular=celular or None,
            fecha_nacimiento=_texto(fecha) or None,
            metadata_admision={**row, "programa_id": programa_id},
        ))
        resumen["por_programa"][programa_id] = resumen["por_programa"].get(programa_id, 0) + 1
    return admitidos


from starlette.concurrency import run_in_threadpool


def parse_excel_sync(contents: bytes):
    excel_data = pd.ExcelFile(BytesIO(contents))
    nombres_normalizados = {normalizar_texto(s): s for s in excel_data.sheet_names}

    hoja_reg = nombres_normalizados.get("b_datos")
    if hoja_reg is None:
        raise ValueError(
            "El Excel debe contener una hoja 'B_Datos'. "
            f"Hojas encontradas: {excel_data.sheet_names}"
        )

    df_reg = pd.read_excel(excel_data, sheet_name=hoja_reg)
    columnas = _resolver_columnas(df_reg)
    resumen = {"errores": [], "filas_leidas": 0, "omitidas": 0, "por_programa": {}}
    dnis_vistos = set()
    admitidos = _procesar_filas(df_reg, columnas, "ORDINARIO", resumen, dnis_vistos)

    hoja_exo = nombres_normalizados.get("b_datos_exonerados")
    if hoja_exo is not None:
        df_exo = pd.read_excel(excel_data, sheet_name=hoja_exo)
        columnas_exo = _resolver_columnas(df_exo)
        admitidos.extend(_procesar_filas(df_exo, columnas_exo, "EXONERADO", resumen, dnis_vistos))

    return admitidos, resumen


@app.post("/upload")
async def upload_excel(file: UploadFile = File(...), db: AsyncSession = Depends(get_db)):
    nombre = (file.filename or "").lower()
    if not nombre.endswith((".xlsx", ".xls")):
        raise HTTPException(
            status_code=400,
            detail="El archivo debe ser un Excel (.xlsx o .xls) con las hojas 'B_Datos' y 'B_Datos_Exonerados'.",
        )

    contents = await file.read()
    if not contents:
        raise HTTPException(status_code=400, detail="El archivo está vacío.")
    if len(contents) > MAX_ARCHIVO_BYTES:
        raise HTTPException(status_code=400, detail="El archivo supera el tamaño máximo de 25 MB.")

    try:
        admitidos_list, resumen = await run_in_threadpool(parse_excel_sync, contents)
    except Exception as exc:
        raise HTTPException(status_code=400, detail=f"No se pudo procesar el Excel: {exc}")

    if not admitidos_list:
        raise HTTPException(
            status_code=400,
            detail={
                "message": "No se encontraron admitidos válidos en el archivo.",
                **resumen,
            },
        )

    await db.execute(delete(PostulanteAdmitido))
    db.add_all(admitidos_list)
    await db.commit()

    global is_published
    is_published = True

    return {
        "message": f"Se procesaron {len(admitidos_list)} admitidos válidos. Resultados publicados.",
        "procesados": len(admitidos_list),
        **resumen,
    }


@app.get("/admitidos")
async def get_admitidos(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(PostulanteAdmitido))
    records = result.scalars().all()

    formatted = []
    no_reconocidos = []
    for record in records:
        programa_id = resolver_programa_id(record.programa_nombre)
        if programa_id is None:
            no_reconocidos.append(record.programa_nombre)
        formatted.append({
            "dni": record.dni,
            "nombres": record.nombres,
            "apellidos": record.apellidos,
            "programa_id": programa_id,
            "programa_nombre": record.programa_nombre,
            "celular": record.celular,
            "email_personal": record.email,
            "fecha_nacimiento": record.fecha_nacimiento,
            "modalidad": record.modalidad_admision,
            "metadata_completa": record.metadata_admision,
        })

    respuesta = {"admitidos": formatted}
    if no_reconocidos:
        respuesta["programas_no_reconocidos"] = sorted(set(no_reconocidos))
    return respuesta

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8009)
