"""
Registro append-only de interacciones usuario–IA en Supabase (tabla public.ia_logs).

Si no hay credenciales de Supabase o falla la red, el registro se omite en silencio
(la app no se detiene). Opcionalmente incluye estudiante_id cuando hay sesión activa.
"""
from __future__ import annotations

import sys
from typing import Any, List, Optional, Union
from uuid import UUID

import requests

try:
    from PIL import Image as PILImageModule
except ImportError:
    PILImageModule = None

_TABLE = "ia_logs"
_TIMEOUT_SEC = 12
_MAX_TEXTO = 120_000  # límite práctico por fila; evita payloads enormes

_warned_no_supabase = False


def _obtener_estudiante_id_sesion() -> Optional[str]:
    """UUID del participante autenticado (Supabase), si existe y es válido."""
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


def serializar_pregunta(prompt_parts: Union[str, List[Any]]) -> str:
    """Convierte el prompt enviado a Gemini en un solo texto para almacenar."""
    if isinstance(prompt_parts, str):
        return prompt_parts
    partes: List[str] = []
    for p in prompt_parts:
        if isinstance(p, str):
            partes.append(p)
        elif PILImageModule is not None and isinstance(p, PILImageModule.Image):
            partes.append("[imagen]")
        else:
            partes.append("[contenido no textual]")
    return "\n---\n".join(partes)


def extraer_texto_respuesta(response: Any) -> str:
    """Obtiene el texto de la respuesta de Gemini de forma tolerante a errores."""
    if response is None:
        return ""
    try:
        t = response.text
        return t if t is not None else ""
    except (ValueError, AttributeError):
        pass
    try:
        cand = response.candidates[0]
        parts = cand.content.parts
        return "".join(getattr(part, "text", "") or "" for part in parts)
    except (IndexError, AttributeError, TypeError):
        return "(contenido no disponible o bloqueado por políticas)"


def _truncar(s: str) -> str:
    if len(s) <= _MAX_TEXTO:
        return s
    return s[: _MAX_TEXTO - 20] + "\n...[truncado]"


def registrar_interaccion(pregunta: str, respuesta: str, modelo: str) -> None:
    """
    Inserta una fila en public.ia_logs (Supabase). Si no hay Supabase o falla la petición,
    no lanza excepción: la app sigue funcionando.
    """
    global _warned_no_supabase

    estudiante_id = _obtener_estudiante_id_sesion()

    try:
        from modules import uso_stats

        base, key = uso_stats.supabase_url_y_clave()
        if not base or not key:
            if not _warned_no_supabase:
                print(
                    "[registro_interacciones] Supabase no configurado: no se guardan logs ia_logs.",
                    file=sys.stderr,
                )
                _warned_no_supabase = True
            return

        url = f"{base.rstrip('/')}/rest/v1/{_TABLE}"
        payload: dict[str, Any] = {
            "pregunta": _truncar(pregunta or ""),
            "respuesta": _truncar(respuesta or ""),
            "modelo": (modelo or "")[:500],
        }
        if estudiante_id:
            payload["estudiante_id"] = estudiante_id

        r = requests.post(
            url,
            headers={**uso_stats.headers_supabase_rest(key), "Prefer": "return=minimal"},
            json=payload,
            timeout=_TIMEOUT_SEC,
        )
        if r.status_code not in (200, 201):
            print(
                f"[registro_interacciones] ia_logs POST {r.status_code}: {(r.text or '')[:400]}",
                file=sys.stderr,
            )
    except requests.RequestException as e:
        print(f"[registro_interacciones] Red ia_logs: {e}", file=sys.stderr)
    except Exception as e:
        print(f"[registro_interacciones] Error ia_logs: {e}", file=sys.stderr)
