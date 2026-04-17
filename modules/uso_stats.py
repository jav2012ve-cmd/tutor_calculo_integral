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
import urllib.parse
from datetime import datetime, timezone
from typing import Any, Optional
from uuid import UUID

import requests

from modules import temario

MODULOS = (
    "Seguimos",
    "Entrenamiento",
    "Respuesta Guiada",
    "Quiz",
    "Tutor Preguntas Abiertas",
    "Corrección de Manuscritos",
)

STATS_TEMA_NO_ESPECIFICADO = "(No especificado)"

_TABLE_NAME = "app_module_usage"
_TABLE_TOPIC = "app_topic_usage"
_TABLE_USAGE_EVENT = "app_usage_event"
_RPC_INCREMENT = "increment_module_usage"
_RPC_INSERT_EVENT = "insert_usage_event"
_RPC_TOPICS_BATCH = "increment_topic_usage_batch"
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


def _ruta_topic_archivo() -> str:
    base = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    carpeta = os.path.join(base, "data")
    os.makedirs(carpeta, exist_ok=True)
    return os.path.join(carpeta, "topic_usage.json")


def _str_credencial(val: Any) -> Optional[str]:
    if val is None:
        return None
    s = str(val).strip()
    return s if s else None


def _credenciales_desde_mapping(m: Any) -> tuple[Optional[str], Optional[str]]:
    """Lee URL y clave desde un dict-like (p. ej. st.secrets o sección [supabase])."""
    if m is None:
        return None, None
    get = getattr(m, "get", None)
    if not callable(get):
        return None, None
    u = _str_credencial(get("SUPABASE_URL")) or _str_credencial(get("url"))
    k = (
        _str_credencial(get("SUPABASE_SERVICE_ROLE_KEY"))
        or _str_credencial(get("SUPABASE_KEY"))
        or _str_credencial(get("service_role_key"))
    )
    return u, k


def _credenciales_supabase() -> tuple[Optional[str], Optional[str]]:
    """
    Prioridad: st.secrets (Cloud / .streamlit/secrets.toml), luego variables de entorno.
    Acepta:
    - Claves planas: SUPABASE_URL / SUPABASE_SERVICE_ROLE_KEY
    - Sección TOML [supabase] con url / service_role_key
    - Streamlit Connections: [connections.supabase] con url/key o SUPABASE_URL/SUPABASE_SERVICE_ROLE_KEY
    """
    try:
        import streamlit as st

        sec = st.secrets
        u, k = _credenciales_desde_mapping(sec)
        if not u or not k:
            sec_get = getattr(sec, "get", None)
            sub = sec_get("supabase") if callable(sec_get) else None
            u2, k2 = _credenciales_desde_mapping(sub)
            u = u or u2
            k = k or k2
        if not u or not k:
            sec_get = getattr(sec, "get", None)
            conns = sec_get("connections") if callable(sec_get) else None
            conns_get = getattr(conns, "get", None)
            sb = conns_get("supabase") if callable(conns_get) else None
            sb_get = getattr(sb, "get", None)
            if callable(sb_get):
                u3 = _str_credencial(sb_get("SUPABASE_URL")) or _str_credencial(sb_get("url"))
                k3 = (
                    _str_credencial(sb_get("SUPABASE_SERVICE_ROLE_KEY"))
                    or _str_credencial(sb_get("service_role_key"))
                    or _str_credencial(sb_get("SUPABASE_KEY"))
                    or _str_credencial(sb_get("key"))
                )
                u = u or u3
                k = k or k3
        if u and k:
            return u, k
    except Exception:
        pass

    url = _str_credencial(os.environ.get("SUPABASE_URL"))
    key = _str_credencial(os.environ.get("SUPABASE_SERVICE_ROLE_KEY")) or _str_credencial(
        os.environ.get("SUPABASE_KEY")
    )
    if url and key:
        return url, key
    return None, None


