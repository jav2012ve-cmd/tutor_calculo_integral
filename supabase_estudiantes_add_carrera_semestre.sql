-- Añade carrera y semestre al registro de participantes.
-- Ejecutar en Supabase → SQL Editor (una vez por proyecto).

ALTER TABLE public.app_estudiante
  ADD COLUMN IF NOT EXISTS carrera text,
  ADD COLUMN IF NOT EXISTS semestre text;

COMMENT ON COLUMN public.app_estudiante.carrera IS 'Carrera o programa que cursa el participante.';
COMMENT ON COLUMN public.app_estudiante.semestre IS 'Semestre u orden académico (texto libre, ej. 4, 2025-1).';

ALTER TABLE public.app_estudiante DROP CONSTRAINT IF EXISTS app_estudiante_carrera_len_chk;
ALTER TABLE public.app_estudiante
  ADD CONSTRAINT app_estudiante_carrera_len_chk CHECK (
    carrera IS NULL OR char_length(btrim(carrera)) BETWEEN 2 AND 120
  );

ALTER TABLE public.app_estudiante DROP CONSTRAINT IF EXISTS app_estudiante_semestre_len_chk;
ALTER TABLE public.app_estudiante
  ADD CONSTRAINT app_estudiante_semestre_len_chk CHECK (
    semestre IS NULL OR char_length(btrim(semestre)) BETWEEN 1 AND 40
  );
