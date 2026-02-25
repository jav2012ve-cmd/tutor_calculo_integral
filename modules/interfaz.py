import streamlit as st
from modules.temario import LISTA_TEMAS

def configurar_pagina():
    st.set_page_config(
        page_title="Matemáticas III - Economía UCAB",
        page_icon="📈",
        layout="wide"
    )

def mostrar_sidebar():
    with st.sidebar:
        st.image("https://upload.wikimedia.org/wikipedia/commons/f/f0/Logo_UCAB_H.png", width=200)
        st.markdown("### 🏛️ Escuela de Economía")
        
        seleccion_visual = st.radio(
            "1. Selecciona tu Modo de Estudio:",
            ["a) Entrenamiento (Temario)", 
             "b) Respuesta Guiada (Consultas)", 
             "c) Autoevaluación (Quiz)",
             "d) Tutor: Preguntas Abiertas"],
            index=None,
            key="radio_seleccion"
        )
        
        col1, col2 = st.columns(2)
        with col1:
            if st.button("▶️ Iniciar"):
                st.session_state.modo_actual = seleccion_visual
                st.rerun()
        with col2:
            if st.button("🔄 Reiniciar"):
                st.session_state.modo_actual = None
                st.session_state.messages = []
                st.rerun()
        
        st.divider()
        
        tema_seleccionado = None
        if st.session_state.get("modo_actual") == "a) Entrenamiento (Temario)":
            st.write("### 📘 Temario Detallado")
            if "tema_seleccionado" not in st.session_state:
                st.session_state.tema_seleccionado = LISTA_TEMAS[0]
            
            tema_seleccionado = st.selectbox("Selecciona el punto:", LISTA_TEMAS)
            st.session_state.tema_seleccionado = tema_seleccionado

        return st.session_state.get("modo_actual"), tema_seleccionado

def mostrar_bienvenida():
    st.title("Matemáticas III - Economía UCAB")
    
    st.markdown("""
    <div style="background-color: #f0f2f6; padding: 25px; border-radius: 10px; border-left: 5px solid #00aeef; margin-bottom: 20px;">
        <h4 style="margin-top: 0; color: #0e1117;">🏛️ Bienvenidos al Tutor Inteligente de la Cátedra</h4>
        <p style="color: #31333f;">Este ecosistema académico está diseñado para fortalecer el dominio de las herramientas matemáticas básicas relacionadas con cálculo integral y ecuaciones diferencial para tu formación como economista. Nos enfocamos en dos pilares:</p>
        <ul style="margin-bottom: 10px; color: #31333f;">
            <li><strong>Cálculo Integral:</strong> Métodos de integración integral definida y sus aplicaciones excedentes, áreas, volúmenes de sólidos y probabilidad.</li>
            <li><strong>Ecuaciones Diferenciales (ED):</strong> De primer orden, de orden superior. Modelos de crecimiento natural, Ley de enfriamiento de Newton, estabilidad de precios y ciclos económicos.</li>
        </ul>
    </div>
    
    ### 🛠️ ¿Qué hay de nuevo?
    **¡Hemos optimizado el motor de ejercicios!** Te invitamos a explorar los ajustes de precisión que incorporamos recientemente:
    
    * **Refinamiento en ED Homogéneas:** Se aumentó el número de problemas modelo.
    * **Ecuaciones Lineas y De Bernoulli:** Se aumentó el número de ejercicios modelo.
    * **Modelos de Primer Orden:** Se incorporaron modelos económicos, físicos y biológicos de primer orden.
    * **Contexto Bio-Económico:** Nuevos reactivos sobre dinámicas de población limitada y equilibrio de mercado.
    
    <hr style="margin-top: 20px; margin-bottom: 20px;">
    """, unsafe_allow_html=True)
    
    # Tip dinámico para mejorar la UX
    st.info("💡 **Consejo del Tutor:** Si estás preparando el próximo parcial, te recomendamos iniciar con el modo **'Autoevaluación'** centrándote en los temas de **ED de Orden Superior**.")

