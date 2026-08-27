-- ============================================================================
-- ICNO 마켓 소셜 스키마 (Phase 6)
-- 대상: 좋아요 · 찜 · 댓글 · 공유 · 다운로드수 · 팔로우 · 조회수 · 신고/검수 · 별점
-- 실행: Supabase SQL Editor 에 통째로 붙여넣고 Run.
-- 전제: market_presets, profiles 테이블은 이미 존재. (auto-expose 꺼져 있어 grant 필수)
-- 원칙: 모든 테이블 RLS 필수. 카운터는 SECURITY DEFINER 트리거로 유지
--       (비소유자가 좋아요/다운로드해도, market_presets UPDATE 권한 없이 카운트 증가 가능).
-- ============================================================================

-- ── 0) 집계 컬럼 추가 ────────────────────────────────────────────────────────
-- market_presets 에는 이미 likes, downloads(int) 컬럼이 있어 카운터로 재사용한다.
alter table public.market_presets
  add column if not exists views          int     default 0,
  add column if not exists wishlist_count int     default 0,
  add column if not exists comment_count  int     default 0,
  add column if not exists rating_sum     int     default 0,   -- 평균 = rating_sum / rating_count
  add column if not exists rating_count   int     default 0,
  add column if not exists is_hidden      boolean default false; -- 검수 숨김

alter table public.profiles
  add column if not exists follower_count  int default 0,
  add column if not exists following_count int default 0;

-- 검수 숨김 반영: 공개글 중 숨김 아닌 것만 노출(+본인은 항상)
drop policy if exists market_presets_select on public.market_presets;
create policy market_presets_select on public.market_presets
  for select using ((is_public = true and is_hidden = false) or auth.uid() = owner_id);


-- ── 1) 좋아요 (likes) ───────────────────────────────────────────────────────
create table if not exists public.likes (
  user_id    uuid not null references public.profiles(id) on delete cascade,
  preset_id  uuid not null references public.market_presets(id) on delete cascade,
  created_at timestamptz default now(),
  primary key (user_id, preset_id)
);
alter table public.likes enable row level security;
create policy likes_select on public.likes for select using (true);            -- 좋아요는 공개(누가 눌렀는지 확인 가능)
create policy likes_insert on public.likes for insert with check (auth.uid() = user_id);
create policy likes_delete on public.likes for delete using (auth.uid() = user_id);
grant select on public.likes to anon, authenticated;
grant insert, delete on public.likes to authenticated;
create index if not exists likes_preset_idx on public.likes(preset_id);


-- ── 2) 찜 (wishlists) — 개인용이라 조회는 본인만 ─────────────────────────────
create table if not exists public.wishlists (
  user_id    uuid not null references public.profiles(id) on delete cascade,
  preset_id  uuid not null references public.market_presets(id) on delete cascade,
  created_at timestamptz default now(),
  primary key (user_id, preset_id)
);
alter table public.wishlists enable row level security;
create policy wishlists_select on public.wishlists for select using (auth.uid() = user_id);
create policy wishlists_insert on public.wishlists for insert with check (auth.uid() = user_id);
create policy wishlists_delete on public.wishlists for delete using (auth.uid() = user_id);
grant select, insert, delete on public.wishlists to authenticated;
create index if not exists wishlists_preset_idx on public.wishlists(preset_id);


-- ── 3) 다운로드 기록 (downloads) — 개수 집계용, 조회는 본인만 ─────────────────
create table if not exists public.downloads (
  id         uuid primary key default gen_random_uuid(),
  user_id    uuid references public.profiles(id) on delete set null,
  preset_id  uuid not null references public.market_presets(id) on delete cascade,
  created_at timestamptz default now()
);
alter table public.downloads enable row level security;
create policy downloads_select on public.downloads for select using (auth.uid() = user_id);
create policy downloads_insert on public.downloads for insert with check (auth.uid() = user_id);
grant select, insert on public.downloads to authenticated;
create index if not exists downloads_preset_idx on public.downloads(preset_id);


