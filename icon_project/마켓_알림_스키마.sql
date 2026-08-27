-- ============================================================================
-- ICNO 알림(notifications) 스키마 (Phase 7)
-- 내가 올린 프리셋에 다른 사람이 댓글/좋아요/다운로드/별점을 하거나,
-- 나를 팔로우하면 -> 나에게 알림 row 가 자동 생성된다.
-- 실행: Supabase SQL Editor. (마켓_소셜_스키마.sql 을 먼저 실행한 상태여야 함)
-- 원칙:
--  - 알림 insert 는 오직 트리거(SECURITY DEFINER)로만. 클라이언트 직접 insert 금지(위조 방지).
--  - 자기 자신 행동은 알림 생성 안 함(actor == recipient 제외).
--  - 신고(reports)는 알림에 넣지 않음 -> 아래 '참고' 설명.
-- ============================================================================

-- ── 알림 테이블 ─────────────────────────────────────────────────────────────
create table if not exists public.notifications (
  id           uuid primary key default gen_random_uuid(),
  recipient_id uuid not null references public.profiles(id) on delete cascade,   -- 받는 사람(내 프리셋 소유자 / 팔로우 당한 사람)
  actor_id     uuid references public.profiles(id) on delete set null,           -- 행동한 사람
  type         text not null check (type in ('comment','like','download','rating','follow')),
  preset_id    uuid references public.market_presets(id) on delete cascade,
  comment_id   uuid references public.comments(id) on delete cascade,
  is_read      boolean default false,
  created_at   timestamptz default now()
);
alter table public.notifications enable row level security;

-- 조회/읽음처리/삭제는 "받는 본인"만. INSERT 정책은 두지 않음 → 클라이언트가 직접 못 만듦.
create policy notifications_select on public.notifications for select using (auth.uid() = recipient_id);
create policy notifications_update on public.notifications for update using (auth.uid() = recipient_id);
create policy notifications_delete on public.notifications for delete using (auth.uid() = recipient_id);

-- INSERT 권한은 authenticated 에 주지 않는다(트리거가 소유자 권한으로 삽입).
grant select, update, delete on public.notifications to authenticated;

create index if not exists notifications_recipient_idx
  on public.notifications(recipient_id, is_read, created_at desc);


-- ============================================================================
-- 트리거: 각 행동 발생 시 프리셋 소유자(또는 팔로우 대상)에게 알림 생성
--   SECURITY DEFINER → 함수 소유자(테이블 owner) 권한으로 실행되어 RLS 우회 삽입.
-- ============================================================================

-- 댓글 → 프리셋 소유자에게
create or replace function public.notify_on_comment() returns trigger
language plpgsql security definer set search_path = public as $$
declare v_owner uuid;
begin
  select owner_id into v_owner from market_presets where id = new.preset_id;
  if v_owner is not null and v_owner <> new.user_id then
    insert into notifications(recipient_id, actor_id, type, preset_id, comment_id)
    values (v_owner, new.user_id, 'comment', new.preset_id, new.id);
  end if;
  return null;
end $$;
drop trigger if exists notify_comment on public.comments;
create trigger notify_comment after insert on public.comments
  for each row execute function public.notify_on_comment();

-- 좋아요/찜(하트) → 프리셋 소유자에게
create or replace function public.notify_on_like() returns trigger
language plpgsql security definer set search_path = public as $$
declare v_owner uuid;
begin
  select owner_id into v_owner from market_presets where id = new.preset_id;
  if v_owner is not null and v_owner <> new.user_id then
    insert into notifications(recipient_id, actor_id, type, preset_id)
    values (v_owner, new.user_id, 'like', new.preset_id);
  end if;
  return null;
end $$;
-- 프론트에서 하트=찜을 wishlists 로 통일했으므로 wishlists 에 건다.
-- (좋아요를 likes 테이블로 다시 쓰면 아래 대상 테이블을 likes 로 바꾸면 됨)
drop trigger if exists notify_like on public.wishlists;
create trigger notify_like after insert on public.wishlists
  for each row execute function public.notify_on_like();

-- 다운로드 → 프리셋 소유자에게
create or replace function public.notify_on_download() returns trigger
language plpgsql security definer set search_path = public as $$
declare v_owner uuid;
begin
  select owner_id into v_owner from market_presets where id = new.preset_id;
  if v_owner is not null and v_owner <> new.user_id then
    insert into notifications(recipient_id, actor_id, type, preset_id)
    values (v_owner, new.user_id, 'download', new.preset_id);
  end if;
  return null;
end $$;
drop trigger if exists notify_download on public.downloads;
create trigger notify_download after insert on public.downloads
  for each row execute function public.notify_on_download();

-- 별점 → 프리셋 소유자에게 (신규 별점 시)
create or replace function public.notify_on_rating() returns trigger
language plpgsql security definer set search_path = public as $$
declare v_owner uuid;
begin
  select owner_id into v_owner from market_presets where id = new.preset_id;
  if v_owner is not null and v_owner <> new.user_id then
    insert into notifications(recipient_id, actor_id, type, preset_id)
    values (v_owner, new.user_id, 'rating', new.preset_id);
  end if;
  return null;
end $$;
drop trigger if exists notify_rating on public.ratings;
create trigger notify_rating after insert on public.ratings
  for each row execute function public.notify_on_rating();

-- 팔로우 → 팔로우 당한 사람에게
create or replace function public.notify_on_follow() returns trigger
language plpgsql security definer set search_path = public as $$
begin
  insert into notifications(recipient_id, actor_id, type)
  values (new.following_id, new.follower_id, 'follow');
  return null;
end $$;
drop trigger if exists notify_follow on public.follows;
create trigger notify_follow after insert on public.follows
  for each row execute function public.notify_on_follow();

-- ============================================================================
-- 참고 — 신고(reports)는 알림에 넣지 않았다.
--   신고는 "콘텐츠 소유자"가 아니라 "검수자(관리자)"가 받아야 하는 것이라,
--   업로더에게 신고 알림을 보내면 보복/악용 소지가 있다.
--   신고는 reports 테이블(검수 큐)에 쌓이고, 관리자가 대시보드/service_role 로 처리한다.
--   (원한다면 별도 관리자 알림 채널을 나중에 추가)
-- ============================================================================
