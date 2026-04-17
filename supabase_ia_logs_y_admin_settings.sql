-- =============================================================================
-- ia_logs: institución / carrera + tabla app_admin_settings (clave panel admin)
-- =============================================================================
-- Ejecutar en Supabase → SQL Editor (tras `supabase_ia_logs.sql` si la tabla
-- aún no incluye estas columnas).
-- =============================================================================

-- -----------------------------------------------------------------------------
-- 1) Columnas en public.ia_logs
-- -----------------------------------------------------------------------------
ALTER TABLE public.ia_logs
  ADD COLUMN IF NOT EXISTS institucion text NOT NULL DEFAULT 'No especificado';

ALTER TABLE public.ia_logs
  ADD COLUMN IF NOT EXISTS carrera text NOT NULL DEFAULT 'No especificado';

COMMENT ON COLUMN public.ia_logs.institucion IS 'Copia al momento del log; segmentación / marketing.';
COMMENT ON COLUMN public.ia_logs.carrera IS 'Copia al momento del log.';

CREATE INDEX IF NOT EXISTS ia_logs_institucion_idx ON public.ia_logs (institucion);

-- -----------------------------------------------------------------------------
-- 2) Tabla de configuración admin (clave para proteger el panel)
-- -----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS public.app_admin_settings (
  id smallint PRIMARY KEY DEFAULT 1,
  clave_acceso text NOT NULL DEFAULT '',
  updated_at timestamptz NOT NULL DEFAULT now(),
  CONSTRAINT app_admin_settings_singleton CHECK (id = 1)
);

COMMENT ON TABLE public.app_admin_settings IS
  'Configuración global del panel admin; fila única (id=1). clave_acceso: secreto comparado por la app.';

COMMENT ON COLUMN public.app_admin_settings.clave_acceso IS
  'Contraseña o token esperado para desbloquear el panel (la app lee vía service_role).';

INSERT INTO public.app_admin_settings (id, clave_acceso)
VALUES (1, '')
ON CONFLICT (id) DO NOTHING;

ALTER TABLE public.app_admin_settings ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS "app_admin_settings_service_role_select" ON public.app_admin_settings;
CREATE POLICY "app_admin_settings_service_role_select"
  ON public.app_admin_settings
  FOR SELECT
  TO service_role
  USING (true);

DROP POLICY IF EXISTS "app_admin_settings_service_role_update" ON public.app_admin_settings;
CREATE POLICY "app_admin_settings_service_role_update"
  ON public.app_admin_settings
  FOR UPDATE
  TO service_role
  USING (true)
  WITH CHECK (true);

DROP POLICY IF EXISTS "app_admin_settings_service_role_insert" ON public.app_admin_settings;
CREATE POLICY "app_admin_settings_service_role_insert"
  ON public.app_admin_settings
  FOR INSERT
  TO service_role
  WITH CHECK (true);

GRANT SELECT, INSERT, UPDATE ON TABLE public.app_admin_settings TO service_role;
