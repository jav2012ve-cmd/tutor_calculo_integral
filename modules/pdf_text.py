"""
Texto seguro para exportación PDF (fpdf 1.x con fuentes TTF uni=True o Helvetica latin-1).
"""

from __future__ import annotations

import re

# Caracteres que suelen romper Helvetica / latin-1; se sustituyen si no hay fuente Unicode.
_MAP_ASCII_FALLBACK: tuple[tuple[str, str], ...] = (
    ("\u2211", "Sumatoria"),  # ∑ n-ary summation
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


def latex_raw_preprocess(s: str, *, uses_unicode_font: bool) -> str:
    """
    Sustituciones de LaTeX “crudo” antes del resto del pipeline (``_sanitizar_para_pdf``).
    - ``^{\\wedge}`` / ``^{\\wedge}`` → ``^``
    - ``\\int`` → símbolo de integral (Unicode) si hay fuente TTF; si no, la palabra INTEGRAL.
    """
    if not s:
        return ""
    t = s.replace("^{\wedge}", "^")
    t = re.sub(r"\^\{\\wedge\}", "^", t)
    rep_int = "\u222b" if uses_unicode_font else " INTEGRAL "
    t = re.sub(r"\\int\b", rep_int, t)
    return t


def finalize_pdf_string(s: str, *, uses_unicode_font: bool) -> str:
    """
    Sustituye símbolos problemáticos y, como último recurso, fuerza latin-1 cuando no hay fuente Unicode.
    Con fuente TTF (uni=True) se conserva Unicode salvo NUL y puntos de código muy altos.
    """
    out = (s or "").replace("\x00", "")
    if uses_unicode_font:
        out = re.sub(r"[\U00010000-\U0010ffff]", "?", out)
        return out
    for u, asc in _MAP_ASCII_FALLBACK:
        out = out.replace(u, asc)
    return out.encode("latin-1", "replace").decode("latin-1")
