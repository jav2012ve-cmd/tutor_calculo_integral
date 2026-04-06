-- Crea una fila por cada tema con count = 0 (para ver en Table Editor temas “sin estudio”).
-- Ejecutar tras supabase_topic_usage.sql. Si cambia LISTA_TEMAS en temario.py, actualiza esta lista.

INSERT INTO public.app_topic_usage (topic_key, count) VALUES
  ('1.1.1 Integrales Indefinidas Directas', 0),
  ('1.1.2 Cambios de variables (Sustitución)', 0),
  ('1.1.3 División de Polinomios', 0),
  ('1.1.4 Fracciones Simples', 0),
  ('1.1.5 Integral por partes', 0),
  ('1.2.1 Integral Definida', 0),
  ('1.2.2 Áreas entre curvas', 0),
  ('1.2.3 Excedentes del consumidor y productor', 0),
  ('1.2.4 Integrales Impropias', 0),
  ('1.2.5 Volúmenes Sólidos de Revolución', 0),
  ('1.2.6 Integrales dobles', 0),
  ('1.2.7 Funciones de Distribución de probabilidad', 0),
  ('2.1.1 ED 1er Orden: Separación de Variables', 0),
  ('2.1.2 ED 1er Orden: Homogéneas', 0),
  ('2.1.3 ED 1er Orden: Exactas', 0),
  ('2.1.4 ED 1er Orden: Lineales', 0),
  ('2.1.5 ED 1er Orden: Bernoulli', 0),
  ('2.2.1 ED Orden Superior: Homogéneas', 0),
  ('2.2.2 ED Orden Superior: No Homogéneas', 0),
  ('2.3.1 Aplicaciones de Ecuaciones Diferenciales de primer orden', 0),
  ('2.3.2 Aplicaciones de Ecuaciones Diferenciales de Orden superior', 0)
ON CONFLICT (topic_key) DO NOTHING;
