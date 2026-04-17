"""
Planes de estudio oficiales por universidad (V1).

Origen: documento «Propuesta de Módulo: planes_de_estudio_oficiales V1» — actúa como
referencia académica para alinear la IA y la interfaz con la malla típica del estudiante.

https://docs.google.com/document/d/1luR_JZIOE8oaAaT9t52Hn5OUU-D5tPd5t67KS4ESSUM/edit
"""

from __future__ import annotations

from typing import Optional, TypedDict


class PlanDetallado(TypedDict):
    nombre_curso: str
    enfoque: str
    temas_criticos: list[str]
    bibliografia: list[str]
    guia_estudio: str


PLANES_DETALLADOS: dict[str, PlanDetallado] = {
    "UCV": {
        "nombre_curso": "Cálculo II (Ingeniería)",
        "enfoque": "Rigor formal y fundamentación analítica.",
        "temas_criticos": [
            "Sumas de Riemann",
            "Teorema Fundamental",
            "Series de Potencias",
        ],
        "bibliografia": ["Leithold", "Demidovich", "Piskunov"],
        "guia_estudio": (
            "Prioriza la demostración de teoremas y el desarrollo exhaustivo de integrales impropias."
        ),
    },
    "USB": {
        "nombre_curso": "Matemáticas II (MA1112)",
        "enfoque": "Sistema trimestral acelerado y aplicaciones técnicas.",
        "temas_criticos": [
            "Funciones Trascendentes",
            "Sustitución Trigonométrica",
            "Optimización",
        ],
        "bibliografia": ["Apostol", "Purcell"],
        "guia_estudio": (
            "Enfócate en la velocidad de resolución y el manejo de funciones exponenciales/logarítmicas."
        ),
    },
    "UNIMET": {
        "nombre_curso": "Matemáticas II",
        "enfoque": "Pragmático con énfasis en aplicaciones económicas e industriales.",
        "temas_criticos": [
            "Excedentes del Consumidor",
            "Modelado con EDO",
            "Áreas",
        ],
        "bibliografia": ["James Stewart", "Larson"],
        "guia_estudio": (
            "Aplica las integrales a problemas de valor presente y excedentes económicos."
        ),
    },
    "ULA": {
        "nombre_curso": "Cálculo 20",
        "enfoque": "Analítico tradicional con énfasis en coordenadas polares.",
        "temas_criticos": [
            "Coordenadas Polares",
            "Sucesiones",
            "Sustitución Universal",
        ],
        "bibliografia": ["Spivak", "Swokowski"],
        "guia_estudio": (
            "Refuerza el cálculo de áreas y volúmenes en coordenadas no cartesianas."
        ),
    },
    "LUZ": {
        "nombre_curso": "Cálculo II / Multivariable",
        "enfoque": "Técnico-ingenieril orientado a física y mecánica.",
        "temas_criticos": [
            "Momentos de Inercia",
            "Superficies de Revolución",
            "Integrales Múltiples",
        ],
        "bibliografia": ["Thomas/Finney", "Stewart Multivariable"],
        "guia_estudio": (
            "Concéntrate en la aplicación de la integral para hallar centros de masa y trabajo."
        ),
    },
    "UC": {
        "nombre_curso": "Cálculo Integral y Series",
        "enfoque": "Balanceado, puente hacia geometría diferencial.",
        "temas_criticos": [
            "EDO Lineales",
            "Series Numéricas",
            "Centros de Gravedad",
        ],
        "bibliografia": ["Courant & John", "Spiegel (Schaum)"],
        "guia_estudio": (
            "Estudia la convergencia de series como preparación para ecuaciones diferenciales."
        ),
    },
}


def listar_claves_planes() -> list[str]:
    """Claves ordenadas (UC, UCV, …) para UI o depuración."""
    return sorted(PLANES_DETALLADOS.keys())


def obtener_plan_por_clave(clave: str) -> Optional[PlanDetallado]:
    """Devuelve el plan si ``clave`` coincide exactamente (ej. ``UCV``); si no, ``None``."""
    k = (clave or "").strip().upper()
    return PLANES_DETALLADOS.get(k)


def obtener_plan_desde_institucion(institucion: Optional[str]) -> Optional[PlanDetallado]:
    """
    Resuelve la institución libre del estudiante a una clave de ``PLANES_DETALLADOS``
    (reutiliza la lógica de ``contexto_universitario.clave_malla_desde_institucion``).
    """
    from modules import contexto_universitario

    clave = contexto_universitario.clave_malla_desde_institucion(institucion)
    if not clave:
        return None
    return PLANES_DETALLADOS.get(clave)


def texto_bloque_plan_oficial_para_prompt(institucion: Optional[str]) -> str:
    """
    Texto listo para inyectar en el system/context de la IA (vacío si no hay plan).
    """
    plan = obtener_plan_desde_institucion(institucion)
    if not plan:
        return ""
    temas = ", ".join(plan["temas_criticos"])
    bib = ", ".join(plan["bibliografia"])
    return (
        f"PLAN DE ESTUDIO INSTITUCIONAL ({plan['nombre_curso']}):\n"
        f"- Enfoque: {plan['enfoque']}\n"
        f"- Temas críticos / prioritarios: {temas}\n"
        f"- Bibliografía de referencia (alinear nivel y estilo de ejemplos): {bib}\n"
        f"- Guía de estudio: {plan['guia_estudio']}"
    )
