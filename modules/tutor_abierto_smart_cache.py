"""
Smart cache para el modo «Dime y te digo» (Tutor Abierto).

Antes de llamar a Gemini: reutiliza respuestas del catálogo maestro o del historial
reciente (misma firma de pregunta y tema seleccionado, últimas 24 h).
El texto devuelto se sanitiza con la misma función que el PDF (Markdown/HTML).
"""

from __future__ import annotations

import re
import time
import unicodedata
from collections.abc import Callable
from typing import Any, Optional

import streamlit as st

from modules import perfil_curso, temario

TTL_HISTORIAL_SEG = 86400  # 24 h

# Entradas maestras: (temas permitidos vacío = cualquier tema activo), firmas alineadas a ``firma_pregunta``
# (sin tildes en las claves de matching), plantilla con {nombre}. El bloque 1.1.2 va sin $/$$ y con ^ en
# potencias para máxima compatibilidad con el PDF antes incluso de ``sanitizar_salida_gemini_para_pdf``.
_CATALOGO_MAESTRO: tuple[dict[str, Any], ...] = (
    {
        "temas": ("1.1.1 Integrales Indefinidas Directas",),
        "firmas": (
            "que es una integral indefinida",
            "define integral indefinida",
            "que es primitiva",
            "concepto de integral indefinida",
        ),
        "texto": (
            "Hola {nombre}. Una integral indefinida de una función f es el conjunto de todas sus primitivas: "
            "si F'(x) = f(x), escribimos $\\int f(x)\\,dx = F(x) + C$ con C constante arbitraria. "
            "En el curso seguimos la misma idea que en los ejercicios del banco: primero identificar la regla "
            "o sustitución que lleva la expresión a una forma estándar, y luego ajustar la constante."
        ),
    },
    {
        "temas": ("1.1.2 Cambios de variables (Sustitución)",),
        "firmas": (
            "baile de la sustitucion",
            "baile sustitucion",
            "baile",
            "metafora",
            "cambio de variable",
            "cambio de variables",
            "sustitucion",
            "u du",
            "metafora sustitucion",
            "metafora cambio de variable",
        ),
        "texto": (
            "Hola {nombre}, bienvenido a la pista de baile del Cálculo. A veces, una integral parece una pareja "
            "que no coordina: tienes una función complicada y, al lado, algo que no ayuda a cerrar la fiesta "
            "(la integral).\n\n"
            "1. El Conflicto: tienes una variable (digamos x) atrapada en una situación difícil.\n\n"
            "2. El Cambio de Pareja (Sustitución): buscamos una nueva acompañante, la variable u. Para que el "
            "baile funcione, u debe ser una parte de la función cuya derivada (du) también esté presente en la fiesta.\n\n"
            "3. La Fiesta (Resolución): cuando u y du quedan alineados, la integral se vuelve amigable y más fácil "
            "de resolver.\n\n"
            "4. El Regreso a Casa (deshacer el cambio): al terminar la música no te quedas con la pareja temporal; "
            "devuelves el protagonismo a la variable original (x) para entregar el resultado final.\n\n"
            "Ejemplo clásico: para resolver la integral de (2x + 5)^10 respecto a x:\n"
            "• Pareja temporal (u): 2x + 5.\n"
            "• Su acompañante (du): 2 dx.\n"
            "• En la fiesta: integramos u^10 y obtenemos u^11/11 (más la constante de integración).\n"
            "• Regreso oficial: sustituimos u por (2x + 5) y listo."
        ),
    },
    {
        "temas": ("1.1.5 Integral por partes",),
        "firmas": (
            "formula de integral por partes",
            "integracion por partes formula",
            "enunciado integral por partes",
        ),
        "texto": (
            "Hola {nombre}. La fórmula clásica es $\\int u\\,dv = uv - \\int v\\,du$. "
            "Elige u de modo que al derivarla simplifiques el integrando (logaritmo, polinomio corto) "
            "y dv sea fácil de integrar. Es el patrón que verás en los parciales tipo del curso."
        ),
    },
    {
        "temas": (),
        "firmas": (
            "teorema fundamental del calculo",
            "teorema fundamental del calculo integral",
            "que dice el teorema fundamental",
        ),
        "texto": (
            "Hola {nombre}. El teorema fundamental enlaza derivada e integral: si f es continua en [a,b] y "
            "F es una primitiva de f, entonces $\\int_a^b f(x)\\,dx = F(b)-F(a)$. "
            "También, $\\frac{d}{dx}\\int_a^x f(t)\\,dt = f(x)$. Conviene practicarlo con ejercicios de "
            "integral definida del temario para automatizar el planteamiento en examen."
        ),
    },
)


