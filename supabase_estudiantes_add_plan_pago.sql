-- Agrega plan de pago al perfil de estudiante.
alter table if exists public.app_estudiante
add column if not exists plan_pago text not null default 'free';

-- Normaliza posibles valores nulos o vacíos previos.
update public.app_estudiante
set plan_pago = 'free'
where plan_pago is null or btrim(plan_pago) = '';

-- Restringe valores permitidos (ajustable según negocio).
do $$
begin
  if not exists (
    select 1
    from pg_constraint
    where conname = 'app_estudiante_plan_pago_chk'
  ) then
    alter table public.app_estudiante
    add constraint app_estudiante_plan_pago_chk
    check (plan_pago in ('free', 'pro'));
  end if;
end$$;
