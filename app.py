from __future__ import annotations

import json
import re
import time
from typing import Any, List, Optional, Union

import streamlit as st
from PIL import Image

from modules import ia_core, interfaz, temario, banco_preguntas, banco_muestras

# --- CONFIGURACIÓN CENTRALIZADA ---
NUM_EJERCICIOS_ENTRENAMIENTO = 5
NUM_PREGUNTAS_QUIZ = 5
INTENTOS_MAX_IA = 3
MULTIPLICADOR_ESPERA_429 = 4  # segundos por intento ante error 429
MAX_MENSAJES_HISTORIAL_TUTOR = 10  # últimos N mensajes para contexto IA
AVISO_HISTORIAL_LARGO = 20  # si hay más mensajes, mostrar aviso

# --- 1. CONFIGURACIÓN INICIAL ---
interfaz.configurar_pagina()

if not ia_core.configurar_gemini():
    st.stop()

model, nombre_modelo = ia_core.iniciar_modelo()

# =======================================================
# FUNCIONES DE SEGURIDAD Y UTILIDADES
# =======================================================

def generar_contenido_seguro(
    prompt_parts: Union[str, list],
    intentos_max: Optional[int] = None,
) -> Optional[Any]:
    """
    Intenta llamar a la IA con texto o imágenes.
    Soporta lista de partes (prompt + imagen) o solo texto.
    """
    if intentos_max is None:
        intentos_max = INTENTOS_MAX_IA
    errores_recientes = ""
    for i in range(intentos_max):
        try:
            return model.generate_content(prompt_parts)
        except Exception as e:
            errores_recientes = str(e)
            if "429" in str(e):
                tiempo_espera = MULTIPLICADOR_ESPERA_429 * (i + 1)
                st.toast(f"🚦 Tráfico alto. Reintentando en {tiempo_espera}s...", icon="⏳")
                time.sleep(tiempo_espera)
            else:
                time.sleep(1)
    
    st.error(f"❌ Error de conexión: {errores_recientes}")
    return None

def preparar_latex_para_streamlit(texto: Optional[str]) -> str:
    """
    Sanea texto con LaTeX para que Streamlit lo renderice bien.
    Quita literales molestos, envuelve \\frac/\\int/\\left en math y líneas que son solo ecuación en $$.
    """
    if not texto:
        return ""
    t = texto
    # Quitar espaciado LaTeX que se muestra literal
    t = re.sub(r"\\\[\s*[\d.]*em\s*\]", " ", t)
    t = t.replace("$$$$", "$$").replace("\\\\", "\n")
    # Envolver \sqrt, \int y \frac sueltos (no ya dentro de $) para render en Streamlit
    def wrap_frac(m):
        return f"$\\frac{{{m.group(1)}}}{{{m.group(2)}}}$"
    t = re.sub(r"(?<!\$)\\frac\{([^{}]+)\}\{([^{}]+)\}(?!\$)", wrap_frac, t)
    # Python 3.13: \c en el patrón es bad escape; construir patrón sin \cdot
    t = re.sub(r"(?<!\$)\\" + "cdot" + r"(?!\$)", lambda _: "$\\cdot$", t)
    def wrap_sqrt(m):
        return f"$\\sqrt{{{m.group(1)}}}$"
    # Evitar \s en patrón como escape: buscar backslash + "sqrt"
    t = re.sub(r"(?<!\$)\\" + "sqrt" + r"\{([^{}]+)\}(?!\$)", wrap_sqrt, t)
    # Líneas que son claramente ecuación: envolver en $$ para display math
    lineas = t.split("\n")
    result = []
    for linea in lineas:
        linea = linea.strip()
        if not linea:
            result.append("")
            continue
        if ("$" not in linea or linea.count("$") % 2 != 0) and (
            "\\int" in linea or "\\frac" in linea or "\\left" in linea or "\\right" in linea or "\\sqrt" in linea
        ):
            linea = linea.replace("$$", "")
            result.append(f"$${linea}$$")
        else:
            result.append(linea)
    t = "\n".join(result)
    return t.strip()

def limpiar_json(texto: Optional[str]) -> Optional[Any]:
    """
    Limpieza quirúrgica para respuestas con LaTeX.
    Devuelve dict o list si parsea correctamente; None en caso contrario.
    """
    if not texto: return None
    texto = texto.replace("```json", "").replace("```", "").strip()
    
    # Intento 1: Directo
    try:
        return json.loads(texto)
    except json.JSONDecodeError:
        pass

    # Intento 2: Reparación Regex para LaTeX
    try:
        # Escapa barras invertidas que no sean de control JSON
        texto_reparado = re.sub(r'\\(?!["\\/bfnrtu])', r'\\\\', texto)
        return json.loads(texto_reparado)
    except Exception:
        # Intento 3: Fuerza bruta si falla regex
        try:
             return json.loads(texto.replace("\\", "\\\\"))
        except:
             return None

