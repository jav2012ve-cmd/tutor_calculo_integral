"""
Particularidades curriculares por plantel (UCV, USB, UNIMET) para contextualizar
respuestas de la IA sin sustituir el temario común del tutor.

Uso típico: ``texto_contexto_ia_para_estudiante()`` lee la institución de la sesión
(``auth_estudiante_institucion``) y devuelve un bloque listo para anexar a prompts.
"""

from __future__ import annotations

import re
from typing import Any, Optional

# Claves internas (mayúsculas) para identificar cada plan.
PLAN_UCV = "UCV"
PLAN_USB = "USB"
PLAN_UNIMET = "UNIMET"

PLANES_ESTUDIO: dict[str, dict[str, str]] = {
    PLAN_UCV: {
        "nombre_corto": "UCV",
        "programa_referencia": "Ingeniería — Cálculo II",
        "resumen": (
            "Énfasis en métodos de integración clásicos; a veces se incluye series de potencias. "
            "Rigor analítico alto, orientado a la demostración de teoremas y al formalismo propio del curso."
        ),
        "enfasis_ia": (
            "Prioriza integración clásica (sustitución, partes, fracciones parciales, trigonométricas) "
            "y, cuando aplique, series de potencias. Cuando el estudiante pida rigor, ofrece pasos "
            "alineados a demostraciones y justificaciones formales (hipótesis, conclusiones)."
        ),
    },
    PLAN_USB: {
        "nombre_corto": "USB",
        "programa_referencia": "Matemáticas II / III",
        "resumen": (
            "Sistema de trimestres y ritmo acelerado. Énfasis en problemas de optimización y "
            "aplicaciones físicas inmediatas (trabajo, presión, entre otras)."
        ),
        "enfasis_ia": (
            "Mantén respuestas compactas y orientadas a ejercicios-tipo; conecta rápido con "
            "optimización (extremos, restricciones) y con física aplicada (trabajo, presión, "
            "interpretación de integrales en contexto). Evita divagación: el ritmo del trimestre exige ir al grano."
        ),
    },
    PLAN_UNIMET: {
        "nombre_corto": "UNIMET",
        "programa_referencia": "Matemáticas II",
        "resumen": (
            "Enfoque muy orientado a la resolución de problemas prácticos y al uso de tecnología, "
            "manteniendo rigor en aplicaciones económicas (excedentes) y de ingeniería."
        ),
        "enfasis_ia": (
            "Favorece planteamientos prácticos, interpretación de resultados y modelado aplicado "
            "(excedentes de consumidor/productor, costos, cantidades equilibradas; también ingeniería). "
            "Puedes sugerir verificación con herramientas (CAS/gráficos) cuando ayude, sin sustituir el razonamiento."
        ),
    },
}


def _normalizar_busqueda(texto: str) -> str:
    return re.sub(r"\s+", " ", (texto or "").strip().lower())


def detectar_plan_por_institucion(institucion: Optional[str]) -> Optional[str]:
    """
    Devuelve la clave de ``PLANES_ESTUDIO`` (``UCV``, ``USB``, ``UNIMET``) si el texto
    del estudiante permite inferirlo; si no, ``None``.
    """
    s = _normalizar_busqueda(institucion or "")
    if not s:
        return None
    if re.search(r"\bucv\b", s) or "universidad central" in s:
        return PLAN_UCV
    if re.search(r"\busb\b", s) or "simón bolívar" in s or "simon bolivar" in s:
        return PLAN_USB
    if re.search(r"\bunimet\b", s) or "universidad metropolitana" in s:
        return PLAN_UNIMET
    return None


def texto_bloque_plan(plan_key: str) -> str:
    """Texto único para pegar en system/context de la IA (español)."""
    p = PLANES_ESTUDIO.get(plan_key)
    if not p:
        return ""
    return (
        f"CONTEXTO INSTITUCIONAL ({p['nombre_corto']} — {p['programa_referencia']}):\n"
        f"- Perfil del curso: {p['resumen']}\n"
        f"- Orientación para tus respuestas: {p['enfasis_ia']}"
    )


def texto_contexto_ia_para_estudiante() -> str:
    """
    Lee ``st.session_state['auth_estudiante_institucion']`` si existe sesión Supabase
    y devuelve el bloque de contexto; cadena vacía si no aplica.
    """
    try:
        import streamlit as st

        inst = (st.session_state.get("auth_estudiante_institucion") or "").strip()
    except Exception:
        inst = ""
    key = detectar_plan_por_institucion(inst)
    if not key:
        return ""
    return texto_bloque_plan(key)


def texto_contexto_ia_desde_institucion(institucion: Optional[str]) -> str:
    """Variante sin Streamlit (tests u otros módulos)."""
    key = detectar_plan_por_institucion(institucion)
    if not key:
        return ""
    return texto_bloque_plan(key)


def metadatos_plan(plan_key: str) -> Optional[dict[str, str]]:
    """Copia superficial del dict del plan, o ``None`` si la clave no existe."""
    p = PLANES_ESTUDIO.get(plan_key)
    return dict(p) if p else None


def listar_planes() -> list[str]:
    """Claves conocidas (orden fijo para UI o depuración)."""
    return [PLAN_UCV, PLAN_USB, PLAN_UNIMET]
