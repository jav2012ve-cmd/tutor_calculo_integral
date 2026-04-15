-- Ejecutar en SQL Editor si la app no escribe en app_module_usage (tabla siempre vacía).
-- Refuerza permisos para la API REST con la clave service_role.

GRANT USAGE ON SCHEMA public TO service_role;
GRANT ALL ON TABLE public.app_module_usage TO service_role;
GRANT EXECUTE ON FUNCTION public.increment_module_usage(text) TO service_role;

-- Tras crear public.app_estudiante (ver supabase_estudiantes.sql):
GRANT SELECT, INSERT, UPDATE, DELETE ON TABLE public.app_estudiante TO service_role;