def generar_tutor_paso_a_paso(pregunta_texto: str, tema: str) -> Optional[dict]:
    """Genera la tutoría para el modo Entrenamiento (Banco/IA)."""
    regla_tema = ""
    if "Integrales Directas" in (tema or ""):
        regla_tema = """
    RESTRICCIÓN DE CONTENIDO (CRÍTICO para este tema):
    - El tema "Integrales Directas" es EXCLUSIVO de integrales INDEFINIDAS.
    - NO uses integrales definidas: ni límites de integración (ej. \\int_a^b, \\int_0^1), ni "evalúe la integral definida", ni aplicación del teorema fundamental.
    - Si el ejercicio que te pasan tiene integral definida, reescríbelo como integral INDEFINIDA equivalente (misma función a integrar, sin límites) o genera un ejercicio de integral indefinida acorde al tema.
    """
    prompt = f"""
    Actúa como un profesor experto de cálculo. Para el siguiente ejercicio de {tema}:
    "{pregunta_texto}"
    
    Genera un objeto JSON estricto.
    REGLAS LATEX (CRÍTICO):
    1. Escribe la fórmula pura. NO incluyas signos "$$" dentro del JSON.
    2. Usa DOBLE BARRA para comandos: \\\\frac, \\\\int.
    
    Estructura JSON:
    {{
        "estrategias": ["Estrategia Correcta", "Estrategia Incorrecta 1", "Estrategia Incorrecta 2"],
        "indice_correcta": 0,
        "feedback_estrategia": "Explicación breve.",
        "paso_intermedio": "Ecuación LaTeX PURA (sin $$) del hito",
        "resultado_final": "Ecuación LaTeX PURA (sin $$) del resultado"
    }}
    Orden aleatorio en estrategias.
    """
    response = generar_contenido_seguro(prompt)
    if response:
        return limpiar_json(response.text)
    return None

def analizar_problema_usuario(
    texto_usuario: Optional[str],
    imagen_usuario: Any = None,
) -> Optional[dict]:
    """
    Analiza un problema subido por el alumno (texto o imagen).
    Distingue entre Integrales/EDO (rígido) y Aplicaciones (flexible).
    """
    prompt_base = """
    Actúa como un Tutor Experto de Matemáticas III.
    Analiza el problema del estudiante (texto o imagen).

    OBJETIVO: Generar una guía paso a paso JSON.

    REGLAS DE ESTRATEGIAS (CRÍTICO):
    1. Si es INTEGRAL (Cálculo directo): Las opciones DEBEN ser Técnicas (ej. "Por Partes", "Sustitución", "Fracciones Parciales").
    2. Si es EDO (Resolver ecuación): Las opciones DEBEN ser Tipos (ej. "Variables Separables", "Lineal", "Exacta").
    3. Si es CÁLCULO DE ÁREAS, VOLÚMENES, EXCEDENTES O APLICACIONES:
       - Tienes LIBERTAD TOTAL.
       - Las opciones deben ser PLANTEAMIENTOS o ENFOQUES (ej. "Integrar con respecto a Y", "Usar método de arandelas", "Igualar Oferta y Demanda").

    REGLAS LATEX (CRÍTICO):
    1. Escribe la fórmula pura. NO incluyas signos "$$" dentro del JSON.
    2. Usa DOBLE BARRA para comandos: \\\\frac, \\\\int.
    
    Estructura JSON requerida:
    {
        "tema_detectado": "Nombre del tema (ej. Volumen de Revolución)",
        "enunciado_latex": "El problema transcrito a LaTeX (sin $$)",
        "estrategias": ["Planteamiento/Técnica CORRECTA", "Opción INCORRECTA 1", "Opción INCORRECTA 2"],
        "indice_correcta": 0,
        "feedback_estrategia": "Por qué este es el camino correcto.",
        "paso_intermedio": "Un hito clave a mitad del desarrollo (LaTeX puro, sin $$)",
        "resultado_final": "La solución final (LaTeX puro, sin $$)"
    }
    """
    
    contenido = [prompt_base]
    if texto_usuario:
        contenido.append(f"Enunciado del estudiante: {texto_usuario}")
    if imagen_usuario:
        contenido.append(imagen_usuario)
        contenido.append("Transcribe y resuelve.")

    response = generar_contenido_seguro(contenido)
    if response:
        return limpiar_json(response.text)
    return None