def diagnostico_supabase() -> dict[str, Any]:
    """
    Diagnóstico seguro (sin exponer secretos): indica si se detectó URL/KEY y desde dónde.
    Útil para depurar Streamlit Cloud Secrets (TOML vs nombres de variables).
    """
    diag: dict[str, Any] = {
        "ok": False,
        "url_presente": False,
        "key_presente": False,
        "fuente": None,  # "secrets_plano" | "secrets_supabase" | "secrets_connections" | "env" | None
        "nombre_key": None,  # "SUPABASE_SERVICE_ROLE_KEY" | "SUPABASE_KEY" | "service_role_key" | None
        "url_host": None,
    }

    # 1) Streamlit secrets
    try:
        import streamlit as st

        sec = st.secrets
        sec_get = getattr(sec, "get", None)
        u1 = _str_credencial(sec_get("SUPABASE_URL")) if callable(sec_get) else None
        k1 = None
        if callable(sec_get):
            for cand in ("SUPABASE_SERVICE_ROLE_KEY", "SUPABASE_KEY", "service_role_key"):
                k1 = _str_credencial(sec_get(cand))
                if k1:
                    diag["nombre_key"] = cand
                    break
        if u1 or k1:
            diag["fuente"] = "secrets_plano"
            diag["url_presente"] = bool(u1)
            diag["key_presente"] = bool(k1)

        sub = sec_get("supabase") if callable(sec_get) else None
        sub_get = getattr(sub, "get", None)
        u2 = _str_credencial(sub_get("SUPABASE_URL")) if callable(sub_get) else None
        if not u2 and callable(sub_get):
            u2 = _str_credencial(sub_get("url"))
        k2 = None
        if callable(sub_get):
            for cand in ("SUPABASE_SERVICE_ROLE_KEY", "SUPABASE_KEY", "service_role_key"):
                k2 = _str_credencial(sub_get(cand))
                if k2:
                    diag["nombre_key"] = cand
                    break
        if u2 or k2:
            diag["fuente"] = "secrets_supabase"
            diag["url_presente"] = bool(u2)
            diag["key_presente"] = bool(k2)

        u = u2 or u1
        k = k2 or k1
        if not u or not k:
            conns = sec_get("connections") if callable(sec_get) else None
            conns_get = getattr(conns, "get", None)
            sb = conns_get("supabase") if callable(conns_get) else None
            sb_get = getattr(sb, "get", None)
            u3 = None
            k3 = None
            if callable(sb_get):
                u3 = _str_credencial(sb_get("SUPABASE_URL")) or _str_credencial(sb_get("url"))
                for cand in (
                    "SUPABASE_SERVICE_ROLE_KEY",
                    "service_role_key",
                    "SUPABASE_KEY",
                    "key",
                ):
                    k3 = _str_credencial(sb_get(cand))
                    if k3:
                        diag["nombre_key"] = cand
                        break
            if u3 or k3:
                diag["fuente"] = "secrets_connections"
                diag["url_presente"] = bool(u3)
                diag["key_presente"] = bool(k3)
            u = u or u3
            k = k or k3
        if u:
            # Extrae host sin librerías extra; no incluye tokens.
            try:
                host = str(u).split("://", 1)[-1].split("/", 1)[0]
                diag["url_host"] = host[:120]
            except Exception:
                pass
        if u and k:
            diag["ok"] = True
            return diag
    except Exception:
        pass

    # 2) Environment
    uenv = _str_credencial(os.environ.get("SUPABASE_URL"))
    kenv = _str_credencial(os.environ.get("SUPABASE_SERVICE_ROLE_KEY")) or _str_credencial(
        os.environ.get("SUPABASE_KEY")
    )
    if uenv or kenv:
        diag["fuente"] = "env"
        diag["url_presente"] = bool(uenv)
        diag["key_presente"] = bool(kenv)
        if uenv:
            try:
                host = str(uenv).split("://", 1)[-1].split("/", 1)[0]
                diag["url_host"] = host[:120]
            except Exception:
                pass
        if uenv and kenv:
            diag["ok"] = True
    return diag


def _headers_rest(api_key: str) -> dict[str, str]:
    return {
        "apikey": api_key,
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
        "Accept": "application/json",
    }


def supabase_url_y_clave() -> tuple[Optional[str], Optional[str]]:
    """URL y clave service_role (o SUPABASE_KEY) para llamadas REST desde otros módulos."""
    return _credenciales_supabase()


def headers_supabase_rest(api_key: str) -> dict[str, str]:
    """Encabezados estándar PostgREST (reutilizable fuera de este módulo)."""
    return _headers_rest(api_key)


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


