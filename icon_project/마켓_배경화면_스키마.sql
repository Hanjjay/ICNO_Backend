-- ============================================================================
-- ICNO 마켓 배경화면(단일) 스키마 (Phase 10)
-- 보관함의 배경화면을 마켓에 올리는 기능용. 이미지는 기존
-- market-preset-images 버킷을 재사용한다(새 버킷 불필요, uid 폴더 정책 그대로).
-- 소셜(찜/좋아요/별점/댓글/다운로드/신고)은 기존 item_* 폴리모픽 테이블을
-- 재사용하며, target_type 에 'wallpaper' 를 추가한다.
-- 실행: Supabase SQL Editor (qdqarbrszfgvjhmsmnab). (auto-expose 꺼져 있어 grant 필수)
-- ※ 아이콘 스키마(마켓_아이콘_스키마.sql)와 아이템 소셜 스키마
--   (마켓_아이템_소셜_스키마.sql)를 먼저 적용한 뒤 실행하세요.
-- ============================================================================

-- ── 1) market_wallpapers 테이블 (market_icons 미러 + 소셜 집계 컬럼 포함) ──────
create table if not exists public.market_wallpapers (
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
  comment_count  int default 0,
  rating_sum     int default 0,
  rating_count   int default 0,
  is_public      boolean default true,
  is_hidden      boolean default false,          -- 검수 숨김
  created_at     timestamptz default now(),
  updated_at     timestamptz default now()
);

alter table public.market_wallpapers enable row level security;

-- 공개+숨김아님은 누구나, 본인 것은 항상
create policy market_wallpapers_select on public.market_wallpapers
  for select using ((is_public = true and is_hidden = false) or auth.uid() = owner_id);
create policy market_wallpapers_insert on public.market_wallpapers
  for insert with check (auth.uid() = owner_id);
create policy market_wallpapers_update on public.market_wallpapers
  for update using (auth.uid() = owner_id);
create policy market_wallpapers_delete on public.market_wallpapers
  for delete using (auth.uid() = owner_id);

-- Data API 노출
grant select on public.market_wallpapers to anon, authenticated;
grant insert, update, delete on public.market_wallpapers to authenticated;

create index if not exists market_wallpapers_owner_idx   on public.market_wallpapers(owner_id);
create index if not exists market_wallpapers_created_idx on public.market_wallpapers(created_at desc);
create index if not exists market_wallpapers_tags_idx    on public.market_wallpapers using gin(tags);

-- ── 2) item_* 소셜 폴리모픽에 'wallpaper' 타입 허용 ───────────────────────────
-- 각 테이블의 target_type 관련 CHECK 제약을 (이름과 무관하게) 모두 드롭한 뒤,
-- 'wallpaper' 를 포함하는 제약으로 재생성한다. 인라인 check 의 기본 이름은
-- {table}_{col}_check 이지만, 이름이 달라도 안전하도록 동적으로 처리한다.
do $$
declare
  t   text;
  con record;
begin
  foreach t in array array['item_likes','item_wishlists','item_downloads',
                           'item_ratings','item_comments','item_reports']
  loop
    -- 해당 테이블에서 정의(pg_get_constraintdef)에 target_type 이 들어간 CHECK 제약 드롭
    for con in
      select c.conname
      from pg_constraint c
      join pg_class     r on r.oid = c.conrelid
      join pg_namespace n on n.oid = r.relnamespace
      where n.nspname = 'public' and r.relname = t and c.contype = 'c'
        and pg_get_constraintdef(c.oid) ilike '%target_type%'
    loop
      execute format('alter table public.%I drop constraint %I', t, con.conname);
    end loop;
    -- 'wallpaper' 포함 CHECK 재생성
    execute format(
      'alter table public.%I add constraint %I check (target_type in (''icon'',''pack'',''wallpaper''))',
      t, t || '_target_type_check');
  end loop;
end $$;

-- ── 3) 카운터 증감 함수에 'wallpaper' 분기 추가 ──────────────────────────────
-- (기존 icon/pack 분기 유지 + wallpaper → market_wallpapers 갱신)
create or replace function public._bump_item_counter(p_type text, p_id uuid, p_col text, p_delta int)
returns void language plpgsql security definer set search_path = public as $$
begin
  if p_type = 'icon' then
    execute format('update market_icons set %I = greatest(%I + $1, 0) where id = $2', p_col, p_col)
      using p_delta, p_id;
  elsif p_type = 'pack' then
    execute format('update market_icon_packs set %I = greatest(%I + $1, 0) where id = $2', p_col, p_col)
      using p_delta, p_id;
  elsif p_type = 'wallpaper' then
    execute format('update market_wallpapers set %I = greatest(%I + $1, 0) where id = $2', p_col, p_col)
      using p_delta, p_id;
  end if;
end $$;

-- increment_item_view 는 _bump_item_counter 를 그대로 쓰므로 별도 수정 불필요.
-- (p_type='wallpaper' 로 호출하면 자동으로 market_wallpapers.views 증가)