def firma_pregunta(texto: str) -> str:
    """Firma estable para comparar preguntas (sin distinguir mayúsculas ni acentos fuertes)."""
    raw = (texto or "").strip().lower()
    if not raw:
        return ""
    nk = unicodedata.normalize("NFKD", raw)
    sin_tono = "".join(c for c in nk if unicodedata.category(c) != "Mn")
    sin_tono = re.sub(r"[^\w\sáéíóúñü.+-]", " ", sin_tono, flags=re.IGNORECASE)
    sin_tono = re.sub(r"\s+", " ", sin_tono).strip()
    return sin_tono[:420]


def normalizar_tema_seleccionado(tema_ui: Optional[str]) -> str:
    """Alinea el tema del selector al temario activo (mismo criterio que el resto de la app)."""
    opts = perfil_curso.lista_temas_activa() or list(temario.LISTA_TEMAS)
    t = temario.normalizar_tema_curso(tema_ui, temas_validos=opts)
    return (t or (tema_ui or "").strip() or "")


def _nombre_participante() -> str:
    n = (st.session_state.get("auth_estudiante_nombre") or "").strip()
    if n and n.lower() != "invitado":
        return n
    n2 = (st.session_state.get("estudiante_nombre_seguimos") or "").strip()
    if n2:
        return n2
    return "estudiante"


def personalizar_nombre(texto: str) -> str:
    return (
        str(texto or "")
        .replace("{{nombre}}", _nombre_participante())
        .replace("{nombre}", _nombre_participante())
    )


def _firma_coincide_maestro(fp: str, firmas: tuple[str, ...]) -> bool:
    if not fp:
        return False
    for f in firmas:
        if fp == f or f in fp or fp in f:
            return True
    return False


def _buscar_maestro(tema_norm: str, fp: str) -> Optional[str]:
    for bloque in _CATALOGO_MAESTRO:
        temas_b: tuple[str, ...] = tuple(bloque.get("temas") or ())
        firmas: tuple[str, ...] = tuple(bloque.get("firmas") or ())
        texto = str(bloque.get("texto") or "")
        if not texto or not firmas or not _firma_coincide_maestro(fp, firmas):
            continue
        if temas_b and (tema_norm not in temas_b):
            continue
        return texto
    return None


def _buscar_en_historial(
    historial: list[dict[str, Any]],
    *,
    tema_norm: str,
    fp: str,
    ahora: float,
) -> Optional[str]:
    """Última respuesta del asistente con misma firma y tema, si el timestamp está dentro de 24 h."""
    if not fp or not tema_norm:
        return None
    for m in reversed(historial):
        if str(m.get("role", "")).lower() != "assistant":
            continue
        if m.get("q_firma") != fp:
            continue
        if m.get("tema") != tema_norm:
            continue
        ts = m.get("ts")
        try:
            ts_f = float(ts)
        except (TypeError, ValueError):
            continue
        if ahora - ts_f > TTL_HISTORIAL_SEG:
            continue
        c = str(m.get("content") or "").strip()
        if c:
            return c
    return None


def intentar_respuesta_cache_tutor(
    *,
    tema_seleccionado: Optional[str],
    pregunta: str,
    historial_previo: list[dict[str, Any]],
    sanitizar_salida_gemini_para_pdf: Callable[[Optional[str]], str],
) -> Optional[tuple[str, str]]:
    """
    Si hay hit en catálogo maestro o historial reciente, devuelve
    ``(texto_listo_para_mostrar_y_pdf, origen)`` con ``origen`` en ``maestra`` | ``historial``.
    En caso contrario devuelve ``None`` (debe llamarse a la API).
    """
    fp = firma_pregunta(pregunta)
    if not fp:
        return None
    tema_norm = normalizar_tema_seleccionado(tema_seleccionado)
    ahora = time.time()

    raw: Optional[str] = None
    origen = ""
    ma = _buscar_maestro(tema_norm, fp) if tema_norm else _buscar_maestro("", fp)
    if ma is not None:
        raw = ma
        origen = "maestra"
    else:
        hist = _buscar_en_historial(historial_previo, tema_norm=tema_norm, fp=fp, ahora=ahora)
        if hist is not None:
            raw = hist
            origen = "historial"

    if not raw:
        return None

    personalizado = personalizar_nombre(raw)
    limpio = sanitizar_salida_gemini_para_pdf(personalizado)
    if not (limpio or "").strip():
        return None
    return (limpio, origen)


def meta_mensaje_tutor(tema_seleccionado: Optional[str], pregunta: str) -> dict[str, Any]:
    """Metadatos a guardar junto a cada mensaje del chat (usuario o asistente) para el cache."""
    return {
        "tema": normalizar_tema_seleccionado(tema_seleccionado),
        "q_firma": firma_pregunta(pregunta),
        "ts": time.time(),
    }