def generar_respuesta_tutor_abierto(
    pregunta_usuario: str,
    historial_previo: str,
) -> str:
    """
    Tutor de Preguntas Abiertas.
    Usa el contexto de banco_muestras y banco_preguntas para personalizar la respuesta.
    """
    # 1. Construimos el contexto (tomamos una muestra para no saturar)
    contexto_ejercicios = str(banco_preguntas.BANCO_FIXED[:10]) 
    estilos_examen = banco_muestras.EJEMPLOS_ESTILO

    # 2. Prompt del Sistema (La personalidad del profesor)
    prompt_tutor = f"""
    Eres el tutor virtual de Matemáticas III para Economía en la UCAB.
    Tu objetivo es ayudar al estudiante a entender la teoría, pero SIEMPRE aterrizándola a la práctica de la clase.

    CONTEXTO DE LA CÁTEDRA (Tu base de conocimiento):
    --- Estilos de Examen ---
    {estilos_examen}
    --- Ejercicios del Banco Oficial (Muestra) ---
    {contexto_ejercicios}
    
    INSTRUCCIONES CLAVE:
    1. Responde de forma clara y pedagógica.
    
    2. GESTIÓN DEL CONOCIMIENTO (CRÍTICO):
       - Usa los ejercicios del contexto para mantener el estilo y la dificultad de la cátedra.
       - SI EL CONTEXTO NO TIENE EJEMPLOS DE UN TEMA (ej. Integrales Dobles o Impropias): 
         NO digas "el banco es pequeño" ni "no tengo ejemplos". 
         Genera tú mismo un ejemplo matemático riguroso (nivel Leithold/Larson) y preséntalo con naturalidad, diciendo: "Un caso típico que estudiamos en este tema es..." o "Para ilustrar esto, analicemos...".
    
    3. FORMATO MATEMÁTICO (CRÍTICO): 
       - Usa SIEMPRE signos de dólar para encerrar el LaTeX.
       - Para fórmulas dentro del texto usa uno solo: $ f(x) = x^2 $
       - Para ecuaciones grandes o centradas usa doble signo: $$ \\int_{{a}}^{{b}} f(x) dx $$
       
    4. VINCULACIÓN: Siempre que sea posible, menciona: "Esto sigue la lógica de nuestros ejercicios de parcial..." o "Es análogo a los problemas de oferta y demanda...".

    Historial de chat reciente:
    {historial_previo}

    Pregunta del estudiante:
    {pregunta_usuario}
    """
    
    response = generar_contenido_seguro(prompt_tutor)
    if response:
        return response.text
    return "Lo siento, tuve un problema pensando la respuesta."

def _sanitizar_para_pdf(texto: Optional[str]) -> str:
    """Reduce LaTeX y caracteres especiales para PDF legible (fuente estándar)."""
    if not texto:
        return ""
    t = texto.replace("$$", "").replace("$", "").strip()
    t = t.replace("\\frac", " frac ").replace("\\int", " int ").replace("\\ln", " ln ")
    for c, r in [("á", "a"), ("é", "e"), ("í", "i"), ("ó", "o"), ("ú", "u"), ("ñ", "n"), ("¿", "?"), ("¡", "")]:
        t = t.replace(c, r).replace(c.upper(), r.upper())
    return t[:500] if len(t) > 500 else t

def generar_pdf_informe_quiz(
    respuestas_usuario: List[dict],
    nota_final: float,
) -> Union[bytes, bytearray]:
    """Genera bytes del PDF con calificación y detalle del examen."""
    from fpdf import FPDF
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Helvetica", size=14)
    pdf.cell(0, 10, "Informe de evaluacion - Matematicas III (Economia UCAB)", ln=True)
    pdf.set_font("Helvetica", size=11)
    pdf.cell(0, 8, f"Calificacion final: {nota_final} / 20 pts", ln=True)
    pdf.cell(0, 8, "Aprobado." if nota_final >= 10 else "No aprobado.", ln=True)
    pdf.ln(4)
    for i, r in enumerate(respuestas_usuario, 1):
        pdf.set_font("Helvetica", "B", size=10)
        pts = r.get("puntos", 0)
        pdf.cell(0, 6, f"Pregunta {i} ({pts} pts)", ln=True)
        pdf.set_font("Helvetica", size=9)
        pdf.multi_cell(0, 5, _sanitizar_para_pdf(r.get("pregunta", "")))
        pdf.cell(0, 4, "Tu respuesta: " + _sanitizar_para_pdf(r.get("elegida", "")), ln=True)
        if not r.get("es_correcta", True):
            pdf.cell(0, 4, "Correcta: " + _sanitizar_para_pdf(r.get("correcta", "")), ln=True)
        pdf.cell(0, 4, "Comentario: " + _sanitizar_para_pdf(r.get("explicacion", "")), ln=True)
        pdf.ln(2)
    out = pdf.output()
    return bytes(out) if not isinstance(out, bytes) else out

# --- 2. GESTIÓN DE ESTADO ---
if "quiz_activo" not in st.session_state: st.session_state.quiz_activo = False
if "preguntas_quiz" not in st.session_state: st.session_state.preguntas_quiz = []
if "indice_pregunta" not in st.session_state: st.session_state.indice_pregunta = 0
if "respuestas_usuario" not in st.session_state: st.session_state.respuestas_usuario = [] 

# Estados para Respuesta Guiada (Modo B)
if "consulta_step" not in st.session_state: st.session_state.consulta_step = 0
if "consulta_data" not in st.session_state: st.session_state.consulta_data = None
if "consulta_validada" not in st.session_state: st.session_state.consulta_validada = False

# Estado D: Tutor Preguntas Abiertas (NUEVO)  <-- AGREGA ESTAS DOS LÍNEAS
if "historial_tutor_abierto" not in st.session_state: st.session_state.historial_tutor_abierto = []

# --- 3. INTERFAZ PRINCIPAL ---
ruta, tema_actual = interfaz.mostrar_sidebar()
interfaz.mostrar_bienvenida()