def _extraer_topic_keys_validos(
    modulo: str, detalle: Optional[dict[str, Any]]
) -> list[str]:
    """Temas del temario presentes en ``detalle`` (uno o varios), sin duplicados."""
    if not detalle:
        return []
    valid = set(temario.LISTA_TEMAS)
    raw: list[str] = []
    if modulo in ("Entrenamiento", "Quiz"):
        for x in detalle.get("temas") or []:
            if isinstance(x, str) and x.strip() in valid:
                raw.append(x.strip())
    elif modulo == "Respuesta Guiada":
        t = temario.normalizar_tema_curso(detalle.get("tema_detectado"))
        if t:
            raw.append(t)
    elif modulo in ("Tutor Preguntas Abiertas", "Corrección de Manuscritos"):
        t = temario.normalizar_tema_curso(detalle.get("tema_catedra"))
        if t:
            raw.append(t)
    seen: set[str] = set()
    out: list[str] = []
    for t in raw:
        if t not in seen:
            seen.add(t)
            out.append(t)
    return out


def _increment_topics_supabase(topics: list[str]) -> bool:
    if not topics:
        return True
    url, key = _credenciales_supabase()
    if not url or not key:
        return False
    base = url.rstrip("/")
    endpoint = f"{base}/rest/v1/rpc/{_RPC_TOPICS_BATCH}"
    try:
        r = requests.post(
            endpoint,
            headers={**_headers_rest(key), "Prefer": "return=minimal"},
            json={"p_topics": topics},
            timeout=_TIMEOUT_SEC,
        )
        return r.status_code in (200, 204)
    except requests.RequestException:
        return False


def _increment_topics_local(topics: list[str]) -> None:
    path = _ruta_topic_archivo()
    data: dict[str, int] = {}
    if os.path.isfile(path):
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
        except (json.JSONDecodeError, OSError):
            data = {}
    for t in topics:
        data[t] = int(data.get(t, 0) or 0) + 1
    try:
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
    except OSError:
        pass


def _obtener_estudiante_id_sesion_para_evento() -> Optional[str]:
    """UUID del participante autenticado para asociar eventos (opcional)."""
    try:
        import streamlit as st

        sid = st.session_state.get("auth_estudiante_id")
        if not sid:
            return None
        s = str(sid).strip()
        UUID(s)
        return s
    except Exception:
        return None


