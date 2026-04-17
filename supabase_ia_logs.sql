-- Registro de interacciones usuario–IA (append-only) para trazabilidad y panel Seguimos.
-- Ejecutar en Supabase → SQL Editor después de `supabase_estudiantes.sql` (requiere app_estudiante).

CREATE TABLE IF NOT EXISTS public.ia_logs (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  created_at timestamptz NOT NULL DEFAULT now(),
  estudiante_id uuid REFERENCES public.app_estudiante (id) ON DELETE SET NULL,
  pregunta text NOT NULL DEFAULT '',
  respuesta text NOT NULL DEFAULT '',
  modelo text NOT NULL DEFAULT '',
  institucion text NOT NULL DEFAULT 'Anónimo',
  carrera text NOT NULL DEFAULT 'N/A'
);

COMMENT ON TABLE public.ia_logs IS 'Logs de prompts y respuestas de Gemini; estudiante_id si hay sesión Supabase.';
COMMENT ON COLUMN public.ia_logs.estudiante_id IS 'UUID de app_estudiante cuando el usuario inició sesión; NULL si anónimo.';
COMMENT ON COLUMN public.ia_logs.institucion IS 'Copia al momento del log (marketing / segmentación).';
COMMENT ON COLUMN public.ia_logs.carrera IS 'Copia al momento del log.';

CREATE INDEX IF NOT EXISTS ia_logs_estudiante_id_idx ON public.ia_logs (estudiante_id);
CREATE INDEX IF NOT EXISTS ia_logs_created_at_idx ON public.ia_logs (created_at DESC);
CREATE INDEX IF NOT EXISTS ia_logs_institucion_idx ON public.ia_logs (institucion);

ALTER TABLE public.ia_logs ENABLE ROW LEVEL SECURITY;

GRANT USAGE ON SCHEMA public TO service_role;
GRANT SELECT, INSERT ON TABLE public.ia_logs TO service_role;