# =======================================================
# LÓGICA A: MODO ENTRENAMIENTO (Dojo Matemático)
# =======================================================
if ruta == "a) Entrenamiento (Temario)":
    st.markdown("### 🥋 Dojo de Matemáticas (Entrenamiento Guiado)")
    st.info("Resolución paso a paso: **1. Elegir Estrategia** -> **2. Hito Intermedio** -> **3. Resultado Final**.")

    if "entrenamiento_activo" not in st.session_state:
        st.session_state.entrenamiento_activo = False

    # --- PANTALLA 0: CONFIGURACIÓN ---
    if not st.session_state.entrenamiento_activo:
        temas_entrenamiento = st.multiselect(
            "🎯 Selecciona los temas a practicar:",
            options=temario.LISTA_TEMAS,
            placeholder="Ej. Ecuaciones Diferenciales Lineales..."
        )

        if st.button(f"⚡ Iniciar Sesión ({NUM_EJERCICIOS_ENTRENAMIENTO} Ejercicios)", type="primary", use_container_width=True):
            if not temas_entrenamiento:
                st.error("⚠️ Selecciona al menos un tema.")
            else:
                cargar_exito = False
                with st.spinner("Preparando tu serie de ejercicios..."):
                    try:
                        import random
                        lista_entrenamiento = []
                        
                        # 1. Banco de Preguntas (Protegido)
                        try:
                            preguntas_banco = banco_preguntas.obtener_preguntas_fijas(temas_entrenamiento, 2)
                            if preguntas_banco:
                                lista_entrenamiento.extend(preguntas_banco)
                        except Exception as e:
                            print(f"Aviso: Banco no disponible {e}")

                        # 2. Generación IA (Protegida)
                        faltantes = NUM_EJERCICIOS_ENTRENAMIENTO - len(lista_entrenamiento)
                        if faltantes > 0:
                            prompt_train = temario.generar_prompt_quiz(temas_entrenamiento, faltantes)
                            respuesta_ia = generar_contenido_seguro(prompt_train)
                            
                            if respuesta_ia:
                                preguntas_ia = limpiar_json(respuesta_ia.text)
                                if preguntas_ia: 
                                    lista_entrenamiento.extend(preguntas_ia)
                        
                        if not lista_entrenamiento:
                            st.error("No se encontraron preguntas. No se pudo interpretar la respuesta de la IA; intenta con otro tema o de nuevo.")
                        else:
                            random.shuffle(lista_entrenamiento)
                            st.session_state.entrenamiento_lista = lista_entrenamiento[:NUM_EJERCICIOS_ENTRENAMIENTO]
                            st.session_state.entrenamiento_idx = 0
                            st.session_state.entrenamiento_step = 1
                            st.session_state.entrenamiento_data_ia = None
                            st.session_state.entrenamiento_validado = False 
                            st.session_state.entrenamiento_activo = True
                            cargar_exito = True

                    except Exception as e:
                        st.error(f"Error técnico al iniciar: {e}")
                
                if cargar_exito:
                    st.rerun()

    # --- PANTALLA DE EJERCICIOS (El Dojo) ---
    else:
        idx = st.session_state.entrenamiento_idx
        lista = st.session_state.entrenamiento_lista
        
        if idx < len(lista):
            ejercicio = lista[idx]
            
            st.progress((idx + 1) / NUM_EJERCICIOS_ENTRENAMIENTO, text=f"Ejercicio {idx + 1} de {NUM_EJERCICIOS_ENTRENAMIENTO}")
            st.markdown(f"**Tema:** `{ejercicio.get('tema', 'General')}`")
            st.markdown("### " + preparar_latex_para_streamlit(ejercicio["pregunta"]))
            st.divider()

            # --- LLAMADA A LA IA TUTOR ---
            if st.session_state.entrenamiento_data_ia is None:
                with st.spinner("🧠 El profesor está analizando el mejor camino de resolución..."):
                    datos_tutor = generar_tutor_paso_a_paso(ejercicio['pregunta'], ejercicio.get('tema', 'Cálculo'))
                    if datos_tutor:
                        st.session_state.entrenamiento_data_ia = datos_tutor
                        st.rerun()
                    else:
                        st.error("No se pudo interpretar la respuesta del tutor. Saltando ejercicio; puedes continuar con el siguiente.")
                        st.session_state.entrenamiento_idx += 1
                        time.sleep(2)
                        st.rerun()
            
            tutor = st.session_state.entrenamiento_data_ia
            step = st.session_state.entrenamiento_step

            # PASO 1: ESTRATEGIA
            if step == 1:
                st.markdown("#### 1️⃣ Paso 1: Selección de Estrategia")
                st.write("Antes de calcular, ¿cuál crees que es el camino correcto?")
                
                opcion_estrategia = st.radio("Selecciona el método:", tutor['estrategias'], index=None, key=f"radio_estrat_{idx}")
                
                if st.button("Validar Estrategia", key=f"btn_val_{idx}"):
                    if opcion_estrategia:
                        idx_seleccionado = tutor['estrategias'].index(opcion_estrategia)
                        if idx_seleccionado == tutor['indice_correcta']:
                            st.session_state.entrenamiento_validado = True 
                        else:
                            st.error("❌ Mmm, no es el mejor camino.")
                            st.warning(f"Pista: {tutor['feedback_estrategia']}")
                    else:
                        st.warning("Debes seleccionar una opción.")

                if st.session_state.get("entrenamiento_validado", False):
                    st.success("✅ ¡Exacto! Esa es la ruta.")
                    st.info(f"👨‍🏫 **Feedback:** {tutor['feedback_estrategia']}")
                    
                    if st.button("Ir al Paso Intermedio ➡️", type="primary", key=f"btn_go_step2_{idx}"):
                        st.session_state.entrenamiento_step = 2
                        st.session_state.entrenamiento_validado = False
                        st.rerun()

            # PASO 2: HITO INTERMEDIO
            if step == 2:
                st.success(f"✅ Estrategia: {tutor['estrategias'][tutor['indice_correcta']]}")
                st.markdown("#### 2️⃣ Paso 2: Ejecución Intermedia")
                st.write("Aplica la estrategia seleccionada. Deberías llegar a una expresión similar a esta:")
                
                # CORRECCIÓN LATEX: Limpiamos por seguridad
                latex_limpio = tutor['paso_intermedio'].replace('$', '')
                st.info(f"$${latex_limpio}$$")
                
                st.write("¿Lograste llegar a este punto o algo equivalente?")
                
                col_si, col_no = st.columns(2)
                with col_si:
                    if st.button("👍 Sí, lo tengo", key=f"btn_si_{idx}"):
                        st.session_state.entrenamiento_step = 3
                        st.rerun()
                with col_no:
                    if st.button("👎 No, necesito ayuda", key=f"btn_no_{idx}"):
                        st.error("Revisa tus derivadas/integrales básicas o el álgebra.")

            # PASO 3: FINAL
            if step == 3:
                st.success(f"✅ Estrategia Correcta | ✅ Hito Intermedio Alcanzado")
                st.markdown("#### 3️⃣ Paso 3: Resolución Final")
                st.write("El resultado definitivo es:")
                
                # CORRECCIÓN LATEX
                latex_final = tutor['resultado_final'].replace('$', '')
                st.success(f"$$ {latex_final} $$")
                
                with st.expander("Ver explicación completa"):
                    st.markdown(preparar_latex_para_streamlit(ejercicio.get("explicacion", "Procedimiento estándar aplicado correctamente.")))

                if st.button("Siguiente Ejercicio ➡️", type="primary", key=f"btn_next_{idx}"):
                    st.session_state.entrenamiento_idx += 1
                    st.session_state.entrenamiento_step = 1
                    st.session_state.entrenamiento_data_ia = None 
                    st.session_state.entrenamiento_validado = False
                    st.rerun()

        else:
            st.success("🎉 ¡Entrenamiento completado!")
            if st.button("🔄 Volver al Inicio", key="btn_reset_entrenamiento"):
                st.session_state.entrenamiento_activo = False
                st.session_state.entrenamiento_idx = 0
                st.rerun()