def _insert_event_supabase(modulo: str, payload: dict[str, Any]) -> tuple[bool, Optional[str]]:
    url, key = _credenciales_supabase()
    if not url or not key:
        return False, None
    base = url.rstrip("/")
    endpoint = f"{base}/rest/v1/rpc/{_RPC_INSERT_EVENT}"
    clean = _sanitize_payload(payload)
    body: dict[str, Any] = {"p_modo": modulo, "p_payload": clean}
    est_id = _obtener_estudiante_id_sesion_para_evento()
    if est_id:
        body["p_estudiante_id"] = est_id
    try:
        r = requests.post(
            endpoint,
            headers={**_headers_rest(key), "Prefer": "return=minimal"},
            json=body,
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


def registrar_evento_aprendizaje(modulo: str, detalle: dict[str, Any]) -> None:
    """
    Inserta solo un evento en ``app_usage_event`` (sin incrementar contador de módulo
    ni conteos por tema). Útil para señales finas (p. ej. respuesta incorrecta en Quiz).
    """
    if modulo not in MODULOS:
        return
    url, key = _credenciales_supabase()
    if url and key:
        ok_ev, _err_ev = _insert_event_supabase(modulo, detalle)
        if not ok_ev:
            _append_evento_local(modulo, detalle)
    else:
        _append_evento_local(modulo, detalle)


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

    topic_keys = _extraer_topic_keys_validos(modulo, detalle)
    if topic_keys:
        if url and key:
            if not _increment_topics_supabase(topic_keys):
                _increment_topics_local(topic_keys)
        else:
            _increment_topics_local(topic_keys)


def obtener_estadisticas() -> dict[str, int]:
    """Devuelve los contadores actuales (solo lectura)."""
    remote = _cargar_supabase()
    if remote is not None:
        return remote
    return _cargar_archivo().copy()


def obtener_estadisticas_temas() -> dict[str, int]:
    """
    Conteos por tema del temario (0 si no hay registro).
    Origen: Supabase ``app_topic_usage`` o archivo local ``data/topic_usage.json``.
    """
    base: dict[str, int] = {t: 0 for t in temario.LISTA_TEMAS}
    url, key = _credenciales_supabase()
    if url and key:
        try:
            b = url.rstrip("/")
            endpoint = f"{b}/rest/v1/{_TABLE_TOPIC}?select=topic_key,count"
            r = requests.get(endpoint, headers=_headers_rest(key), timeout=_TIMEOUT_SEC)
            if r.status_code == 200:
                for row in r.json() or []:
                    k = row.get("topic_key")
                    if k in base:
                        base[k] = int(row.get("count") or 0)
                return base
        except (requests.RequestException, ValueError, TypeError):
            pass
    path = _ruta_topic_archivo()
    if os.path.isfile(path):
        try:
            with open(path, "r", encoding="utf-8") as f:
                local = json.load(f)
            for t in temario.LISTA_TEMAS:
                if t in local:
                    base[t] = int(local[t] or 0)
        except (json.JSONDecodeError, OSError, TypeError):
            pass
    return base


def obtener_eventos_aprendizaje_estudiante(
    estudiante_id: str, limit: int = 600
) -> list[dict[str, Any]]:
    """
    Eventos de uso asociados al participante (Quiz, Tutor abierto, etc.).
    Requiere columna ``estudiante_id`` en ``app_usage_event`` (ver ``supabase_usage_events_estudiante.sql``).
    """
    url, key = _credenciales_supabase()
    if not url or not key:
        return []
    try:
        UUID(str(estudiante_id).strip())
    except ValueError:
        return []
    qid = urllib.parse.quote(str(estudiante_id).strip(), safe="")
    lim = max(50, min(int(limit), 2000))
    endpoint = (
        f"{url.rstrip('/')}/rest/v1/{_TABLE_USAGE_EVENT}"
        f"?estudiante_id=eq.{qid}&select=modo,payload,created_at"
        f"&order=created_at.desc&limit={lim}"
    )
    try:
        r = requests.get(endpoint, headers=_headers_rest(key), timeout=_TIMEOUT_SEC)
        if r.status_code != 200:
            return []
        rows = r.json()
        return rows if isinstance(rows, list) else []
    except (requests.RequestException, ValueError, TypeError):
        return []


def calcular_metricas_debilidad_por_tema(
    eventos: list[dict[str, Any]],
) -> dict[str, dict[str, Any]]:
    """
    A partir de eventos con ``estudiante_id``, acumula señales de debilidad:
    - Errores en Quiz (``tipo_evento`` = quiz_respuesta_incorrecta): peso alto.
    - Consultas en Tutor abierto con ``tema_catedra``: peso medio (dudas en ese tema).

    Devuelve ``tema_oficial -> {score, errores_quiz, consultas_tutor}`` solo para temas con actividad > 0.
    """
    acum: dict[str, dict[str, float]] = {}

    def _add(tema: Optional[str], quiz_delta: float, tutor_delta: float) -> None:
        if not tema or tema not in temario.LISTA_TEMAS:
            return
        slot = acum.setdefault(
            tema, {"score": 0.0, "errores_quiz": 0.0, "consultas_tutor": 0.0}
        )
        slot["score"] += quiz_delta + tutor_delta
        if quiz_delta:
            slot["errores_quiz"] += 1.0
        if tutor_delta:
            slot["consultas_tutor"] += 1.0

    for row in eventos:
        modo = (row.get("modo") or "").strip()
        pl = row.get("payload")
        if isinstance(pl, str):
            try:
                pl = json.loads(pl)
            except json.JSONDecodeError:
                pl = {}
        if not isinstance(pl, dict):
            pl = {}
        if modo == "Quiz" and pl.get("tipo_evento") == "quiz_respuesta_incorrecta":
            t = temario.normalizar_tema_curso(pl.get("tema"))
            _add(t, 4.0, 0.0)
        elif modo == "Tutor Preguntas Abiertas":
            t = temario.normalizar_tema_curso(pl.get("tema_catedra"))
            if t:
                _add(t, 0.0, 1.0)
    return {
        k: {
            "score": round(v["score"], 2),
            "errores_quiz": int(v["errores_quiz"]),
            "consultas_tutor": int(v["consultas_tutor"]),
        }
        for k, v in acum.items()
        if v["score"] > 0
    }
