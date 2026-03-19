# Lista de mejoras priorizadas — Tutor Matemáticas III

## Prioridad 1 — Crítico (corregir ya)

| # | Mejora | Dónde | Motivo |
|---|--------|--------|--------|
| 1.1 | **Unificar códigos de tema** entre `temario.py` y `banco_preguntas.py`. En temario: Volúmenes = 1.2.5, Integrales Dobles = 1.2.6. En banco: Volúmenes = 1.2.4, Integrales Dobles = 1.2.5. | `modules/banco_preguntas.py` | Filtrado por tema y simulacros por parcial pueden no coincidir; ejercicios de “Volúmenes” o “Integrales dobles” pueden no aparecer donde el usuario espera. |
| 1.2 | **Documentar y validar API Key** (Gemini). Dejar claro en README o en pantalla que se requiere `GOOGLE_API_KEY` en Secrets; opcional: mensaje más claro si falta (ej. “Configura la clave en .streamlit/secrets.toml”). | `modules/ia_core.py`, README | La app hace `st.stop()` sin indicar cómo solucionarlo; dificulta el primer uso. |

---

## Prioridad 2 — Alto (impacto directo en uso)

| # | Mejora | Dónde | Motivo |
|---|--------|--------|--------|
| 2.1 | **Añadir README** con: descripción del proyecto, instalación (`pip install -r requirements.txt`), ejecución (`streamlit run app.py`), configuración de Secrets (API Key), requisitos (Python 3.x). | Raíz del proyecto | Facilita mantenimiento, despliegue y que otros profesores/desarrolladores puedan correr la app. |
| 2.2 | **Limpiar dependencias**: quitar `fpdf` de `requirements.txt` si no se usará, o implementar exportar resultado del quiz a PDF y dejar la dependencia. | `requirements.txt`, opcionalmente `app.py` | Evita dependencias muertas y confusión; si se usa fpdf, añadir la funcionalidad da valor. |
| 2.3 | **Reset de estado al cambiar de modo**: al elegir otro modo en el sidebar (ej. de Quiz a Entrenamiento), limpiar o reiniciar estados del modo anterior (quiz_activo, entrenamiento_activo, consulta_step, etc.) para evitar comportamientos raros o datos residuales. | `app.py`, `modules/interfaz.py` | Mejora la experiencia y evita bugs al alternar modos. |

---

## Prioridad 3 — Medio (calidad y robustez)

| # | Mejora | Dónde | Motivo |
|---|--------|--------|--------|
| 3.1 | **Manejo explícito de “solo texto” en Respuesta Guiada**: comprobar `if imagen_subida` antes de `Image.open(imagen_subida)` y solo entonces abrir la imagen; dejar claro en código que el flujo texto-only no pasa por imagen. | `app.py` (bloque Respuesta Guiada) | Código más claro y menos propenso a errores si luego se añaden más casos. |
| 3.2 | **Mensajes de error más claros** cuando la IA no devuelve JSON válido (tutoría, análisis de problema o preguntas de quiz): indicar “No se pudo interpretar la respuesta; intenta de nuevo” en lugar de fallos genéricos. | `app.py` (generar_tutor_paso_a_paso, analizar_problema_usuario, flujo quiz) | El usuario entiende mejor qué hacer ante fallos de IA. |
| 3.3 | **Configuración centralizada**: mover número de ejercicios (5), intentos máximos de IA (3), tiempo de espera ante 429, etc. a constantes o a un pequeño módulo de config (o `.streamlit/config.toml` donde aplique). | Nuevo `config.py` o sección al inicio de `app.py` | Facilita ajustar la app sin tocar la lógica dispersa. |
| 3.4 | **Corregir typo en banco**: en al menos una pregunta de Integrales Impropias aparece `"Converge a 2$"` (falta backslash o sobra `$`). Revisar y normalizar formato LaTeX en respuestas. | `modules/banco_preguntas.py` | Evita que se muestre “2$” como texto suelto en la interfaz. |

---

## Prioridad 4 — Bajo (mejoras deseables)

| # | Mejora | Dónde | Motivo |
|---|--------|--------|--------|
| 4.1 | **Exportar resultado del quiz a PDF**: si se mantiene `fpdf`, implementar botón “Descargar informe PDF” en la pantalla de resultados del quiz (preguntas, respuestas, explicaciones, nota). | `app.py`, posible helper en `modules/` | Valor añadido para el estudiante y el profesor. |
| 4.2 | **Type hints** en funciones principales** (generar_contenido_seguro, limpiar_json, analizar_problema_usuario, etc.). | `app.py`, `modules/*.py` | Mejor legibilidad y soporte del IDE. |
| 4.3 | **Tests básicos**: al menos tests unitarios para `limpiar_json`, `obtener_preguntas_fijas` y que los temas en temario y banco coincidan (nombres o códigos). | Carpeta `tests/` | Permite refactorizar con más seguridad. |
| 4.4 | **Límite de historial en Tutor abierto**: limitar a N mensajes (ej. últimos 10) el contexto enviado a la IA o mostrar aviso “Conversación larga; considera iniciar una nueva” para controlar coste y tamaño de contexto. | `app.py` (modo Tutor Preguntas Abiertas) | Control de uso de API y comportamiento más estable. |
| 4.5 | **Página “Acerca de” o ayuda en sidebar**: breve descripción de cada modo (Entrenamiento, Respuesta Guiada, Quiz, Tutor abierto) y enlace a instrucciones si se añaden. | `modules/interfaz.py` | Mejora la usabilidad para nuevos usuarios. |

---

## Resumen por prioridad

- **P1 (Crítico):** 2 ítems — temas + API Key/documentación.
- **P2 (Alto):** 3 ítems — README, dependencias, estado al cambiar de modo.
- **P3 (Medio):** 4 ítems — flujo imagen/texto, errores IA, config, typo LaTeX.
- **P4 (Bajo):** 5 ítems — PDF quiz, type hints, tests, límite historial, ayuda.

Recomendación: abordar en orden P1 → P2 → P3 → P4; dentro de cada prioridad, el orden de la tabla es una sugerencia de secuencia.
