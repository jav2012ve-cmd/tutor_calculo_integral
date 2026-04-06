-- Ejecutar en SQL Editor si `app_usage_event` existe pero NO tiene la columna `payload`.
-- (Ocurre si la tabla se creó a mano o con un script viejo antes de supabase_usage_events.sql.)

ALTER TABLE public.app_usage_event
  ADD COLUMN IF NOT EXISTS payload jsonb NOT NULL DEFAULT '{}'::jsonb;

COMMENT ON COLUMN public.app_usage_event.payload IS 'Detalle JSON: temas, modalidad quiz, tema_detectado, etc.';

-- Asegura que la función RPC inserte en (modo, payload):
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

GRANT EXECUTE ON FUNCTION public.insert_usage_event(text, jsonb) TO service_role;
