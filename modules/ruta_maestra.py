"""
Ruta Maestra Σigma: itinerario por malla universitaria (JSON en ``data/minicurso_*.json``).

Cruza el orden atómico del pensum con eventos de ``app_usage_event`` cuando hay sesión.
"""

from __future__ import annotations

import json
import os
import re
from typing import Any, Optional

import streamlit as st

from modules import contexto_universitario, seguimos_curso, temario

_ATOM_CODE_RE = re.compile(r"^(\d+(?:\.\d+)*)\b")

HITOS_ORDEN: tuple[tuple[str, str], ...] = (
    ("fund", "Fundamentos de Integración"),
    ("apps", "Aplicaciones Geométricas"),
    ("series", "El Reto de las Series"),
    ("ed", "Modelado con ED"),
)

# Tips breves por clave de universidad (perfil de rigor / examen típico).
TIPS_POR_UNIVERSIDAD: dict[str, str] = {
    "UCV": "Tip UCV: en varios temas suelen exigir la demostración formal del teorema fundamental y el rigor en límites del integral de Riemann.",
    "USB": "Tip USB: el ritmo trimestral premia automatizar técnicas de integración y plantear aplicaciones físicas con rapidez.",
    "UNIMET": "Tip UNIMET: conecta siempre integración con modelado (excedentes, costos, balances) cuando prepares el simulacro.",
    "ULA": "Tip ULA: en Series, practica criterios de convergencia con justificación paso a paso; suele ponderarse fuerte en el segundo parcial.",
    "LUZ": "Tip LUZ: coordenadas polares y trazado de curvas suelen ser bloque propio; repasa rosas, lemniscatas y cardioides con gráficas.",
    "UC": "Tip UC (Carabobo): equilibra teoría y EDO lineales; revisa el enunciado tipo examen antes de abreviar pasos.",
    "UNEXPO": "Tip UNEXPO (p. ej. Barquisimeto): aplicaciones tipo Pappus, presión hidrostática y ED especiales (Bernoulli/Riccati); no omitas enunciados con contexto mecánico.",
    "UDO": "Tip UDO: enlaza aplicaciones de ingeniería de procesos con el planteamiento de ED; el enunciado suele ser contextualizado.",
    "UNELLEZ": "Tip UNELLEZ: refuerza modelado poblacional y volúmenes de revolución como puente hacia ED.",
    "UBV": "Tip UBV PFG: prioriza interpretación física (presión, mezclas, almacenamiento) al validar integrales y ED.",
    "UCLA": "Tip UCLA: mantén orden en integración por partes y en volúmenes; el DCyT suele valorar el planteamiento explícito.",
    "UCAB": "Tip UCAB: practica el simulacro mezclando series con aplicaciones geométricas según tu malla FING.",
    "UMA": "Tip UMA: articula finanzas y probabilidad con el temario de integrales cuando el curso lo exija.",
}

HORAS_DEFECTO_ATOMO = 4.0


def _raiz_proyecto() -> str:
    return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def _parse_payload_row(row: dict[str, Any]) -> dict[str, Any]:
    pl = row.get("payload")
    if isinstance(pl, dict):
        return pl
    if isinstance(pl, str) and pl.strip():
        try:
            o = json.loads(pl)
            return o if isinstance(o, dict) else {}
        except json.JSONDecodeError:
            return {}
    return {}


def codigo_atomico(atom: str) -> str:
    m = _ATOM_CODE_RE.match((atom or "").strip())
    return m.group(1) if m else ""


def hito_para_atomo(atom: str) -> tuple[str, str]:
    """Devuelve (id_hito, etiqueta legible)."""
    s = (atom or "").strip().lower()
    code = codigo_atomico(atom)
    parts = code.split(".") if code else []
    try:
        major = int(parts[0]) if parts else 0
    except ValueError:
        major = 0

    series_kw = (
        "serie",
        "convergencia",
        "taylor",
        "sucesión",
        "sucesiones",
        "dirichlet",
        "abel",
        "potencias",
        "criterios",
        "numérica",
    )
    ed_kw = (
        " ed:",
        "bernoulli",
        "riccati",
        "variables separables",
        "lineales de primer",
        "lineal de primer",
        "modelado poblacional",
        "mezclas y ambiental",
        "ecuación diferencial",
        "ecuaciones diferencial",
        "orden superior",
        "homogéneas",
        "exactas",
    )
    apps_kw = (
        "volumen",
        "revolución",
        "masa",
        "centro",
        "centroid",
        "pappus",
        "hidrostát",
        "polar",
        "polares",
        "cardioide",
        "almacenamiento",
        "presión",
        "excedente",
        "área",
    )

    if any(k in s for k in ed_kw):
        return ("ed", "Modelado con ED")
    if any(k in s for k in series_kw):
        return ("series", "El Reto de las Series")
    if major >= 6:
        return ("ed", "Modelado con ED")
    if major == 5 and any(k in s for k in series_kw):
        return ("series", "El Reto de las Series")
    if major == 5:
        return ("ed", "Modelado con ED")
    if major == 4:
        if any(k in s for k in ("polar", "polares", "cardioide", "rosa")):
            return ("apps", "Aplicaciones Geométricas")
        return ("series", "El Reto de las Series")
    if major in (2, 3) or any(k in s for k in apps_kw):
        return ("apps", "Aplicaciones Geométricas")
    if major == 1 or not code:
        return ("fund", "Fundamentos de Integración")
    return ("fund", "Fundamentos de Integración")


