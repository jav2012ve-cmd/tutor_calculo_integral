-- Registro de participantes (estudiantes universitarios).
-- Ejecutar en Supabase → SQL Editor (proyecto nuevo o tras respaldar datos).
-- Si ya tenías la tabla antigua, ejecuta antes `supabase_estudiantes_migrate_participante.sql`.

CREATE TABLE IF NOT EXISTS public.app_estudiante (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  email text NOT NULL,
  password_hash text NOT NULL,
  nombre text NOT NULL,
  cedula text NOT NULL,
  institucion text NOT NULL,
  fecha_nacimiento date NOT NULL,
  created_at timestamptz NOT NULL DEFAULT now(),
  updated_at timestamptz NOT NULL DEFAULT now(),
  CONSTRAINT app_estudiante_email_format_chk CHECK (
    email ~* '^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$'
  ),
  CONSTRAINT app_estudiante_nombre_len_chk CHECK (char_length(btrim(nombre)) BETWEEN 2 AND 200),
  CONSTRAINT app_estudiante_cedula_len_chk CHECK (char_length(btrim(cedula)) BETWEEN 5 AND 32),
  CONSTRAINT app_estudiante_institucion_len_chk CHECK (char_length(btrim(institucion)) BETWEEN 2 AND 200),
  CONSTRAINT app_estudiante_password_hash_len_chk CHECK (char_length(password_hash) >= 20),
  CONSTRAINT app_estudiante_fecha_nac_chk CHECK (fecha_nacimiento < CURRENT_DATE)
);

COMMENT ON TABLE public.app_estudiante IS 'Participantes: nombre, cédula, correo, institución, fecha nacimiento; contraseña solo hash bcrypt.';

CREATE UNIQUE INDEX IF NOT EXISTS app_estudiante_email_lower_uidx
  ON public.app_estudiante (lower(trim(email)));

CREATE UNIQUE INDEX IF NOT EXISTS app_estudiante_cedula_norm_uidx
  ON public.app_estudiante (regexp_replace(lower(trim(cedula)), '\s+', '', 'g'));

ALTER TABLE public.app_estudiante ENABLE ROW LEVEL SECURITY;

GRANT USAGE ON SCHEMA public TO service_role;
GRANT SELECT, INSERT, UPDATE, DELETE ON TABLE public.app_estudiante TO service_role;
