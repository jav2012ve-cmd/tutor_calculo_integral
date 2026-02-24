import streamlit as st
import json
import random 
import time
import re   
from PIL import Image
from modules import ia_core, interfaz, temario, banco_preguntas, banco_muestras

# --- 1. CONFIGURACIÓN INICIAL ---
interfaz.configurar_pagina()

if not ia_core.configurar_gemini():
    st.stop()

model, nombre_modelo = ia_core.iniciar_modelo()

# =======================================================
# FUNCIONES DE SEGURIDAD Y UTILIDADES
# =======================================================

def generar_contenido_seguro(prompt_parts, intentos_max=3):
    """
    Intenta llamar a la IA con texto o imágenes. 
    Soporta lista de partes (prompt + imagen) o solo texto.
    """
    errores_recientes = ""
    for i in range(intentos_max):
        try:
            return model.generate_content(prompt_parts)
        except Exception as e:
            errores_recientes = str(e)
            if "429" in str(e):
                tiempo_espera = 4 * (i + 1)
                st.toast(f"🚦 Tráfico alto. Reintentando en {tiempo_espera}s...", icon="⏳")
                time.sleep(tiempo_espera)
            else:
                time.sleep(1)
    
    st.error(f"❌ Error de conexión: {errores_recientes}")
    return None

