-- ============================================================================
-- ICNO 마켓 아이템(아이콘/팩) 소셜 스키마 (Phase 9)
-- 프리셋 소셜과 동일한 찜/좋아요/별점/댓글/다운로드/신고를, 아이콘과 팩에
-- 폴리모픽(target_type: 'icon' | 'pack')으로 제공한다. (프리셋 소셜은 별도 유지)
-- 실행: Supabase SQL Editor (qdqarbrszfgvjhmsmnab).
-- ============================================================================

-- ── 0) 집계 컬럼 보강 ───────────────────────────────────────────────────────
alter table public.market_icons
  add column if not exists comment_count int default 0,
  add column if not exists rating_sum    int default 0,
  add column if not exists rating_count  int default 0;
alter table public.market_icon_packs
  add column if not exists comment_count int default 0,
  add column if not exists rating_sum    int default 0,
  add column if not exists rating_count  int default 0;

-- ── 공통: 대상 테이블의 카운터 컬럼을 delta 만큼 증감 (SECURITY DEFINER) ──────
create or replace function public._bump_item_counter(p_type text, p_id uuid, p_col text, p_delta int)
returns void language plpgsql security definer set search_path = public as $$
begin
  if p_type = 'icon' then
    execute format('update market_icons set %I = greatest(%I + $1, 0) where id = $2', p_col, p_col)
      using p_delta, p_id;
  elsif p_type = 'pack' then
    execute format('update market_icon_packs set %I = greatest(%I + $1, 0) where id = $2', p_col, p_col)
      using p_delta, p_id;
  end if;
end $$;

-- ── 1) 좋아요 ───────────────────────────────────────────────────────────────
create table if not exists public.item_likes (
  user_id     uuid not null references public.profiles(id) on delete cascade,
  target_type text not null check (target_type in ('icon','pack')),
  target_id   uuid not null,
  created_at  timestamptz default now(),
  primary key (user_id, target_type, target_id)
);
alter table public.item_likes enable row level security;
create policy item_likes_select on public.item_likes for select using (true);
create policy item_likes_insert on public.item_likes for insert with check (auth.uid() = user_id);
create policy item_likes_delete on public.item_likes for delete using (auth.uid() = user_id);
grant select on public.item_likes to anon, authenticated;
grant insert, delete on public.item_likes to authenticated;

-- ── 2) 찜(개인용, 조회는 본인만) ────────────────────────────────────────────
create table if not exists public.item_wishlists (
  user_id     uuid not null references public.profiles(id) on delete cascade,
  target_type text not null check (target_type in ('icon','pack')),
  target_id   uuid not null,
  created_at  timestamptz default now(),
  primary key (user_id, target_type, target_id)
);
alter table public.item_wishlists enable row level security;
create policy item_wishlists_select on public.item_wishlists for select using (auth.uid() = user_id);
create policy item_wishlists_insert on public.item_wishlists for insert with check (auth.uid() = user_id);
create policy item_wishlists_delete on public.item_wishlists for delete using (auth.uid() = user_id);
grant select, insert, delete on public.item_wishlists to authenticated;

-- ── 3) 다운로드 기록 ────────────────────────────────────────────────────────
create table if not exists public.item_downloads (
  id          uuid primary key default gen_random_uuid(),
  user_id     uuid references public.profiles(id) on delete set null,
  target_type text not null check (target_type in ('icon','pack')),
  target_id   uuid not null,
  created_at  timestamptz default now()
);
alter table public.item_downloads enable row level security;
create policy item_downloads_select on public.item_downloads for select using (auth.uid() = user_id);
create policy item_downloads_insert on public.item_downloads for insert with check (auth.uid() = user_id);
grant select, insert on public.item_downloads to authenticated;

-- ── 4) 별점 (사용자당 1개) ──────────────────────────────────────────────────
create table if not exists public.item_ratings (
  user_id     uuid not null references public.profiles(id) on delete cascade,
  target_type text not null check (target_type in ('icon','pack')),
  target_id   uuid not null,
  score       int  not null check (score between 1 and 5),
  created_at  timestamptz default now(),
  updated_at  timestamptz default now(),
  primary key (user_id, target_type, target_id)
);
alter table public.item_ratings enable row level security;
create policy item_ratings_select on public.item_ratings for select using (true);
create policy item_ratings_insert on public.item_ratings for insert with check (auth.uid() = user_id);
create policy item_ratings_update on public.item_ratings for update using (auth.uid() = user_id);
create policy item_ratings_delete on public.item_ratings for delete using (auth.uid() = user_id);
grant select on public.item_ratings to anon, authenticated;
grant insert, update, delete on public.item_ratings to authenticated;