-- ── 4) 별점 (ratings) — 사용자당 프리셋 1개 ─────────────────────────────────
create table if not exists public.ratings (
  user_id    uuid not null references public.profiles(id) on delete cascade,
  preset_id  uuid not null references public.market_presets(id) on delete cascade,
  score      int  not null check (score between 1 and 5),
  created_at timestamptz default now(),
  updated_at timestamptz default now(),
  primary key (user_id, preset_id)
);
alter table public.ratings enable row level security;
create policy ratings_select on public.ratings for select using (true);
create policy ratings_insert on public.ratings for insert with check (auth.uid() = user_id);
create policy ratings_update on public.ratings for update using (auth.uid() = user_id);
create policy ratings_delete on public.ratings for delete using (auth.uid() = user_id);
grant select on public.ratings to anon, authenticated;
grant insert, update, delete on public.ratings to authenticated;
create index if not exists ratings_preset_idx on public.ratings(preset_id);


-- ── 5) 댓글 (comments) ──────────────────────────────────────────────────────
create table if not exists public.comments (
  id         uuid primary key default gen_random_uuid(),
  preset_id  uuid not null references public.market_presets(id) on delete cascade,
  user_id    uuid not null references public.profiles(id) on delete cascade,
  body       text not null check (char_length(body) between 1 and 1000),
  created_at timestamptz default now(),
  updated_at timestamptz default now()
);
alter table public.comments enable row level security;
create policy comments_select on public.comments for select using (true);
create policy comments_insert on public.comments for insert with check (auth.uid() = user_id);
create policy comments_update on public.comments for update using (auth.uid() = user_id);
create policy comments_delete on public.comments for delete using (auth.uid() = user_id);
grant select on public.comments to anon, authenticated;
grant insert, update, delete on public.comments to authenticated;
create index if not exists comments_preset_idx on public.comments(preset_id, created_at desc);


-- ── 6) 팔로우 (follows) ─────────────────────────────────────────────────────
create table if not exists public.follows (
  follower_id  uuid not null references public.profiles(id) on delete cascade,
  following_id uuid not null references public.profiles(id) on delete cascade,
  created_at   timestamptz default now(),
  primary key (follower_id, following_id),
  check (follower_id <> following_id)           -- 자기 자신 팔로우 금지
);
alter table public.follows enable row level security;
create policy follows_select on public.follows for select using (true);
create policy follows_insert on public.follows for insert with check (auth.uid() = follower_id);
create policy follows_delete on public.follows for delete using (auth.uid() = follower_id);
grant select on public.follows to anon, authenticated;
grant insert, delete on public.follows to authenticated;
create index if not exists follows_following_idx on public.follows(following_id);


-- ── 7) 신고 (reports) — 검수 큐. 조회는 신고자 본인만(관리자는 대시보드/service_role) ─
create table if not exists public.reports (
  id          uuid primary key default gen_random_uuid(),
  reporter_id uuid references public.profiles(id) on delete set null,
  preset_id   uuid not null references public.market_presets(id) on delete cascade,
  reason      text not null check (reason in ('spam','inappropriate','copyright','malware','other')),
  detail      text default '' check (char_length(detail) <= 1000),
  status      text default 'open' check (status in ('open','reviewing','resolved','dismissed')),
  created_at  timestamptz default now()
);
alter table public.reports enable row level security;
create policy reports_select_own on public.reports for select using (auth.uid() = reporter_id);
create policy reports_insert on public.reports for insert with check (auth.uid() = reporter_id);
grant select, insert on public.reports to authenticated;
create index if not exists reports_status_idx on public.reports(status, created_at desc);


-- ============================================================================
-- 8) 카운터 유지 트리거 (SECURITY DEFINER — 비소유자 액션도 카운트 반영)
-- ============================================================================

-- 좋아요 수 → market_presets.likes
create or replace function public.trg_likes_count() returns trigger
language plpgsql security definer set search_path = public as $$
begin
  if tg_op = 'INSERT' then
    update market_presets set likes = likes + 1 where id = new.preset_id;
  elsif tg_op = 'DELETE' then
    update market_presets set likes = greatest(likes - 1, 0) where id = old.preset_id;
  end if;
  return null;
