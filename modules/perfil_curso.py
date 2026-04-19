"""
Perfil de temario activo en la app.

La lista histórica ``temario.LISTA_TEMAS`` (Σigma / banco actual) queda reservada al caso
**UCAB · Economía · Matemáticas III**. El resto de universidades/carreras usan el orden atómico
del minicurso inferido por institución o el elegido explícitamente en Ruta Maestra.
"""

from __future__ import annotations

from typing import Any, Optional


def _st_session_get(key: str) -> Any:
    try:
        import streamlit as st

        return st.session_state.get(key)
    except Exception:
        return None


def es_ucab_economia_matematicas_iii() -> bool:
    """
    True si el perfil de sesión corresponde a UCAB Economía cursando Matemáticas III
    (temario canónico ``LISTA_TEMAS`` / banco Σigma actual).
    """
    inst = (_st_session_get("auth_estudiante_institucion") or "")
    car = (_st_session_get("auth_estudiante_carrera") or "")
    if not isinstance(inst, str) or not isinstance(car, str):
        return False
    inst_l = inst.strip().lower()
    car_l = car.strip().lower()
    if not inst_l or not car_l:
        return False
    ucab = (
        "ucab" in inst_l
        or "andrés bello" in inst_l
        or "andres bello" in inst_l
        or ("católica" in inst_l and "bello" in inst_l)
        or ("catolica" in inst_l and "bello" in inst_l)
    )
    if not ucab:
        return False
    if "econom" not in car_l:
        return False
    if "matemáticas iii" in car_l or "matematicas iii" in car_l or "matemática iii" in car_l or "matematica iii" in car_l:
        return True
    if "mat iii" in car_l or "mat. iii" in car_l:
        return True
    if ("matemática" in car_l or "matematica" in car_l) and (" iii" in car_l or car_l.endswith(" iii")):
        return True
    if ("matemática" in car_l or "matematica" in car_l) and (" 3" in car_l or " iii" in car_l):
        return True
    if _st_session_get("sigma_forzar_lista_ucab_econ_mat3"):
        return True
    return False


def _atomos_explicitos_sesion() -> Optional[list[str]]:
    v = _st_session_get("sigma_atomos_malla_activa")
    if not isinstance(v, list) or not v:
        return None
    out = [str(x).strip() for x in v if str(x).strip()]
    return out or None


def lista_temas_activa() -> list[str]:
    """
    Temas que alimentan selectores, normalización y seguimiento 5+5.

    - UCAB Economía Mat III → ``temario.LISTA_TEMAS`` (banco / prompts históricos).
    - Resto → átomos del minicurso elegido en sesión, o inferidos por institución.
    """
    if es_ucab_economia_matematicas_iii():
        from modules import temario

        return list(temario.LISTA_TEMAS)

    ex = _atomos_explicitos_sesion()
    if ex:
        return ex

    from modules.minicurso_catalogo import (
        inferir_indice_por_institucion,
        listar_entradas_minicurso_v2,
        orden_temario_desde_entrada,
    )

    entradas = listar_entradas_minicurso_v2()
    if not entradas:
        return []
    inst = (_st_session_get("auth_estudiante_institucion") or "")
    inst_s = inst.strip() if isinstance(inst, str) else ""
    if not inst_s:
        return []
    ix = inferir_indice_por_institucion(inst_s, entradas)
    return orden_temario_desde_entrada(entradas, ix)


def lista_temas_para_metricas_agregadas() -> list[str]:
    """
    Temas base para tablas agregadas (admin / uso) cuando no hay sesión Streamlit
    o la lista activa viene vacía: evita romper paneles.
    """
    try:
        lt = lista_temas_activa()
        if lt:
            return lt
    except Exception:
        pass
    from modules import temario

    return list(temario.LISTA_TEMAS)
