-- ============================================================================
-- ICNO 마켓 아이콘(개별) 스키마 (Phase 8)
-- 보관함의 개별 아이콘을 마켓에 올리는 기능용. 이미지는 기존
-- market-preset-images 버킷을 재사용한다(새 버킷 불필요, uid 폴더 정책 그대로).
-- 실행: Supabase SQL Editor. (auto-expose 꺼져 있어 grant 필수)
-- ============================================================================

create table if not exists public.market_icons (
  id             uuid primary key default gen_random_uuid(),
  owner_id       uuid not null references public.profiles(id) on delete cascade,
  name           text not null,
  description    text default '',
  tags           text[] default '{}',
  image_path     text not null,                 -- Storage 경로 (market-preset-images 버킷)
  sha256         text,
  width          int,
  height         int,
  format         text,                          -- 'png' | 'gif' | 'jpg'
  downloads      int default 0,
  likes          int default 0,
  views          int default 0,
  wishlist_count int default 0,
  is_public      boolean default true,
  is_hidden      boolean default false,          -- 검수 숨김
  created_at     timestamptz default now(),
  updated_at     timestamptz default now()
);

alter table public.market_icons enable row level security;

-- 공개+숨김아님은 누구나, 본인 것은 항상
create policy market_icons_select on public.market_icons
  for select using ((is_public = true and is_hidden = false) or auth.uid() = owner_id);
create policy market_icons_insert on public.market_icons
  for insert with check (auth.uid() = owner_id);
create policy market_icons_update on public.market_icons
  for update using (auth.uid() = owner_id);
create policy market_icons_delete on public.market_icons
  for delete using (auth.uid() = owner_id);

-- Data API 노출
grant select on public.market_icons to anon, authenticated;
grant insert, update, delete on public.market_icons to authenticated;

create index if not exists market_icons_owner_idx   on public.market_icons(owner_id);
create index if not exists market_icons_created_idx on public.market_icons(created_at desc);
create index if not exists market_icons_tags_idx    on public.market_icons using gin(tags);

-- 참고: 이미지 저장은 기존 market-preset-images 버킷 재사용.
--   경로 규칙: {auth.uid()}/icons/{uuid}.{ext}  (기존 insert 정책이 첫 폴더=uid 검사)
--   버킷의 허용 MIME(png/jpeg/gif)·용량(15MB) 제한도 그대로 적용됨.