# =======================================================
# LÓGICA B: RESPUESTA GUIADA (Consultas) - TUTOR PERSONALIZADO
# =======================================================
elif ruta == "b) Respuesta Guiada (Consultas)":
    st.markdown("### 🎓 Tutor Personalizado")
    st.info("Sube tu ejercicio (foto o texto) y te guiaré paso a paso.")

    # 1. INPUT (Foto o Texto)
    if st.session_state.consulta_step == 0:
        col_img, col_txt = st.columns([1, 2])
        with col_img:
            imagen_subida = st.file_uploader("📸 Foto del ejercicio", type=["png", "jpg", "jpeg"])
        with col_txt:
            texto_subido = st.text_area("✍️ O escribe el enunciado aquí:", height=100)

        if st.button("🚀 Resolver Paso a Paso", type="primary", use_container_width=True):
            if not imagen_subida and not texto_subido:
                st.warning("⚠️ Sube una imagen o escribe el texto para comenzar.")
            else:
                exito_analisis = False
                with st.spinner("🤖 Analizando el tipo de problema..."):
                    try:
                        # Solo abrir imagen si el usuario subió un archivo (flujo texto-only no usa imagen)
                        img_pil = None
                        if imagen_subida:
                            img_pil = Image.open(imagen_subida)
                        datos_problema = analizar_problema_usuario(texto_subido or None, img_pil)
                        if datos_problema:
                            st.session_state.consulta_data = datos_problema
                            st.session_state.consulta_step = 1
                            st.session_state.consulta_validada = False
                            exito_analisis = True
                        else:
                            st.error("No se pudo interpretar la respuesta del tutor. Intenta de nuevo con otra redacción o imagen más clara.")
                    except Exception as e:
                        st.error(f"Error técnico: {e}")
                
                if exito_analisis:
                    st.rerun()

    # 2. INTERACCIÓN (Similar al Dojo pero para el problema del usuario)
    else:
        datos = st.session_state.consulta_data
        step = st.session_state.consulta_step

        # Botón para cancelar/reiniciar arriba
        if st.button("🔄 Nueva Consulta", key="btn_new_query_top"):
            st.session_state.consulta_step = 0
            st.session_state.consulta_data = None
            st.rerun()

        st.divider()
        st.markdown(f"**Tema Detectado:** `{datos.get('tema_detectado', 'Matemáticas')}`")
        if datos.get('enunciado_latex'):
            # CORRECCIÓN LATEX
            enunciado_limpio = datos['enunciado_latex'].replace('$', '')
            st.markdown(f"**Problema Identificado:**\n$$ {enunciado_limpio} $$")
        
        # PASO 1: Identificar Técnica/Tipo o Planteamiento
        if step == 1:
            st.subheader("1️⃣ Paso 1: Planteamiento")
            
            # Lógica dinámica para el mensaje
            tema_lower = datos.get('tema_detectado', '').lower()
            if "integral" in tema_lower and "área" not in tema_lower and "volumen" not in tema_lower:
                st.write("¿Qué **técnica de integración** usarías?")
            elif "ecuación diferencial" in tema_lower and "aplicación" not in tema_lower:
                st.write("¿Qué **tipo de EDO** es esta?")
            else:
                # Caso Áreas, Volúmenes, Excedentes, etc.
                st.write("¿Cuál es el **planteamiento o enfoque** correcto?")

            opcion = st.radio("Selecciona:", datos['estrategias'], index=None, key="rad_cons")
            
            if st.button("Validar Estrategia", type="primary"):
                if opcion and datos['estrategias'].index(opcion) == datos['indice_correcta']:
                    st.session_state.consulta_validada = True
                    st.rerun()
                else:
                    st.error("❌ No es lo más eficiente.")
                    st.warning(datos['feedback_estrategia'])
            
            if st.session_state.consulta_validada:
                st.success("✅ ¡Correcto! Vamos a desarrollarlo.")
                if st.button("Ver Paso Intermedio ➡️"):
                    st.session_state.consulta_step = 2
                    st.session_state.consulta_validada = False
                    st.rerun()

        # PASO 2: Hito Intermedio
        if step == 2:
            st.success(f"✅ Estrategia: {datos['estrategias'][datos['indice_correcta']]}")
            st.subheader("2️⃣ Paso 2: Desarrollo")
            st.write("Aplicando la técnica, deberías llegar a esta expresión intermedia:")
            
            # CORRECCIÓN LATEX
            intermedio_limpio = datos['paso_intermedio'].replace('$', '')
            st.info(f"$$ {intermedio_limpio} $$")
            
            c1, c2 = st.columns(2)
            if c1.button("👍 Llegué a eso"):
                st.session_state.consulta_step = 3
                st.rerun()
            if c2.button("👎 Me perdí, explícame"):
                st.info(f"💡 Pista: {datos.get('feedback_estrategia', 'Revisa las operaciones algebraicas.')}")

        # PASO 3: Solución Final
        if step == 3:
            st.success("✅ Desarrollo intermedio correcto")
            st.subheader("3️⃣ Solución Final")
            
            # CORRECCIÓN LATEX
            final_limpio = datos['resultado_final'].replace('$', '')
            st.success(f"### $$ {final_limpio} $$")
            
            st.balloons()
            if st.button("🏁 Terminar ejercicio"):
                st.session_state.consulta_step = 0
                st.session_state.consulta_data = None
                st.rerun()