def limpiar_json(texto):
    """
    Limpieza quirúrgica para respuestas con LaTeX.
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

import random
import json
import streamlit as st

def generar_tutor_paso_a_paso(pregunta_texto, tema):
    """ Genera la tutoría con 4 opciones. Mantiene estructura JSON completa y evita errores de tipo. """
    
    prompt = f"""
    Actúa como un profesor experto de cálculo de la UCAB. Para el siguiente ejercicio de {tema}:
    "{pregunta_texto}"
    
    Genera un objeto JSON estricto.
    REGLAS:
    1. EXACTAMENTE 4 estrategias (una correcta y tres distractores).
    2. El "indice_correcta" debe variar entre 0, 1, 2 y 3.
    3. Usa LaTeX puro sin $$.
    
    Estructura JSON:
    {{
        "estrategias": ["Opción 1", "Opción 2", "Opción 3", "Opción 4"],
        "indice_correcta": 0,
        "feedback_estrategia": "Texto explicativo detallado",
        "paso_intermedio": "LaTeX",
        "resultado_final": "LaTeX"
    }}
    """
    
    response = generar_contenido_seguro(prompt)
    
    if response:
        try:
            # 1. Limpiamos y cargamos a diccionario
            texto_ia = limpiar_json(response.text)
            datos = json.loads(texto_ia)
            
            # 2. PROCESO DE ALEATORIEDAD Y BLINDAJE
            opciones = datos.get("estrategias", [])
            
            # Aseguramos 4 elementos para que el st.radio de la interfaz no explote
            while len(opciones) < 4:
                opciones.append(f"Planteamiento alternativo {len(opciones)+1}")
            
            # Recuperamos la correcta para re-indexar tras el shuffle
            idx_ia = datos.get("indice_correcta", 0)
            correcta_texto = opciones[idx_ia] if idx_ia < len(opciones) else opciones[0]
            
            # Barajamos las opciones (Aleatoriedad Real)
            random.shuffle(opciones)
            
            # Actualizamos el índice real basado en la nueva posición
            datos["estrategias"] = opciones
            datos["indice_correcta"] = opciones.index(correcta_texto)
            
            # 3. RETORNO COMPATIBLE: Devolvemos String
            return json.dumps(datos)
            
        except Exception as e:
            # En caso de error de parseo, enviamos un JSON con estructura mínima 
            # para que st.radio(["Error...", ...]) funcione y no de Traceback
            error_fallback = {
                "estrategias": ["Error al generar opciones", "Reintente", "...", "..."],
                "indice_correcta": 0,
                "feedback_estrategia": f"Detalle: {str(e)}",
                "paso_intermedio": "",
                "resultado_final": ""
            }
            return json.dumps(error_fallback)
            
    return None
    
def analizar_problema_usuario(texto_usuario, imagen_usuario=None):
    """
    Analiza un problema subido por el alumno (Texto o Imagen).
    Versión corregida: Evita el error 'must be str, not dict'.
    """
    prompt_base = """
    Actúa como un Tutor Experto de Matemáticas III de la UCAB.
    
    OBJETIVO: Generar una guía paso a paso en formato JSON estricto.

    REGLAS DE CONTENIDO:
    1. Genera EXACTAMENTE 4 estrategias (una correcta y tres distractores).
    2. El "indice_correcta" debe ser un número entre 0 y 3.
    3. No uses siempre el mismo índice para la respuesta correcta.

    Estructura JSON:
    {
        "tema_detectado": "Nombre",
        "enunciado_latex": "Enunciado",
        "estrategias": ["A", "B", "C", "D"],
        "indice_correcta": 0,
        "feedback_estrategia": "Texto",
        "paso_intermedio": "LaTeX",
        "resultado_final": "LaTeX"
    }
    """
    
    contenido = [prompt_base]
    if texto_usuario:
        contenido.append(f"Enunciado: {texto_usuario}")
    if imagen_usuario:
        contenido.append(imagen_usuario)

    response = generar_contenido_seguro(contenido)
    
    if response:
        try:
            # 1. Obtenemos el texto limpio de la IA
            texto_limpio = limpiar_json(response.text)
            
            # 2. Convertimos a diccionario para manipular la aleatoriedad
            datos = json.loads(texto_limpio)
            
            # --- LÓGICA DE ALEATORIEDAD (El Shuffle) ---
            opciones = datos["estrategias"]
            # Aseguramos 4 opciones por si la IA falla
            while len(opciones) < 4:
                opciones.append("Planteamiento alternativo genérico")
            
            texto_correcta = opciones[datos["indice_correcta"]]
            random.shuffle(opciones)
            datos["estrategias"] = opciones
            datos["indice_correcta"] = opciones.index(texto_correcta)
            
            # 3. ¡IMPORTANTE! Devolvemos un STRING de JSON para que la 
            # función que llama a esta no explote al intentar parsear.
            return json.dumps(datos)
            
        except Exception as e:
            st.error(f"Error procesando la respuesta del tutor: {e}")
            return None
    return None
def generar_respuesta_tutor_abierto(pregunta_usuario, historial_previo):
    """
    NUEVA FUNCIÓN: Tutor de Preguntas Abiertas.
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

        if st.button("⚡ Iniciar Sesión (5 Ejercicios)", type="primary", use_container_width=True):
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
                        faltantes = 5 - len(lista_entrenamiento)
                        if faltantes > 0:
                            prompt_train = temario.generar_prompt_quiz(temas_entrenamiento, faltantes)
                            respuesta_ia = generar_contenido_seguro(prompt_train)
                            
                            if respuesta_ia:
                                preguntas_ia = limpiar_json(respuesta_ia.text)
                                if preguntas_ia: 
                                    lista_entrenamiento.extend(preguntas_ia)
                        
                        if not lista_entrenamiento:
                            st.error("No se encontraron preguntas. Intenta con otro tema.")
                        else:
                            random.shuffle(lista_entrenamiento)
                            st.session_state.entrenamiento_lista = lista_entrenamiento[:5]
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
            
            st.progress((idx + 1) / 5, text=f"Ejercicio {idx + 1} de 5")
            st.markdown(f"**Tema:** `{ejercicio.get('tema', 'General')}`")
            st.markdown(f"### {ejercicio['pregunta']}")
            st.divider()

