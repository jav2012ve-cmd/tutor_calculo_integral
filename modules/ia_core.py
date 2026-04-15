import os
from typing import Optional

import google.generativeai as genai
import streamlit as st

# Nombres admitidos (Streamlit Secrets o variables de entorno), en orden de preferencia.
_NOMBRES_CLAVE = (
    "GOOGLE_API_KEY",
    "GEMINI_API_KEY",
    "GOOGLE_GEMINI_API_KEY",
)


def _leer_clave_google() -> Optional[str]:
    """Obtiene la API key desde st.secrets o entorno; ignora cadenas vacías."""
    for nombre in _NOMBRES_CLAVE:
        try:
            if nombre in st.secrets:
                v = str(st.secrets[nombre]).strip()
                if v:
                    return v
        except (FileNotFoundError, KeyError, TypeError, RuntimeError):
            pass
        except Exception:
            # Otros errores al leer secrets no deben tumbar la app silenciosamente
            pass
    for nombre in _NOMBRES_CLAVE:
        v = os.environ.get(nombre)
        if v and str(v).strip():
            return str(v).strip()
    return None


def configurar_gemini() -> bool:
    api_key = _leer_clave_google()
    if api_key:
        genai.configure(api_key=api_key)
        return True
    st.error(
        "⚠️ **Falta la API Key de Google (Gemini).**\n\n"
        "La app busca (en este orden) en **Secrets / entorno**: "
        "`GOOGLE_API_KEY`, `GEMINI_API_KEY` o `GOOGLE_GEMINI_API_KEY`.\n\n"
        "**Local:** crea `.streamlit/secrets.toml` con una línea como:\n"
        "`GOOGLE_API_KEY = \"AIza...\"` (comillas recomendadas).\n\n"
        "**Streamlit Cloud:** *Settings → Secrets* → pega en formato **TOML** (no JSON), por ejemplo:\n"
        "```\nGOOGLE_API_KEY = \"AIza...\"\n```\n"
        "Pulsa **Save** y luego **Reboot app** (o despliega de nuevo).\n\n"
        "**Variable de entorno:** define `GOOGLE_API_KEY` en el sistema o en el proveedor de hosting.\n\n"
        "Obtén la clave en [Google AI Studio](https://aistudio.google.com/apikey)."
    )
    return False

def obtener_modelo_robusto():
    try:
        for m in genai.list_models():
            if 'generateContent' in m.supported_generation_methods:
                if 'flash' in m.name: return m.name
        for m in genai.list_models():
             if 'generateContent' in m.supported_generation_methods: return m.name
        return "gemini-1.5-flash"
    except Exception:
        return "gemini-1.5-flash"

def iniciar_modelo():
    nombre_modelo = obtener_modelo_robusto()
    try:
        model = genai.GenerativeModel(
            model_name=nombre_modelo,
            generation_config={
                "temperature": 0.2,  # Menor creatividad = más rigor en formato
                "top_p": 0.95,
            }
        )
        return model, nombre_modelo
    except Exception as e:
        st.error(f"Error iniciando modelo: {e}")
        return None, None
