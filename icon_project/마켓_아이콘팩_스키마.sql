-- ============================================================================
-- ICNO 마켓 아이콘 팩 스키마 (Phase 8b)
-- 여러 아이콘을 하나로 묶어 올리는 '아이콘 팩' 상품용.
--  - 아이콘 1개  → market_icons (단일)  ← 이미 있음
--  - 아이콘 2개+ → market_icon_packs (팩) ← 이 파일
-- 이미지는 기존 market-preset-images 버킷 재사용({uid}/icons/{uuid}.{ext}).
-- 실행: Supabase SQL Editor.
-- ============================================================================

create table if not exists public.market_icon_packs (
  id             uuid primary key default gen_random_uuid(),
  owner_id       uuid not null references public.profiles(id) on delete cascade,
  name           text not null,
  description    text default '',
  tags           text[] default '{}',
  icons          jsonb default '[]'::jsonb,       -- [{ image_path, name, sha256 }]
  icon_count     int default 0,
  downloads      int default 0,
  likes          int default 0,
  views          int default 0,
  wishlist_count int default 0,
  is_public      boolean default true,
  is_hidden      boolean default false,
  created_at     timestamptz default now(),
  updated_at     timestamptz default now()
);

alter table public.market_icon_packs enable row level security;

create policy market_icon_packs_select on public.market_icon_packs
  for select using ((is_public = true and is_hidden = false) or auth.uid() = owner_id);
create policy market_icon_packs_insert on public.market_icon_packs
  for insert with check (auth.uid() = owner_id);
create policy market_icon_packs_update on public.market_icon_packs
  for update using (auth.uid() = owner_id);
create policy market_icon_packs_delete on public.market_icon_packs
  for delete using (auth.uid() = owner_id);

grant select on public.market_icon_packs to anon, authenticated;
grant insert, update, delete on public.market_icon_packs to authenticated;

create index if not exists market_icon_packs_owner_idx   on public.market_icon_packs(owner_id);
create index if not exists market_icon_packs_created_idx on public.market_icon_packs(created_at desc);
create index if not exists market_icon_packs_tags_idx    on public.market_icon_packs using gin(tags);
