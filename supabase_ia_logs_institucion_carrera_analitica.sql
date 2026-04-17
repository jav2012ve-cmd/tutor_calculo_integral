-- Actualización de la tabla de logs para analítica (SQL Editor de Supabase).
-- Columnas nullable; la app envía texto (p. ej. «No especificado»).

ALTER TABLE public.ia_logs
  ADD COLUMN IF NOT EXISTS institucion text,
  ADD COLUMN IF NOT EXISTS carrera text;

CREATE INDEX IF NOT EXISTS idx_ia_logs_institucion ON public.ia_logs (institucion);