# =======================================================
# LÓGICA C: AUTOEVALUACIÓN (Quiz)
# =======================================================
elif ruta == "c) Autoevaluación (Quiz)":
    st.markdown("### 📝 Centro de Evaluación")

    # --- PANTALLA 1: CONFIGURACIÓN ---
    if not st.session_state.quiz_activo:
        st.info("Configura tu prueba (El sistema combinará ejercicios oficiales y generados por IA):")
        
        col1, col2 = st.columns(2)
        with col1:
            if st.button("🏆 Generar Primer Parcial (Simulacro)", use_container_width=True):
                st.session_state.config_temas = temario.TEMAS_PARCIAL_1
                st.session_state.config_cant = NUM_PREGUNTAS_QUIZ 
                st.session_state.trigger_quiz = True
                st.rerun()
        with col2:
            if st.button("🏆 Generar Segundo Parcial (Simulacro)", use_container_width=True):
                st.session_state.config_temas = temario.TEMAS_PARCIAL_2
                st.session_state.config_cant = NUM_PREGUNTAS_QUIZ
                st.session_state.trigger_quiz = True
                st.rerun()

        with st.expander("⚙️ Personalizado"):
            temas_custom = st.multiselect("Temas:", temario.LISTA_TEMAS)
            if st.button("▶️ Iniciar Quiz Custom"):
                if not temas_custom:
                    st.error("Selecciona tema.")
                else:
                    st.session_state.config_temas = temas_custom
                    st.session_state.config_cant = NUM_PREGUNTAS_QUIZ
                    st.session_state.trigger_quiz = True
                    st.rerun()

        # --- LÓGICA DE GENERACIÓN ---
        if st.session_state.get("trigger_quiz"):
            quiz_generado = False
            with st.spinner("Compilando examen (Balanceando 50% Banco Oficial / 50% IA)..."):
                try:
                    import random
                    lista_final_preguntas = []
                    cantidad_total = st.session_state.config_cant
                    temas = st.session_state.config_temas

                    cuota_banco = cantidad_total // 2
                    cuota_ia = cantidad_total - cuota_banco

                    # 1. Banco
                    try:
                        preguntas_banco = banco_preguntas.obtener_preguntas_fijas(temas, cuota_banco)
                        if preguntas_banco:
                            lista_final_preguntas.extend(preguntas_banco)
                    except: pass
                    
                    # 2. IA
                    falta = cantidad_total - len(lista_final_preguntas)
                    if falta > 0:
                        prompt_quiz = temario.generar_prompt_quiz(temas, falta)
                        respuesta = generar_contenido_seguro(prompt_quiz)
                        if respuesta:
                            preguntas_ia = limpiar_json(respuesta.text)
                            if preguntas_ia:
                                lista_final_preguntas.extend(preguntas_ia)
                    
                    random.shuffle(lista_final_preguntas)
                    lista_final_preguntas = lista_final_preguntas[:cantidad_total]

                    if not lista_final_preguntas:
                         st.error("No se pudieron generar preguntas. No se pudo interpretar la respuesta de la IA; intenta de nuevo.")
                         st.session_state.trigger_quiz = False
                    else:
                        st.session_state.preguntas_quiz = lista_final_preguntas
                        st.session_state.indice_pregunta = 0
                        st.session_state.respuestas_usuario = []
                        st.session_state.quiz_activo = True
                        st.session_state.trigger_quiz = False
                        quiz_generado = True
                    
                except Exception as e:
                    st.error(f"Error generando examen: {e}")
                    st.session_state.trigger_quiz = False
            
            if quiz_generado:
                st.rerun()

    # --- PANTALLA 2 (RESPONDER) y 3 (RESULTADOS) ---
    else:
        total = len(st.session_state.preguntas_quiz)
        actual = st.session_state.indice_pregunta
        
        if actual < total:
            pregunta_data = st.session_state.preguntas_quiz[actual]
            
            st.progress((actual) / total, text=f"Pregunta {actual + 1} de {total}")
            
            # 1. RENDERIZADO DE LA PREGUNTA
            st.markdown("#### " + preparar_latex_para_streamlit(pregunta_data["pregunta"]))
            st.divider()
            
            # 2. RENDERIZADO DE LAS OPCIONES (VISUAL) — LaTeX renderizado como fórmula
            st.write("Opciones:")
            col_ops = st.columns(2)
            opciones_completas = pregunta_data["opciones"]

            for i, opcion_texto in enumerate(opciones_completas):
                if ")" in opcion_texto:
                    letra, resto = opcion_texto.split(")", 1)
                    resto = preparar_latex_para_streamlit(resto.strip())
                    texto_mostrar = f"**{letra})** {resto}"
                else:
                    texto_mostrar = preparar_latex_para_streamlit(opcion_texto)

                with col_ops[i % 2]:
                    st.markdown(texto_mostrar)
            
            st.divider()

            # 3. SELECTOR DE RESPUESTA (LÓGICA)
            ya_respondido = len(st.session_state.respuestas_usuario) > actual
            
            if not ya_respondido:
                # Creamos opciones simplificadas (Solo A, B, C, D) para el selector
                # Así evitamos que Streamlit intente renderizar LaTeX crudo en el widget
                opciones_radio = [op.split(")")[0] + ")" for op in opciones_completas]
                
                seleccion_letra = st.radio(
                    "Selecciona tu respuesta:", 
                    opciones_radio, 
                    key=f"radio_{actual}", 
                    index=None,
                    horizontal=True
                )

                if st.button("Responder", type="primary"):
                    if seleccion_letra:
                        # Recuperamos la opción completa original basada en la letra seleccionada
                        letra_elegida = seleccion_letra.split(")")[0] # Ej: "A"
                        # Buscamos la opción original que empieza con esa letra
                        opcion_elegida_completa = next(op for op in opciones_completas if op.startswith(letra_elegida))
                        
                        letra_correcta = pregunta_data['respuesta_correcta'].strip()[0].upper()
                        es_correcta = (letra_elegida == letra_correcta)
                        pts = round(20 / total, 2) if es_correcta else 0
                        
                        st.session_state.respuestas_usuario.append({
                            "pregunta": pregunta_data['pregunta'],
                            "elegida": opcion_elegida_completa, # Guardamos la completa para el reporte final
                            "correcta": pregunta_data['respuesta_correcta'],
                            "explicacion": pregunta_data['explicacion'],
                            "puntos": pts,
                            "es_correcta": es_correcta
                        })
                        st.rerun()
                    else:
                        st.warning("⚠️ Selecciona una opción.")
            
            else:
                # FEEDBACK INMEDIATO (Si ya respondió pero no ha pasado a la siguiente)
                ultimo_dato = st.session_state.respuestas_usuario[actual]
                
                # Renderizamos la elección del usuario de forma bonita
                st.info(f"Tu respuesta: **{ultimo_dato['elegida']}**")
                
                if ultimo_dato['es_correcta']:
                    st.success("✅ ¡Correcto!")
                else:
                    st.error(f"❌ Incorrecto. La correcta era: {ultimo_dato['correcta']}")
                
                with st.expander("💡 Ver Explicación", expanded=True):
                    st.markdown(preparar_latex_para_streamlit(ultimo_dato["explicacion"]))
                
                if st.button("Siguiente Pregunta ➡️", type="primary"):
                    st.session_state.indice_pregunta += 1
                    st.rerun()

        else:
            # PANTALLA 3: RESULTADOS
            suma_puntos = sum(r['puntos'] for r in st.session_state.respuestas_usuario)
            nota_final = round(suma_puntos, 2)

            if nota_final >= 10:
                st.success(f"✅ Examen Finalizado - Aprobado con {nota_final}")
            else:
                st.warning(f"⚠️ Examen Finalizado - Nota: {nota_final}")
            
            col_nota_top, col_info_top = st.columns([1, 2])
            with col_nota_top:
                st.metric("Calificación Final", f"{nota_final} / 20 pts")
            with col_info_top:
                st.info("💡 Puedes **descargar el informe en PDF** con tu calificación y comentarios al final de esta página.")

            st.divider()
            st.subheader("📄 Detalle del Examen")

            for i, r in enumerate(st.session_state.respuestas_usuario):
                st.markdown(f"#### 🔹 Pregunta {i+1} ({r['puntos']} pts)")
                st.markdown(preparar_latex_para_streamlit(r["pregunta"])) 
                
                col_res1, col_res2 = st.columns(2)
                with col_res1:
                    if r['es_correcta']:
                        st.success(f"✅ **Tu respuesta:** {r['elegida']}")
                    else:
                        st.error(f"❌ **Tu respuesta:** {r['elegida']}")
                
                with col_res2:
                    if not r['es_correcta']:
                        st.warning(f"✔ **Correcta:** {r['correcta']}")

                st.markdown("**📝 Explicación:**")
                st.markdown(preparar_latex_para_streamlit(r["explicacion"])) 
                st.markdown("---")

            st.markdown("### 🏁 Resumen Final")
            col_nota_bot, col_info_bot = st.columns([1, 2])
            with col_nota_bot:
                st.metric("Calificación Final ", f"{nota_final} / 20 pts")
            
            st.divider()

            col_pdf, col_nuevo = st.columns(2)
            with col_pdf:
                pdf_bytes = generar_pdf_informe_quiz(st.session_state.respuestas_usuario, nota_final)
                pdf_bytes = bytes(pdf_bytes) if isinstance(pdf_bytes, bytearray) else pdf_bytes
                st.download_button(
                    "📥 Descargar informe (PDF)",
                    data=pdf_bytes,
                    file_name=f"informe_quiz_{str(nota_final).replace('.', '_')}.pdf",
                    mime="application/pdf",
                    use_container_width=True
                )
            with col_nuevo:
                if st.button("🔄 Comenzar Nuevo Examen", type="primary", use_container_width=True):
                    st.session_state.quiz_activo = False
                    st.session_state.indice_pregunta = 0
                    st.session_state.respuestas_usuario = []
                    st.rerun()