def listar_entradas_minicurso_v2() -> list[dict[str, Any]]:
    """Cada entrada: path, label, data (dict del JSON)."""
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


def horas_para_atomo(data: dict[str, Any], atom: str) -> float:
    hmap = data.get("horas_orientativas_por_atomico")
    if isinstance(hmap, dict) and atom in hmap:
        try:
            return float(hmap[atom])
        except (TypeError, ValueError):
            pass
    return HORAS_DEFECTO_ATOMO


def total_horas_ruta(data: dict[str, Any]) -> float:
    orden = data.get("orden_temario_atomico")
    if not isinstance(orden, list):
        return 0.0
    return round(sum(horas_para_atomo(data, str(a)) for a in orden if str(a).strip()), 1)


def _tema_coincide_atomo(tema_raw: str, atom: str, code: str) -> bool:
    if not tema_raw or not atom:
        return False
    tl = tema_raw.lower()
    al = atom.lower()
    if code:
        if code.lower() in tl:
            return True
        for t_of in temario.LISTA_TEMAS:
            if t_of.lower() == tl or tl in t_of.lower():
                if code in t_of:
                    return True
    for pal in al.split()[1:]:
        p = re.sub(r"[^\wáéíóúñü]+", "", pal, flags=re.I)
        if len(p) > 3 and p in tl:
            return True
    return False


def conteos_actividad_sobre_atomo(eventos: list[dict[str, Any]], atom: str) -> dict[str, int]:
    code = codigo_atomico(atom)
    pr = q_ok = 0
    for row in eventos:
        modo = (row.get("modo") or "").strip()
        pl = _parse_payload_row(row)
        tema = str(pl.get("tema") or pl.get("tema_catedra") or "")
        if not _tema_coincide_atomo(tema, atom, code):
            continue
        if modo == "Entrenamiento" and pl.get("tipo_evento") == seguimos_curso.EVENTO_PRACTICA_OK:
            pr += 1
        elif modo == "Quiz" and pl.get("tipo_evento") == seguimos_curso.EVENTO_QUIZ_OK:
            q_ok += 1
    return {"practica_ok": pr, "quiz_ok": q_ok}


def atomo_dominado_app(
    eventos: list[dict[str, Any]],
    atom: str,
    *,
    conteos_canon: Optional[dict[str, dict[str, int]]] = None,
) -> bool:
    """True si hay evidencia fuerte (5+5) en temas canónicos mapeables o en coincidencia fuzzy."""
    cont = conteos_actividad_sobre_atomo(eventos, atom)
    if cont["practica_ok"] >= seguimos_curso.META_PRACTICA and cont["quiz_ok"] >= seguimos_curso.META_QUIZ:
        return True
    cc = conteos_canon if conteos_canon is not None else seguimos_curso.conteos_minicurso_por_tema(eventos)
    code = codigo_atomico(atom)
    for t in temario.LISTA_TEMAS:
        if code and code in t:
            slots = cc.get(t, {"practica_ok": 0, "quiz_ok": 0})
            if seguimos_curso.tema_superado(slots):
                return True
    return False


def perfil_rigor_lineas(data: dict[str, Any], max_items: int = 6) -> list[str]:
    orden = data.get("orden_temario_atomico")
    if not isinstance(orden, list):
        return []
    out: list[str] = []
    for a in orden:
        s = str(a).strip()
        if s:
            out.append(s)
    return out[:max_items]


def narrativa_dominio(nombre: str, data: dict[str, Any], total_h: float) -> str:
    nom = (nombre or "estudiante").strip() or "estudiante"
    clave = (data.get("universidad_clave") or "").strip()
    curso = (data.get("curso_codigo") or "").strip()
    fac = (data.get("carrera_nombre_oficial") or "").strip()
    orden = data.get("orden_temario_atomico")
    atoms = [str(x).strip() for x in orden] if isinstance(orden, list) else []
    series_atoms = [
        a
        for a in atoms
        if any(k in a.lower() for k in ("serie", "convergencia", "taylor", "suces"))
    ]
    conv_atoms = [a for a in atoms if "convergencia" in a.lower()]

    curso_txt = f"**{curso}**" if curso else "este curso de Cálculo integral"
    fac_txt = f" ({fac})" if fac else ""

    p_series = ""
    if series_atoms:
        ej = series_atoms[0]
        p_series = (
            f"Tu **segundo parcial** suele apoyarse fuerte en **Series** y temas afines; "
            f"por ejemplo **{ej}** es un bloque típico de esa evaluación. "
        )
        if conv_atoms and clave.upper() == "ULA":
            p_series += (
                "En la práctica docente de la ULA, **los criterios de convergencia** suelen concentrar "
                "una parte **muy relevante** del examen (del orden del **40%** cuando el banco privilegia Series). "
            )
        elif conv_atoms:
            p_series += (
                "**Los criterios de convergencia** suelen concentrar una parte relevante del examen cuando el parcial es de Series. "
            )

    return (
        f"Hola **{nom}**, detectamos que cursas {curso_txt} en **{clave}**{fac_txt}. "
        f"{p_series}"
        f"Hemos diseñado esta **Ruta Maestra** de **{total_h:g} h** de inversión estimada "
        f"(según el programa y las horas orientativas de tu malla) para ordenar tu estudio con el rigor de tu facultad."
    )


