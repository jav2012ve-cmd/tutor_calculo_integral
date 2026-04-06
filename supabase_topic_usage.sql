-- Uso acumulado por tema del temario (una fila por tema ≈ una “columna” lógica).
-- Ejecutar en SQL Editor. Después ejecuta supabase_topic_usage_seed.sql para filas en 0.

CREATE TABLE IF NOT EXISTS public.app_topic_usage (
  topic_key text PRIMARY KEY,
  count bigint NOT NULL DEFAULT 0 CHECK (count >= 0)
);

COMMENT ON TABLE public.app_topic_usage IS 'Conteo de interacciones por tema oficial (LISTA_TEMAS); anónimo.';

CREATE OR REPLACE FUNCTION public.increment_topic_usage_batch(p_topics text[])
RETURNS void
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = public
AS $$
DECLARE
  t text;
BEGIN
  IF p_topics IS NULL THEN
    RETURN;
  END IF;
  FOREACH t IN ARRAY p_topics LOOP
    IF t IS NULL OR btrim(t) = '' THEN
      CONTINUE;
    END IF;
    INSERT INTO public.app_topic_usage (topic_key, count)
    VALUES (btrim(t), 1)
    ON CONFLICT (topic_key)
    DO UPDATE SET count = public.app_topic_usage.count + 1;
  END LOOP;
END;
$$;

ALTER TABLE public.app_topic_usage ENABLE ROW LEVEL SECURITY;

GRANT ALL ON TABLE public.app_topic_usage TO service_role;
GRANT EXECUTE ON FUNCTION public.increment_topic_usage_batch(text[]) TO service_role;
