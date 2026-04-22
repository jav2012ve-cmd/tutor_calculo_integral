"""
Texto legible para PDF con **fpdf2** (import ``from fpdf import FPDF``): Unicode + latin-1 de respaldo.
"""

from __future__ import annotations

import re
from typing import Optional

# Dígitos en superíndice Unicode (0–9)
_SUP_DIG: str = "⁰¹²³⁴⁵⁶⁷⁸⁹"

# Caracteres que suelen romper Helvetica / latin-1; se sustituyen si no hay fuente Unicode.
_MAP_ASCII_FALLBACK: tuple[tuple[str, str], ...] = (
    ("\u2211", "Sumatoria"),
    ("\u03a3", "Sigma"),
    ("\u222b", " INTEGRAL "),
    ("\u222c", " INTEGRAL_DOBLE "),
    ("\u222d", " INTEGRAL_TRIPLE "),
    ("\u221e", " infinito "),
    ("\u00b7", " * "),
    ("\u22c5", " * "),
    ("\u2212", "-"),
    ("\u00d7", " x "),
    ("\u00f7", " / "),
    ("\u2264", " <= "),
    ("\u2265", " >= "),
    ("\u2260", " != "),
    ("\u2248", " ~ "),
    ("\u2014", "-"),
    ("\u2013", "-"),
    ("\u2018", "'"),
    ("\u2019", "'"),
    ("\u201c", '"'),
    ("\u201d", '"'),
    ("\u2026", "..."),
)


def limpiar_texto_para_pdf(texto: Optional[str]) -> str:
    """
    Convierte texto con fragmentos LaTeX típicos en texto legible para PDF.

    - Elimina delimitadores ``$`` y ``$$``.
    - Sustituye ``\\int`` → ∫, ``\\infty`` → ∞, ``\\Sigma`` → Σ (sustituciones globales con ``re``).
    - Convierte exponentes ``x^{\\wedge}2`` (y ``x^{2}``, ``x^2`` con un dígito) a superíndice Unicode (0–9).
    - Elimina cualquier ``\\`` residual al final.
    - Normaliza con ``encode('utf-8').decode('utf-8')``.
    """
    s = "" if texto is None else str(texto)
    s = re.sub(r"\$\$", "", s)
    s = s.replace("$", "")
    s = re.sub(r"\\int(?![a-zA-Z])", "\u222b", s)
    s = re.sub(r"\\infty(?![a-zA-Z])", "\u221e", s)
    s = re.sub(r"\\Sigma(?![a-zA-Z])", "\u03a3", s)
    s = re.sub(r"\\wedge\b", "^", s)
    s = s.replace("^{\wedge}", "^")
    s = re.sub(r"\^\{\\wedge\}", "^", s)

    def _sup(d: str) -> str:
        return _SUP_DIG[int(d)] if d.isdigit() and len(d) == 1 else d

    s = re.sub(
        r"([A-Za-z0-9])\^\{\\wedge\}([0-9])",
        lambda m: m.group(1) + _sup(m.group(2)),
        s,
    )
    s = re.sub(
        r"([A-Za-z0-9])\^\{([0-9])\}",
        lambda m: m.group(1) + _sup(m.group(2)),
        s,
    )
    s = re.sub(
        r"([A-Za-z0-9])\^([0-9])(?!\d)",
        lambda m: m.group(1) + _sup(m.group(2)),
        s,
    )
    s = re.sub(r"\\", "", s)
    return s.encode("utf-8", errors="surrogatepass").decode("utf-8")


def limpiar_texto_pdf(texto: Optional[str], *, for_pdf_unicode_font: bool = True) -> str:
    """
    Capa sobre ``limpiar_texto_para_pdf``: si no hay fuente Unicode en el PDF,
    sustituye símbolos por palabras antes del paso final UTF-8.
    """
    s = limpiar_texto_para_pdf(texto)
    if not for_pdf_unicode_font:
        s = s.replace("\u222b", " INTEGRAL ")
        s = s.replace("\u221e", " infinito ")
        s = s.replace("\u03a3", " Sigma ")
        s = re.sub(r"\binfinito\b", " infinito ", s, flags=re.IGNORECASE)
    return s.encode("utf-8", errors="surrogatepass").decode("utf-8")


def latex_raw_preprocess(s: str, *, uses_unicode_font: bool) -> str:
    """Preproceso antes de ``_limpiar_latex_comunes_para_pdf`` / ``_sanitizar_para_pdf``."""
    if not s:
        return ""
    return limpiar_texto_pdf(s, for_pdf_unicode_font=uses_unicode_font)


def finalize_pdf_string(s: str, *, uses_unicode_font: bool) -> str:
    """
    Último paso: re-aplica ``limpiar_texto_para_pdf`` y, sin fuente TTF, fuerza latin-1.
    """
    out = (s or "").replace("\x00", "")
    out = limpiar_texto_para_pdf(out)
    if uses_unicode_font:
        out = re.sub(r"[\U00010000-\U0010ffff]", "?", out)
        return out.encode("utf-8", errors="surrogatepass").decode("utf-8")
    for u, asc in _MAP_ASCII_FALLBACK:
        out = out.replace(u, asc)
    return out.encode("latin-1", errors="replace").decode("latin-1")
