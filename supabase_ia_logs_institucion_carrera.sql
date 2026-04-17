-- Segmentación en ia_logs (marketing / analítica sin cruzar app_estudiante).
-- Ejecutar en Supabase → SQL Editor tras `supabase_ia_logs.sql`.

ALTER TABLE public.ia_logs
  ADD COLUMN IF NOT EXISTS institucion text NOT NULL DEFAULT 'Anónimo';

ALTER TABLE public.ia_logs
  ADD COLUMN IF NOT EXISTS carrera text NOT NULL DEFAULT 'N/A';

COMMENT ON COLUMN public.ia_logs.institucion IS 'Copia al momento del log desde el perfil (o Anónimo).';
COMMENT ON COLUMN public.ia_logs.carrera IS 'Copia al momento del log desde el perfil (o N/A).';

CREATE INDEX IF NOT EXISTS ia_logs_institucion_idx ON public.ia_logs (institucion);
