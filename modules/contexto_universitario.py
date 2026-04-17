"""
Resumen de enfoque curricular típico por universidad (referencia para prompts o lógica de tutoría).
"""

from __future__ import annotations

import re
from typing import Optional

MALLAS = {
    "UCV": "Enfoque en rigor analítico, demostraciones y aplicaciones físicas clásicas (Cálculo II). Lenguaje formal.",
    "USB": "Sistema trimestral acelerado. Fuerte en técnicas avanzadas de integración y aplicaciones físicas inmediatas.",
    "UNIMET": "Enfoque práctico/económico. Énfasis en excedentes, finanzas y modelado industrial con EDO.",
    "ULA": "Tradición analítica. Alta importancia a series, sucesiones e integrales impropias profundas.",
    "LUZ": "Orientado a ingeniería aplicada: cálculo de áreas, volúmenes y momentos de inercia.",
    "UC": "Equilibrio entre teoría y práctica, con énfasis en ecuaciones diferenciales lineales de orden superior.",
}


def obtener_contexto(universidad: Optional[str]) -> str:
    """Devuelve la descripción de malla si la clave coincide; si no, el texto genérico."""
    if not universidad or not str(universidad).strip():
        return "Estudiante universitario de ingeniería/ciencias."
    clave = str(universidad).strip().upper()
    return MALLAS.get(clave, "Estudiante universitario de ingeniería/ciencias.")


def clave_malla_desde_institucion(institucion: Optional[str]) -> Optional[str]:
    """
    Devuelve la clave presente en ``MALLAS`` (ej. ``UCV``) si el texto de institución
    del estudiante permite inferirla; si no, ``None``.
    """
    if not institucion or not str(institucion).strip():
        return None
    raw = str(institucion).strip()
    cu = raw.upper()
    if cu in MALLAS:
        return cu

    from modules.planes_estudio import detectar_plan_por_institucion

    plan = detectar_plan_por_institucion(raw)
    if plan and plan in MALLAS:
        return plan

    s = re.sub(r"\s+", " ", raw.lower())
    if re.search(r"\bula\b", s) or "los andes" in s:
        return "ULA"
    if re.search(r"\bluz\b", s) or "zulia" in s or "del zulia" in s:
        return "LUZ"
    if "carabobo" in s:
        return "UC"
    return None


def texto_instruccion_contexto_malla(institucion: Optional[str]) -> str:
    """
    Instrucción para el prompt del tutor cuando la institución corresponde a una entrada
    de ``MALLAS``; cadena vacía si no aplica.
    """
    clave = clave_malla_desde_institucion(institucion)
    if not clave:
        return ""
    contexto_malla = MALLAS.get(clave, "")
    if not contexto_malla:
        return ""
    universidad = (institucion or "").strip() or clave
    return (
        f"Estás respondiendo a un estudiante de la {universidad}. "
        f"Ajusta tu nivel de rigor, ejemplos y terminología según el siguiente contexto: {contexto_malla}"
    )
