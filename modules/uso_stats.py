"""
Contador de accesos anónimo: registra qué módulos se usan y cuántas consultas
hay en cada uno. No identifica al usuario.

Prioridad de almacenamiento:
1. Supabase (PostgREST) si hay SUPABASE_URL + clave service_role — persiste en Streamlit Cloud.
2. Archivo local data/uso_stats.json como respaldo o desarrollo sin Supabase.

Se usa HTTP directo (requests) para no depender del paquete pesado `supabase-py`
(compatible con más versiones de Python, p. ej. 3.14).
"""
from __future__ import annotations

import json
import os
from typing import Optional

import requests

MODULOS = (
    "Entrenamiento",
    "Respuesta Guiada",
    "Quiz",
    "Tutor Preguntas Abiertas",
    "Corrección de Manuscritos",
)

_TABLE_NAME = "app_module_usage"
_RPC_NAME = "increment_module_usage"
_TIMEOUT_SEC = 12


def _ruta_archivo() -> str:
    base = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    carpeta = os.path.join(base, "data")
    os.makedirs(carpeta, exist_ok=True)
    return os.path.join(carpeta, "uso_stats.json")


def _credenciales_supabase() -> tuple[Optional[str], Optional[str]]:
    url = os.environ.get("SUPABASE_URL")
    key = os.environ.get("SUPABASE_SERVICE_ROLE_KEY") or os.environ.get(
        "SUPABASE_KEY"
    )
    if url and key:
        return url.strip(), key.strip()
    try:
        import streamlit as st

        sec = st.secrets
        u = str(sec["SUPABASE_URL"]).strip()
        k = None
        try:
            k = str(sec["SUPABASE_SERVICE_ROLE_KEY"]).strip()
        except (KeyError, TypeError):
            pass
        if not k:
            try:
                k = str(sec["SUPABASE_KEY"]).strip()
            except (KeyError, TypeError):
                pass
        if u and k:
            return u, k
    except Exception:
        pass
    return None, None


def _headers_rest(api_key: str) -> dict[str, str]:
    return {
        "apikey": api_key,
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
        "Accept": "application/json",
    }


def _base_vacia() -> dict[str, int]:
    return {m: 0 for m in MODULOS}


def _cargar_archivo() -> dict[str, int]:
    ruta = _ruta_archivo()
    if not os.path.isfile(ruta):
        return _base_vacia()
    try:
        with open(ruta, "r", encoding="utf-8") as f:
            data = json.load(f)
        for m in MODULOS:
            data.setdefault(m, 0)
        return data
    except (json.JSONDecodeError, OSError):
        return _base_vacia()


def _guardar_archivo(data: dict[str, int]) -> None:
    try:
        with open(_ruta_archivo(), "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
    except OSError:
        pass


def _cargar_supabase() -> Optional[dict[str, int]]:
    url, key = _credenciales_supabase()
    if not url or not key:
        return None
    base = url.rstrip("/")
    endpoint = f"{base}/rest/v1/{_TABLE_NAME}?select=module,count"
    try:
        r = requests.get(endpoint, headers=_headers_rest(key), timeout=_TIMEOUT_SEC)
        if r.status_code != 200:
            return None
        rows = r.json()
        out = _base_vacia()
        for row in rows:
            mod = row.get("module")
            if mod in MODULOS:
                out[mod] = int(row.get("count") or 0)
        return out
    except (requests.RequestException, ValueError, TypeError):
        return None


def _registrar_supabase(modulo: str) -> tuple[bool, Optional[str]]:
    """Devuelve (éxito, mensaje_error) si falla."""
    url, key = _credenciales_supabase()
    if not url or not key:
        return False, None
    base = url.rstrip("/")
    endpoint = f"{base}/rest/v1/rpc/{_RPC_NAME}"
    try:
        r = requests.post(
            endpoint,
            headers={**_headers_rest(key), "Prefer": "return=minimal"},
            json={"p_module": modulo},
            timeout=_TIMEOUT_SEC,
        )
        if r.status_code in (200, 204):
            return True, None
        body = (r.text or "")[:300]
        return False, f"HTTP {r.status_code}: {body}"
    except requests.RequestException as e:
        return False, str(e)


def _session_set_supabase_warn(msg: str) -> None:
    try:
        import streamlit as st

        st.session_state["_uso_stats_supabase_warn"] = msg
    except Exception:
        pass


def _session_clear_supabase_warn() -> None:
    try:
        import streamlit as st

        st.session_state.pop("_uso_stats_supabase_warn", None)
    except Exception:
        pass


def registrar_uso(modulo: str) -> None:
    """
    Incrementa en 1 el contador del módulo indicado.
    No identifica al usuario; solo registra uso anónimo.
    """
    if modulo not in MODULOS:
        return
    url, key = _credenciales_supabase()
    ok, err = _registrar_supabase(modulo)
    if ok:
        _session_clear_supabase_warn()
        return
    if url and key and err:
        _session_set_supabase_warn(
            f"No se pudo guardar el uso en Supabase ({modulo}). {err} "
            "Revisa Secrets (URL + service_role), ejecuta `supabase_grants.sql` y vuelve a desplegar."
        )
    data = _cargar_archivo()
    data[modulo] = data.get(modulo, 0) + 1
    _guardar_archivo(data)


def obtener_estadisticas() -> dict[str, int]:
    """Devuelve los contadores actuales (solo lectura)."""
    remote = _cargar_supabase()
    if remote is not None:
        return remote
    return _cargar_archivo().copy()
