# Tutor Matemáticas III — Economía UCAB

Tutor virtual para **Matemáticas III** (Cálculo Integral y Ecuaciones Diferenciales). Incluye entrenamiento guiado, consultas con foto o texto, quiz de autoevaluación y tutor de preguntas abiertas, usando **Streamlit** y **Google Gemini**.

## Requisitos

- Python 3.8+
- API Key de Google (Gemini)

## Instalación

```bash
pip install -r requirements.txt
```

## Configurar la API Key (obligatorio)

La aplicación necesita `GOOGLE_API_KEY` para conectar con Gemini.

1. Obtén una clave en [Google AI Studio](https://aistudio.google.com/apikey).
2. **Ejecución local:** crea la carpeta `.streamlit` y dentro el archivo `secrets.toml` con:
   ```toml
   GOOGLE_API_KEY = "tu-clave-aqui"
   ```
3. **Streamlit Cloud:** en tu app → Settings → Secrets, añade la variable `GOOGLE_API_KEY`.

Sin esta clave, la app se detendrá y mostrará en pantalla las mismas instrucciones.

## Ejecutar

```bash
streamlit run app.py
```

## Modos de la aplicación

- **Entrenamiento (Temario):** serie de 5 ejercicios paso a paso por temas.
- **Respuesta guiada:** subes foto o texto de un ejercicio y el tutor te guía.
- **Autoevaluación (Quiz):** simulacro de parcial (Primer, Segundo o temas personalizados).
- **Tutor preguntas abiertas:** chat sobre teoría y ejercicios de la cátedra.
