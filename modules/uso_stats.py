"""
Contador de accesos anónimo: registra qué módulos se usan y cuántas consultas
hay en cada uno. No identifica al usuario.

Además, opcionalmente registra un evento detallado en Supabase (tabla
app_usage_event) con JSON: temas, modalidad de quiz, tema detectado, etc.

Prioridad de almacenamiento:
1. Supabase (PostgREST) si hay SUPABASE_URL + clave service_role.
2. Archivo local data/uso_stats.json para contadores; data/usage_events.jsonl
   como respaldo de eventos si Supabase no acepta el detalle.

Se usa HTTP directo (requests).
"""
from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from typing import Any, Optional

import requests

MODULOS = (
    "Entrenamiento",
    "Respuesta Guiada",
    "Quiz",
    "Tutor Preguntas Abiertas",
    "Corrección de Manuscritos",
)

STATS_TEMA_NO_ESPECIFICADO = "(No especificado)"

_TABLE_NAME = "app_module_usage"
_RPC_INCREMENT = "increment_module_usage"
_RPC_INSERT_EVENT = "insert_usage_event"
_TIMEOUT_SEC = 12


def _ruta_archivo() -> str:
    base = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    carpeta = os.path.join(base, "data")
    os.makedirs(carpeta, exist_ok=True)
    return os.path.join(carpeta, "uso_stats.json")


def _ruta_eventos_jsonl() -> str:
    base = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    carpeta = os.path.join(base, "data")
    os.makedirs(carpeta, exist_ok=True)
    return os.path.join(carpeta, "usage_events.jsonl")


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


def _sanitize_payload(d: Any) -> dict[str, Any]:
    """Convierte a estructura JSON-serializable y acota tamaños."""

    def norm(v: Any) -> Any:
        if v is None or isinstance(v, (bool, int, float)):
            return v
        if isinstance(v, str):
            return v[:2000]
        if isinstance(v, list):
            out = []
            for x in v[:80]:
                if isinstance(x, dict):
                    out.append(_sanitize_payload(x))
                else:
                    out.append(norm(x))
            return out
        if isinstance(v, dict):
            return _sanitize_payload(v)
        return str(v)[:500]

    if not isinstance(d, dict):
        return {}
    return {str(k)[:120]: norm(val) for k, val in d.items()}


def _append_evento_local(modo: str, detalle: dict[str, Any]) -> None:
    try:
        line = json.dumps(
            {
                "ts": datetime.now(timezone.utc).isoformat(),
                "modo": modo,
                "payload": _sanitize_payload(detalle),
            },
            ensure_ascii=False,
        )
        with open(_ruta_eventos_jsonl(), "a", encoding="utf-8") as f:
            f.write(line + "\n")
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
    url, key = _credenciales_supabase()
    if not url or not key:
        return False, None
    base = url.rstrip("/")
    endpoint = f"{base}/rest/v1/rpc/{_RPC_INCREMENT}"
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


def _insert_event_supabase(modulo: str, payload: dict[str, Any]) -> tuple[bool, Optional[str]]:
    url, key = _credenciales_supabase()
    if not url or not key:
        return False, None
    base = url.rstrip("/")
    endpoint = f"{base}/rest/v1/rpc/{_RPC_INSERT_EVENT}"
    clean = _sanitize_payload(payload)
    try:
        r = requests.post(
            endpoint,
            headers={**_headers_rest(key), "Prefer": "return=minimal"},
            json={"p_modo": modulo, "p_payload": clean},
            timeout=_TIMEOUT_SEC,
        )
        if r.status_code in (200, 204):
            return True, None
        body = (r.text or "")[:400]
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


def registrar_uso(modulo: str, detalle: Optional[dict[str, Any]] = None) -> None:
    """
    Incrementa el contador del módulo y, si se pasa ``detalle``, inserta un
    evento en ``app_usage_event`` (requiere ejecutar ``supabase_usage_events.sql``).
    """
    if modulo not in MODULOS:
        return
    url, key = _credenciales_supabase()
    ok_inc, err_inc = _registrar_supabase(modulo)
    if ok_inc:
        _session_clear_supabase_warn()
    elif url and key and err_inc:
        _session_set_supabase_warn(
            f"No se pudo guardar el contador en Supabase ({modulo}). {err_inc} "
            "Revisa Secrets y `supabase_schema.sql` / `supabase_grants.sql`."
        )

    if not ok_inc:
        data = _cargar_archivo()
        data[modulo] = data.get(modulo, 0) + 1
        _guardar_archivo(data)

    if detalle:
        if url and key:
            ok_ev, _err_ev = _insert_event_supabase(modulo, detalle)
            if not ok_ev:
                _append_evento_local(modulo, detalle)
        else:
            _append_evento_local(modulo, detalle)


def obtener_estadisticas() -> dict[str, int]:
    """Devuelve los contadores actuales (solo lectura)."""
    remote = _cargar_supabase()
    if remote is not None:
        return remote
    return _cargar_archivo().copy()