def tip_universidad(clave: str) -> Optional[str]:
    c = (clave or "").strip().upper()
    return TIPS_POR_UNIVERSIDAD.get(c)


def render_panel_ruta_maestra(
    *,
    nombre: str,
    eventos: list[dict[str, Any]],
    sesion_supabase: bool,
) -> None:
    st.markdown("### Tu Ruta Maestra Σigma")
    st.markdown(
        "<div style='color:#1e293b;font-size:1.02rem;line-height:1.55;margin-bottom:0.9rem;'>"
        "Itinerario por **tu pensum** (datos oficiales mapeados por universidad y carrera). "
        "La columna de horas resume la **inversión estimada** por ítem atómico; la cobertura cruza lo que ya registraste "
        "en **A practicar** y **Simulacro** cuando el tema coincide con el banco Σigma."
        "</div>",
        unsafe_allow_html=True,
    )

    entradas = listar_entradas_minicurso_v2()
    if not entradas:
        st.warning("No hay archivos `minicurso_*.json` (schema 2) en `data/`.")
        return

    labels = [e["label"] for e in entradas]
    auth_inst = (st.session_state.get("auth_estudiante_institucion") or "").strip()
    default_ix = inferir_indice_por_institucion(auth_inst, entradas) if auth_inst else 0

    ix = st.selectbox(
        "Universidad y programa (pensum)",
        range(len(labels)),
        format_func=lambda i: labels[i],
        index=default_ix,
        key="ruta_maestra_select_malla",
    )
    entry = entradas[int(ix)]
    data = entry["data"]
    clave_u = (data.get("universidad_clave") or "").strip()

    orden = [str(x).strip() for x in data.get("orden_temario_atomico", []) if str(x).strip()]
    if not orden:
        st.error("Este archivo no define `orden_temario_atomico`.")
        return

    conteos_canon = seguimos_curso.conteos_minicurso_por_tema(eventos) if sesion_supabase else {}

    total_h = total_horas_ruta(data)
    st.markdown(narrativa_dominio(nombre, data, total_h))

    tip = tip_universidad(clave_u)
    if tip:
        st.info(tip)

    # Agrupar por hito
    buckets: dict[str, list[str]] = {hid: [] for hid, _ in HITOS_ORDEN}
    for atom in orden:
        hid, _ = hito_para_atomo(atom)
        if hid not in buckets:
            hid = "fund"
        buckets[hid].append(atom)

    st.markdown("#### Línea de tiempo sugerida (hitos)")
    for hid, titulo in HITOS_ORDEN:
        atoms = buckets.get(hid) or []
        if not atoms:
            continue
        subh = sum(horas_para_atomo(data, a) for a in atoms)
        with st.expander(f"**{titulo}** · ~{subh:g} h", expanded=(hid == "fund")):
            for atom in atoms:
                h = horas_para_atomo(data, atom)
                dom = (
                    atomo_dominado_app(eventos, atom, conteos_canon=conteos_canon)
                    if sesion_supabase
                    else False
                )
                c1, c2 = st.columns((4, 1))
                with c1:
                    if dom:
                        st.markdown(f"✅ **{atom}**")
                    else:
                        st.markdown(
                            f"<span style='color:#b91c1c;font-weight:600;'>▸ Falta por dominar:</span> **{atom}**",
                            unsafe_allow_html=True,
                        )
                with c2:
                    st.caption(f"{h:g} h")
            st.caption(
                "«Falta por dominar» = aún no alcanzas la meta de evidencia en la app "
                f"({seguimos_curso.META_PRACTICA} prácticas + {seguimos_curso.META_QUIZ} aciertos en simulacro) "
                "en ejercicios etiquetados con ese tema o código."
            )

    st.markdown("##### Perfil de rigor (temas distintivos de tu malla)")
    for linea in perfil_rigor_lineas(data):
        st.markdown(f"- {linea}")

    if data.get("notas"):
        st.caption(str(data["notas"]))

    if not sesion_supabase:
        st.info("Inicia sesión para **cruzar** esta ruta con tus eventos reales de práctica y simulacro.")
