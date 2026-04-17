-- Vincula eventos de uso al participante (para panel Seguimos: debilidades, mapa de calor).
-- Ejecutar en Supabase → SQL Editor después de `supabase_usage_events.sql` y `supabase_estudiantes.sql`.

ALTER TABLE public.app_usage_event
  ADD COLUMN IF NOT EXISTS estudiante_id uuid REFERENCES public.app_estudiante (id) ON DELETE SET NULL;

CREATE INDEX IF NOT EXISTS idx_app_usage_event_estudiante_created
  ON public.app_usage_event (estudiante_id, created_at DESC);

COMMENT ON COLUMN public.app_usage_event.estudiante_id IS 'Si hay sesión, el evento se asocia al participante; NULL si anónimo.';

-- Reemplaza la firma de la función para aceptar estudiante opcional.
DROP FUNCTION IF EXISTS public.insert_usage_event(text, jsonb);

CREATE OR REPLACE FUNCTION public.insert_usage_event(
  p_modo text,
  p_payload jsonb,
  p_estudiante_id uuid DEFAULT NULL
) RETURNS void
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = public
AS $$
BEGIN
  IF p_modo IS NULL OR btrim(p_modo) = '' THEN
    RETURN;
  END IF;
  INSERT INTO public.app_usage_event (modo, payload, estudiante_id)
  VALUES (btrim(p_modo), COALESCE(p_payload, '{}'::jsonb), p_estudiante_id);
END;
$$;

GRANT EXECUTE ON FUNCTION public.insert_usage_event(text, jsonb, uuid) TO service_role;
