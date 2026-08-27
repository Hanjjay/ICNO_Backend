-- ============================================================================
-- [핫픽스] 다른 사람이 마켓 업로드가 안 되는 문제 해결
-- 원인: 새 유저에게 public.profiles 행이 자동 생성되지 않으면,
--       market_presets/market_icons/market_wallpapers 의 owner_id → profiles
--       외래키를 만족하지 못해 업로드가 실패한다.
-- 조치: (1) 회원가입 시 profiles 자동 생성 트리거를 보장하고,
--       (2) 이미 가입했지만 profiles 가 없는 기존 유저를 백필한다.
-- 실행: 진짜 프로젝트(qdqarbrszfgvjhmsmnab) SQL Editor. 여러 번 실행해도 안전(멱등).
-- ============================================================================

-- (1) 회원가입 → profiles 자동 생성 함수/트리거 보장 -------------------------
create or replace function public.handle_new_user()
returns trigger
language plpgsql
security definer
set search_path = public
as $$
begin
  insert into public.profiles (id, display_name, avatar_url)
  values (
    new.id,
    coalesce(new.raw_user_meta_data ->> 'display_name', split_part(new.email, '@', 1)),
    new.raw_user_meta_data ->> 'avatar_url'
  )
  on conflict (id) do nothing;
  return new;
end;
$$;

drop trigger if exists on_auth_user_created on auth.users;
create trigger on_auth_user_created
  after insert on auth.users
  for each row execute function public.handle_new_user();

-- (2) 기존 유저 백필: profiles 가 없는 auth.users 를 모두 채운다 --------------
insert into public.profiles (id, display_name, avatar_url)
select u.id,
       coalesce(u.raw_user_meta_data ->> 'display_name', split_part(u.email, '@', 1)),
       u.raw_user_meta_data ->> 'avatar_url'
from auth.users u
left join public.profiles p on p.id = u.id
where p.id is null
on conflict (id) do nothing;

-- (확인용) 아직도 profiles 없는 유저가 있나? (0 이어야 정상)
-- select count(*) from auth.users u
--   left join public.profiles p on p.id = u.id where p.id is null;
