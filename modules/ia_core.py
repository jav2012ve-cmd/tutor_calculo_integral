import os
import streamlit as st
import google.generativeai as genai

def configurar_gemini():
    api_key = None
    try:
        if "GOOGLE_API_KEY" in st.secrets:
            api_key = st.secrets["GOOGLE_API_KEY"]
    except (Exception, FileNotFoundError):
        pass
    if not api_key:
        api_key = os.environ.get("GOOGLE_API_KEY")
    if api_key:
        genai.configure(api_key=api_key)
        return True
    st.error(
        "⚠️ **Falta la API Key de Google (Gemini).**\n\n"
        "Para que el tutor funcione, configura la clave:\n\n"
        "• **En local:** crea el archivo `.streamlit/secrets.toml` (carpeta del proyecto) con:\n"
        "  `GOOGLE_API_KEY = \"tu-clave-aqui\"`\n\n"
        "• **Variable de entorno:** también puedes definir `GOOGLE_API_KEY` en tu sistema.\n\n"
        "• **En Streamlit Cloud:** en la app → Settings → Secrets, añade `GOOGLE_API_KEY`.\n\n"
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