end $$;
drop trigger if exists likes_count on public.likes;
create trigger likes_count after insert or delete on public.likes
  for each row execute function public.trg_likes_count();

-- 찜 수 → wishlist_count
create or replace function public.trg_wishlist_count() returns trigger
language plpgsql security definer set search_path = public as $$
begin
  if tg_op = 'INSERT' then
    update market_presets set wishlist_count = wishlist_count + 1 where id = new.preset_id;
  elsif tg_op = 'DELETE' then
    update market_presets set wishlist_count = greatest(wishlist_count - 1, 0) where id = old.preset_id;
  end if;
  return null;
end $$;
drop trigger if exists wishlist_count on public.wishlists;
create trigger wishlist_count after insert or delete on public.wishlists
  for each row execute function public.trg_wishlist_count();

-- 다운로드 수 → downloads
create or replace function public.trg_downloads_count() returns trigger
language plpgsql security definer set search_path = public as $$
begin
  update market_presets set downloads = downloads + 1 where id = new.preset_id;
  return null;
end $$;
drop trigger if exists downloads_count on public.downloads;
create trigger downloads_count after insert on public.downloads
  for each row execute function public.trg_downloads_count();

-- 댓글 수 → comment_count
create or replace function public.trg_comment_count() returns trigger
language plpgsql security definer set search_path = public as $$
begin
  if tg_op = 'INSERT' then
    update market_presets set comment_count = comment_count + 1 where id = new.preset_id;
  elsif tg_op = 'DELETE' then
    update market_presets set comment_count = greatest(comment_count - 1, 0) where id = old.preset_id;
  end if;
  return null;
end $$;
drop trigger if exists comment_count on public.comments;
create trigger comment_count after insert or delete on public.comments
  for each row execute function public.trg_comment_count();

-- 별점 합/개수 → rating_sum, rating_count (평균은 프론트에서 sum/count)
create or replace function public.trg_ratings_agg() returns trigger
language plpgsql security definer set search_path = public as $$
begin
  if tg_op = 'INSERT' then
    update market_presets set rating_sum = rating_sum + new.score, rating_count = rating_count + 1 where id = new.preset_id;
  elsif tg_op = 'DELETE' then
    update market_presets set rating_sum = greatest(rating_sum - old.score, 0), rating_count = greatest(rating_count - 1, 0) where id = old.preset_id;
  elsif tg_op = 'UPDATE' then
    update market_presets set rating_sum = greatest(rating_sum - old.score + new.score, 0) where id = new.preset_id;
  end if;
  return null;
end $$;
drop trigger if exists ratings_agg on public.ratings;
create trigger ratings_agg after insert or update or delete on public.ratings
  for each row execute function public.trg_ratings_agg();

-- 팔로워/팔로잉 수 → profiles
create or replace function public.trg_follows_count() returns trigger
language plpgsql security definer set search_path = public as $$
begin
  if tg_op = 'INSERT' then
    update profiles set follower_count  = follower_count  + 1 where id = new.following_id;
    update profiles set following_count = following_count + 1 where id = new.follower_id;
  elsif tg_op = 'DELETE' then
    update profiles set follower_count  = greatest(follower_count  - 1, 0) where id = old.following_id;
    update profiles set following_count = greatest(following_count - 1, 0) where id = old.follower_id;
  end if;
  return null;
end $$;
drop trigger if exists follows_count on public.follows;
create trigger follows_count after insert or delete on public.follows
  for each row execute function public.trg_follows_count();


-- ── 9) 조회수 증가 RPC (anon 도 호출, RLS 우회 위해 SECURITY DEFINER) ─────────
create or replace function public.increment_view(p_preset_id uuid) returns void
language plpgsql security definer set search_path = public as $$
begin
  update market_presets set views = views + 1
   where id = p_preset_id and is_public = true and is_hidden = false;
end $$;
grant execute on function public.increment_view(uuid) to anon, authenticated;

-- ============================================================================
-- 끝. (검수/숨김·신고 처리는 관리자가 대시보드/service_role 로 수행:
--     update market_presets set is_hidden = true where id = ...;
--     update reports set status = 'resolved' where id = ...; )
-- ============================================================================
