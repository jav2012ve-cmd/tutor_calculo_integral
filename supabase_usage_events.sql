-- Ejecutar en Supabase → SQL Editor (además de supabase_schema.sql).
-- Registro detallado por interacción: modalidad, temas, etc. (payload JSON).

CREATE TABLE IF NOT EXISTS public.app_usage_event (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  created_at timestamptz NOT NULL DEFAULT now(),
  modo text NOT NULL,
  payload jsonb NOT NULL DEFAULT '{}'::jsonb
);

COMMENT ON TABLE public.app_usage_event IS 'Eventos de uso del tutor (detalle en JSON); anónimo.';

CREATE INDEX IF NOT EXISTS idx_app_usage_event_modo ON public.app_usage_event (modo);
CREATE INDEX IF NOT EXISTS idx_app_usage_event_created ON public.app_usage_event (created_at DESC);

CREATE OR REPLACE FUNCTION public.insert_usage_event(p_modo text, p_payload jsonb)
RETURNS void
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = public
AS $$
BEGIN
  IF p_modo IS NULL OR btrim(p_modo) = '' THEN
    RETURN;
  END IF;
  INSERT INTO public.app_usage_event (modo, payload)
  VALUES (btrim(p_modo), COALESCE(p_payload, '{}'::jsonb));
END;
$$;

ALTER TABLE public.app_usage_event ENABLE ROW LEVEL SECURITY;

GRANT ALL ON TABLE public.app_usage_event TO service_role;
GRANT EXECUTE ON FUNCTION public.insert_usage_event(text, jsonb) TO service_role;
