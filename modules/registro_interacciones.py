"""
Registro append-only de interacciones usuario–IA en CSV local.
"""
from __future__ import annotations

import csv
import os
from datetime import datetime
from typing import Any, List, Union

try:
    from PIL import Image as PILImageModule
except ImportError:
    PILImageModule = None

FIELDNAMES = ["Fecha/Hora", "Pregunta", "Respuesta", "Modelo"]
NOMBRE_ARCHIVO = "interacciones_tutor.csv"


def _ruta_archivo() -> str:
    """Raíz del proyecto (carpeta que contiene `app.py` y `modules/`)."""
    mod_dir = os.path.dirname(os.path.abspath(__file__))
    raiz = os.path.abspath(os.path.join(mod_dir, os.pardir))
    return os.path.join(raiz, NOMBRE_ARCHIVO)


def serializar_pregunta(prompt_parts: Union[str, List[Any]]) -> str:
    """Convierte el prompt enviado a Gemini en un solo texto para el CSV."""
    if isinstance(prompt_parts, str):
        return prompt_parts
    partes: List[str] = []
    for p in prompt_parts:
        if isinstance(p, str):
            partes.append(p)
        elif PILImageModule is not None and isinstance(p, PILImageModule.Image):
            partes.append("[imagen]")
        else:
            partes.append("[contenido no textual]")
    return "\n---\n".join(partes)


def extraer_texto_respuesta(response: Any) -> str:
    """Obtiene el texto de la respuesta de Gemini de forma tolerante a errores."""
    if response is None:
        return ""
    try:
        t = response.text
        return t if t is not None else ""
    except (ValueError, AttributeError):
        pass
    try:
        cand = response.candidates[0]
        parts = cand.content.parts
        return "".join(getattr(part, "text", "") or "" for part in parts)
    except (IndexError, AttributeError, TypeError):
        return "(contenido no disponible o bloqueado por políticas)"


def registrar_interaccion(pregunta: str, respuesta: str, modelo: str) -> None:
    """
    Añade una fila a interacciones_tutor.csv (crea archivo y cabecera si no existen).
    No borra filas anteriores. Fallos de disco no interrumpen la app.
    """
    ruta = _ruta_archivo()
    escribir_cabecera = not os.path.isfile(ruta) or os.path.getsize(ruta) == 0
    fila = {
        "Fecha/Hora": datetime.now().isoformat(timespec="seconds"),
        "Pregunta": pregunta or "",
        "Respuesta": respuesta or "",
        "Modelo": modelo or "",
    }
    try:
        with open(ruta, "a", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=FIELDNAMES, quoting=csv.QUOTE_MINIMAL)
            if escribir_cabecera:
                w.writeheader()
            w.writerow(fila)
    except OSError as e:
        import sys

        print(f"[registro_interacciones] No se pudo escribir {ruta}: {e}", file=sys.stderr)
