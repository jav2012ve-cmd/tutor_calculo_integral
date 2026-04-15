-- Migración: tabla app_estudiante creada con display_name / codigo_opcional
-- → esquema participante (nombre, cédula, institución, fecha_nacimiento).
-- Ejecutar en SQL Editor UNA VEZ. Revisa datos antes si ya hay filas.

-- 1) Nombre (copia desde display_name si existía)
ALTER TABLE public.app_estudiante ADD COLUMN IF NOT EXISTS nombre text;
DO $$
BEGIN
  IF EXISTS (
    SELECT 1 FROM information_schema.columns
    WHERE table_schema = 'public' AND table_name = 'app_estudiante' AND column_name = 'display_name'
  ) THEN
    UPDATE public.app_estudiante SET nombre = display_name WHERE nombre IS NULL;
  END IF;
END;
$$;

-- 2) Campos nuevos (nullable primero; rellena y luego aplica NOT NULL manualmente si quieres)
ALTER TABLE public.app_estudiante ADD COLUMN IF NOT EXISTS cedula text;
ALTER TABLE public.app_estudiante ADD COLUMN IF NOT EXISTS institucion text;
ALTER TABLE public.app_estudiante ADD COLUMN IF NOT EXISTS fecha_nacimiento date;

-- 3) Índice único por cédula normalizada (solo si no existe otro con el mismo nombre)
DROP INDEX IF EXISTS public.app_estudiante_cedula_norm_uidx;
CREATE UNIQUE INDEX IF NOT EXISTS app_estudiante_cedula_norm_uidx
  ON public.app_estudiante (regexp_replace(lower(trim(cedula)), '\s+', '', 'g'))
  WHERE cedula IS NOT NULL AND btrim(cedula) <> '';

-- 4) (Opcional) eliminar columnas antiguas cuando ya no las use la app:
-- ALTER TABLE public.app_estudiante DROP COLUMN IF EXISTS codigo_opcional;
-- ALTER TABLE public.app_estudiante DROP COLUMN IF EXISTS display_name;
