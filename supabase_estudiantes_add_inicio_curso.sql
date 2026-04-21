-- Añade fecha de inicio del curso al perfil del participante.
-- Ejecutar en Supabase -> SQL Editor (una vez por proyecto).

ALTER TABLE public.app_estudiante
  ADD COLUMN IF NOT EXISTS fecha_inicio_curso date;

COMMENT ON COLUMN public.app_estudiante.fecha_inicio_curso IS
  'Fecha de inicio oficial del curso que está cursando el participante.';

ALTER TABLE public.app_estudiante DROP CONSTRAINT IF EXISTS app_estudiante_inicio_curso_chk;
ALTER TABLE public.app_estudiante
  ADD CONSTRAINT app_estudiante_inicio_curso_chk CHECK (
    fecha_inicio_curso IS NULL OR fecha_inicio_curso <= CURRENT_DATE
  );
