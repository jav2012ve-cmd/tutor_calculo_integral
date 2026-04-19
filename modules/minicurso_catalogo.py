"""
Catálogo de archivos ``data/minicurso_*.json`` (schema 2) compartido por Ruta Maestra y perfil de temas.
"""

from __future__ import annotations

import json
import os
from typing import Any

from modules import contexto_universitario


def _raiz_proyecto() -> str:
    return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def listar_entradas_minicurso_v2() -> list[dict[str, Any]]:
    """Cada entrada: path, label, data (dict del JSON), basename."""
    carpeta = os.path.join(_raiz_proyecto(), "data")
    if not os.path.isdir(carpeta):
        return []
    out: list[dict[str, Any]] = []
    for nombre in sorted(os.listdir(carpeta)):
        if not (nombre.startswith("minicurso_") and nombre.endswith(".json")):
            continue
        if nombre == "minicurso_anexo_ucv_ingenieria.json":
            continue
        ruta = os.path.join(carpeta, nombre)
        try:
            with open(ruta, encoding="utf-8") as f:
                data = json.load(f)
        except (OSError, json.JSONDecodeError, TypeError):
            continue
        if not isinstance(data, dict):
            continue
        if int(data.get("schema_version") or 0) != 2:
            continue
        clave = (data.get("universidad_clave") or "").strip()
        if not clave:
            continue
        cnom = (data.get("carrera_nombre_oficial") or "").strip() or (data.get("carrera_id") or "").strip()
        curso = (data.get("curso_codigo") or "").strip()
        suf = f" · {curso}" if curso else ""
        label = f"{clave} — {cnom}{suf}"
        out.append({"path": ruta, "label": label, "data": data, "basename": nombre})
    return out


def inferir_indice_por_institucion(institucion: str, entradas: list[dict[str, Any]]) -> int:
    if not entradas or not (institucion or "").strip():
        return 0
    inst_raw = institucion.strip()
    inst_u = inst_raw.upper()
    clave = contexto_universitario.clave_malla_desde_institucion(inst_raw)
    if clave:
        for i, e in enumerate(entradas):
            if (e["data"].get("universidad_clave") or "").upper() == clave.upper():
                return i
    for i, e in enumerate(entradas):
        if (e["data"].get("universidad_clave") or "").upper() == inst_u:
            return i
    for i, e in enumerate(entradas):
        ck = (e["data"].get("universidad_clave") or "").strip().upper()
        if len(ck) >= 3 and ck in inst_u:
            return i
    return 0


def orden_temario_desde_entrada(entradas: list[dict[str, Any]], indice: int) -> list[str]:
    if not entradas or indice < 0 or indice >= len(entradas):
        return []
    orden = entradas[indice]["data"].get("orden_temario_atomico")
    if not isinstance(orden, list):
        return []
    return [str(x).strip() for x in orden if str(x).strip()]
