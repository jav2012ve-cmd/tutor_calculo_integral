-- =============================================================================
-- Admin: columnas ia_logs + RPC métricas + RLS / permisos para service_role
-- =============================================================================
-- Ejecutar en Supabase → SQL Editor (proyecto con `ia_logs` y `app_usage_event`).
-- Orden sugerido: tras `supabase_estudiantes.sql`, `supabase_ia_logs.sql`,
-- `supabase_usage_events.sql` (y migración de `estudiante_id` si aplica).
--
-- Nota Supabase: la clave **service_role** en PostgREST **omite RLS** por defecto.
-- Aun así se dejan GRANTs y políticas explícitas para INSERT (incl. institucion/carrera)
-- y una política permisiva para service_role si en el futuro se consulta con otro contexto.
-- =============================================================================

-- -----------------------------------------------------------------------------
-- 1) Columnas en ia_logs (segmentación sin joins a app_estudiante)
-- -----------------------------------------------------------------------------
ALTER TABLE public.ia_logs
  ADD COLUMN IF NOT EXISTS institucion text NOT NULL DEFAULT 'Anónimo';

ALTER TABLE public.ia_logs
  ADD COLUMN IF NOT EXISTS carrera text NOT NULL DEFAULT 'N/A';

COMMENT ON COLUMN public.ia_logs.institucion IS 'Copia al momento del log; segmentación / marketing.';
COMMENT ON COLUMN public.ia_logs.carrera IS 'Copia al momento del log.';

CREATE INDEX IF NOT EXISTS ia_logs_institucion_idx ON public.ia_logs (institucion);

-- -----------------------------------------------------------------------------
-- 2) Permisos de tabla: service_role puede escribir y leer (incl. nuevas columnas)
-- -----------------------------------------------------------------------------
GRANT USAGE ON SCHEMA public TO service_role;
GRANT SELECT, INSERT ON TABLE public.ia_logs TO service_role;

-- -----------------------------------------------------------------------------
-- 3) RLS: políticas explícitas para service_role (INSERT y SELECT)
-- -----------------------------------------------------------------------------
ALTER TABLE public.ia_logs ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS "ia_logs_service_role_insert" ON public.ia_logs;
CREATE POLICY "ia_logs_service_role_insert"
  ON public.ia_logs
  FOR INSERT
  TO service_role
  WITH CHECK (true);

DROP POLICY IF EXISTS "ia_logs_service_role_select" ON public.ia_logs;
CREATE POLICY "ia_logs_service_role_select"
  ON public.ia_logs
  FOR SELECT
  TO service_role
  USING (true);

-- -----------------------------------------------------------------------------
-- 4) RPC: resumen de métricas para panel admin
-- -----------------------------------------------------------------------------
DROP FUNCTION IF EXISTS public.obtener_metricas_admin();

CREATE OR REPLACE FUNCTION public.obtener_metricas_admin()
RETURNS jsonb
LANGUAGE sql
STABLE
SECURITY DEFINER
SET search_path = public
AS $$
  SELECT jsonb_build_object(
    'total_estudiantes_unicos_registrados',
    (SELECT COUNT(*)::bigint FROM public.app_estudiante),
    'total_estudiantes_unicos_con_log_ia',
    (SELECT COUNT(DISTINCT estudiante_id)::bigint
     FROM public.ia_logs
     WHERE estudiante_id IS NOT NULL),
    'total_interacciones_ia_logs',
    (SELECT COUNT(*)::bigint FROM public.ia_logs),
    'eventos_por_modo',
    COALESCE(
      (
        SELECT jsonb_object_agg(sub.modo, sub.cnt)
        FROM (
          SELECT modo, COUNT(*)::bigint AS cnt
          FROM public.app_usage_event
          GROUP BY modo
        ) AS sub
      ),
      '{}'::jsonb
    )
  );
$$;

COMMENT ON FUNCTION public.obtener_metricas_admin() IS
  'Resumen admin: estudiantes (registrados y con log), total filas ia_logs, conteos por modo en app_usage_event.';

GRANT EXECUTE ON FUNCTION public.obtener_metricas_admin() TO service_role;

-- Opcional: no exponer a anon/authenticated (ajusta según tu modelo de seguridad)
REVOKE ALL ON FUNCTION public.obtener_metricas_admin() FROM PUBLIC;