-- ── 5) 댓글 ─────────────────────────────────────────────────────────────────
create table if not exists public.item_comments (
  id          uuid primary key default gen_random_uuid(),
  target_type text not null check (target_type in ('icon','pack')),
  target_id   uuid not null,
  user_id     uuid not null references public.profiles(id) on delete cascade,
  body        text not null check (char_length(body) between 1 and 1000),
  created_at  timestamptz default now(),
  updated_at  timestamptz default now()
);
alter table public.item_comments enable row level security;
create policy item_comments_select on public.item_comments for select using (true);
create policy item_comments_insert on public.item_comments for insert with check (auth.uid() = user_id);
create policy item_comments_update on public.item_comments for update using (auth.uid() = user_id);
create policy item_comments_delete on public.item_comments for delete using (auth.uid() = user_id);
grant select on public.item_comments to anon, authenticated;
grant insert, update, delete on public.item_comments to authenticated;
create index if not exists item_comments_target_idx on public.item_comments(target_type, target_id, created_at desc);

-- ── 6) 신고 ─────────────────────────────────────────────────────────────────
create table if not exists public.item_reports (
  id          uuid primary key default gen_random_uuid(),
  reporter_id uuid references public.profiles(id) on delete set null,
  target_type text not null check (target_type in ('icon','pack')),
  target_id   uuid not null,
  reason      text not null check (reason in ('spam','inappropriate','copyright','malware','other')),
  detail      text default '' check (char_length(detail) <= 1000),
  status      text default 'open' check (status in ('open','reviewing','resolved','dismissed')),
  created_at  timestamptz default now()
);
alter table public.item_reports enable row level security;
create policy item_reports_select_own on public.item_reports for select using (auth.uid() = reporter_id);
create policy item_reports_insert on public.item_reports for insert with check (auth.uid() = reporter_id);
grant select, insert on public.item_reports to authenticated;

-- ── 7) 카운터 트리거 (SECURITY DEFINER) ─────────────────────────────────────
create or replace function public.trg_item_likes() returns trigger
language plpgsql security definer set search_path = public as $$
begin
  if tg_op = 'INSERT' then perform _bump_item_counter(new.target_type, new.target_id, 'likes', 1);
  elsif tg_op = 'DELETE' then perform _bump_item_counter(old.target_type, old.target_id, 'likes', -1); end if;
  return null;
end $$;
drop trigger if exists item_likes_count on public.item_likes;
create trigger item_likes_count after insert or delete on public.item_likes
  for each row execute function public.trg_item_likes();

create or replace function public.trg_item_wishlists() returns trigger
language plpgsql security definer set search_path = public as $$
begin
  if tg_op = 'INSERT' then perform _bump_item_counter(new.target_type, new.target_id, 'wishlist_count', 1);
  elsif tg_op = 'DELETE' then perform _bump_item_counter(old.target_type, old.target_id, 'wishlist_count', -1); end if;
  return null;
end $$;
drop trigger if exists item_wishlists_count on public.item_wishlists;
create trigger item_wishlists_count after insert or delete on public.item_wishlists
  for each row execute function public.trg_item_wishlists();

create or replace function public.trg_item_downloads() returns trigger
language plpgsql security definer set search_path = public as $$
begin
  perform _bump_item_counter(new.target_type, new.target_id, 'downloads', 1);
  return null;
end $$;
drop trigger if exists item_downloads_count on public.item_downloads;
create trigger item_downloads_count after insert on public.item_downloads
  for each row execute function public.trg_item_downloads();

create or replace function public.trg_item_comments() returns trigger
language plpgsql security definer set search_path = public as $$
begin
  if tg_op = 'INSERT' then perform _bump_item_counter(new.target_type, new.target_id, 'comment_count', 1);
  elsif tg_op = 'DELETE' then perform _bump_item_counter(old.target_type, old.target_id, 'comment_count', -1); end if;
  return null;
end $$;
drop trigger if exists item_comments_count on public.item_comments;
create trigger item_comments_count after insert or delete on public.item_comments
  for each row execute function public.trg_item_comments();

create or replace function public.trg_item_ratings() returns trigger
language plpgsql security definer set search_path = public as $$
begin
  if tg_op = 'INSERT' then
    perform _bump_item_counter(new.target_type, new.target_id, 'rating_sum', new.score);
    perform _bump_item_counter(new.target_type, new.target_id, 'rating_count', 1);
  elsif tg_op = 'DELETE' then
    perform _bump_item_counter(old.target_type, old.target_id, 'rating_sum', -old.score);
    perform _bump_item_counter(old.target_type, old.target_id, 'rating_count', -1);
  elsif tg_op = 'UPDATE' then
    perform _bump_item_counter(new.target_type, new.target_id, 'rating_sum', new.score - old.score);
  end if;
  return null;
end $$;
drop trigger if exists item_ratings_agg on public.item_ratings;
create trigger item_ratings_agg after insert or update or delete on public.item_ratings
  for each row execute function public.trg_item_ratings();

-- ── 8) 조회수 증가 RPC ──────────────────────────────────────────────────────
create or replace function public.increment_item_view(p_type text, p_id uuid) returns void
language plpgsql security definer set search_path = public as $$
begin
  perform _bump_item_counter(p_type, p_id, 'views', 1);
end $$;
grant execute on function public.increment_item_view(text, uuid) to anon, authenticated;
