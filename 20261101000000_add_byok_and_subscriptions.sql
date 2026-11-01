-- JAI subscription entitlement state. BYOK API keys are stored only in the
-- user's browser and are never written to this database.

create table if not exists public.jai_subscriptions (
    user_id uuid primary key references auth.users(id) on delete cascade,
    stripe_customer_id text,
    stripe_subscription_id text,
    status text not null default 'inactive',
    current_period_end bigint,
    stripe_event_created bigint,
    stripe_event_id text,
    updated_at timestamptz not null default now()
);

alter table public.jai_subscriptions enable row level security;
revoke all on public.jai_subscriptions from anon, authenticated;
grant all on public.jai_subscriptions to service_role;

-- Only the server's service-role key may call this signed-webhook writer.
-- Older Stripe events cannot overwrite newer subscription states.
create or replace function public.jai_update_subscription(
    p_user_id uuid,
    p_stripe_customer_id text,
    p_stripe_subscription_id text,
    p_status text,
    p_current_period_end bigint,
    p_event_created bigint,
    p_event_id text
) returns void
language plpgsql
security definer
set search_path = public
as $$
begin
    insert into public.jai_subscriptions as stored (
        user_id, stripe_customer_id, stripe_subscription_id, status,
        current_period_end, stripe_event_created, stripe_event_id, updated_at
    ) values (
        p_user_id, p_stripe_customer_id, p_stripe_subscription_id, p_status,
        p_current_period_end, p_event_created, p_event_id, now()
    )
    on conflict (user_id) do update
       set stripe_customer_id = excluded.stripe_customer_id,
           stripe_subscription_id = excluded.stripe_subscription_id,
           status = excluded.status,
           current_period_end = excluded.current_period_end,
           stripe_event_created = excluded.stripe_event_created,
           stripe_event_id = excluded.stripe_event_id,
           updated_at = now()
     where (coalesce(excluded.stripe_event_created, 0), coalesce(excluded.stripe_event_id, ''))
         >= (coalesce(stored.stripe_event_created, 0), coalesce(stored.stripe_event_id, ''));
end;
$$;

revoke all on function public.jai_update_subscription(uuid, text, text, text, bigint, bigint, text) from public, anon, authenticated;
grant execute on function public.jai_update_subscription(uuid, text, text, text, bigint, bigint, text) to service_role;