# =======================================================
# LÓGICA D: TUTOR PREGUNTAS ABIERTAS (NUEVO)
# =======================================================
elif ruta == "d) Tutor: Preguntas Abiertas":
    st.markdown("### 💬 Preguntas Abiertas al Tutor")
    st.markdown("""
    Haz cualquier pregunta teórica. El tutor te responderá **vinculando la teoría con
    los ejercicios y estilos de examen** de nuestra cátedra.
    """)

    if len(st.session_state.historial_tutor_abierto) > AVISO_HISTORIAL_LARGO:
        st.info("💬 **Conversación larga.** Para respuestas más precisas, considera usar **Reiniciar** en el menú y empezar una nueva.")

    for mensaje in st.session_state.historial_tutor_abierto:
        with st.chat_message(mensaje["role"]):
            st.markdown(mensaje["content"])

    if prompt := st.chat_input("Ej. puedes preguntar por resumen o explicación corta de cualquier tema a partir de las ejercicios del profesor"):
        st.session_state.historial_tutor_abierto.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        with st.chat_message("assistant"):
            with st.spinner("Consultando guías de la cátedra..."):
                ultimos = st.session_state.historial_tutor_abierto[-MAX_MENSAJES_HISTORIAL_TUTOR:]
                historial_texto = "\n".join([f"{m['role']}: {m['content']}" for m in ultimos])
                respuesta_tutor = generar_respuesta_tutor_abierto(prompt, historial_texto)
                st.markdown(respuesta_tutor)

        st.session_state.historial_tutor_abierto.append({"role": "assistant", "content": respuesta_tutor})