# --- LLAMADA A LA IA TUTOR ---
            if st.session_state.entrenamiento_data_ia is None:
                with st.spinner("🧠 El profesor está analizando el mejor camino de resolución..."):
                    datos_tutor = generar_tutor_paso_a_paso(ejercicio['pregunta'], ejercicio.get('tema', 'Cálculo'))
                    if datos_tutor:
                        st.session_state.entrenamiento_data_ia = datos_tutor
                        st.rerun()
                    else:
                        st.error("Error conectando con el tutor IA. Saltando ejercicio.")
                        st.session_state.entrenamiento_idx += 1
                        time.sleep(2)
                        st.rerun()
            
            # --- CORRECCIÓN AQUÍ: Convertir el texto a diccionario ---
            data_ia = st.session_state.entrenamiento_data_ia
            if isinstance(data_ia, str):
                try:
                    tutor = json.loads(data_ia)
                except:
                    st.error("Error al procesar la estrategia. Reintentando...")
                    st.session_state.entrenamiento_data_ia = None
                    st.rerun()
            else:
                tutor = data_ia

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
                        # Procesar imagen si existe
                        img_pil = Image.open(imagen_subida) if imagen_subida else None
                        
                        # Llamada a la IA con la función de análisis
                        datos_problema = analizar_problema_usuario(texto_subido, img_pil)
                        
                        if datos_problema:
                            st.session_state.consulta_data = datos_problema
                            st.session_state.consulta_step = 1
                            st.session_state.consulta_validada = False
                            exito_analisis = True
                        else:
                            st.error("No pude entender el problema. Intenta mejorar la foto o el texto.")
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
                st.session_state.config_cant = 5 
                st.session_state.trigger_quiz = True
                st.rerun()
        with col2:
            if st.button("🏆 Generar Segundo Parcial (Simulacro)", use_container_width=True):
                st.session_state.config_temas = temario.TEMAS_PARCIAL_2
                st.session_state.config_cant = 5
                st.session_state.trigger_quiz = True
                st.rerun()

        with st.expander("⚙️ Personalizado"):
            temas_custom = st.multiselect("Temas:", temario.LISTA_TEMAS)
            if st.button("▶️ Iniciar Quiz Custom"):
                if not temas_custom:
                    st.error("Selecciona tema.")
                else:
                    st.session_state.config_temas = temas_custom
                    st.session_state.config_cant = 5
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
                         st.error("No se pudieron generar preguntas.")
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
            st.markdown(f"#### {pregunta_data['pregunta']}")
            st.divider()
            
            # 2. RENDERIZADO DE LAS OPCIONES (VISUAL)
            # Esto corrige el problema de LaTeX en los radio buttons.
            # Mostramos las opciones formateadas con Markdown primero.
            st.write("Opciones:")
            col_ops = st.columns(2)
            opciones_completas = pregunta_data['opciones']
            
            for i, opcion_texto in enumerate(opciones_completas):
                # Extraemos la letra si existe formato "A) ..." para negrita
                if ")" in opcion_texto:
                    letra, resto = opcion_texto.split(")", 1)
                    texto_mostrar = f"**{letra})** {resto}"
                else:
                    texto_mostrar = opcion_texto

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
                    st.write(ultimo_dato['explicacion'])
                
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
                st.info("💡 **Recordatorio:** Presiona `Ctrl + P` para guardar.")

            st.divider()
            st.subheader("📄 Detalle del Examen")

            for i, r in enumerate(st.session_state.respuestas_usuario):
                st.markdown(f"#### 🔹 Pregunta {i+1} ({r['puntos']} pts)")
                st.markdown(r['pregunta']) 
                
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
                st.write(r['explicacion']) 
                st.markdown("---")

            st.markdown("### 🏁 Resumen Final")
            col_nota_bot, col_info_bot = st.columns([1, 2])
            with col_nota_bot:
                st.metric("Calificación Final ", f"{nota_final} / 20 pts")
            
            st.divider()

            if st.button("🔄 Comenzar Nuevo Examen", type="primary"):
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

    # Mostrar historial de chat
    for mensaje in st.session_state.historial_tutor_abierto:
        with st.chat_message(mensaje["role"]):
            st.markdown(mensaje["content"])

    # Input del usuario (Texto actualizado)
    if prompt := st.chat_input("Ej. puedes preguntar por resumen o explicación corta de cualquier tema a partir de las ejercicios del profesor"):
        # 1. Guardar y mostrar mensaje usuario
        st.session_state.historial_tutor_abierto.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        # 2. Generar respuesta con la IA
        with st.chat_message("assistant"):
            with st.spinner("Consultando guías de la cátedra..."):
                # Preparamos contexto del chat previo
                historial_texto = "\n".join([f"{m['role']}: {m['content']}" for m in st.session_state.historial_tutor_abierto[-4:]])
                
                # Llamamos a la función del tutor (Asegúrate de haber hecho el PASO 2)
                respuesta_tutor = generar_respuesta_tutor_abierto(prompt, historial_texto)
                
                st.markdown(respuesta_tutor)
                
        # 3. Guardar respuesta asistente

        st.session_state.historial_tutor_abierto.append({"role": "assistant", "content": respuesta_tutor})












