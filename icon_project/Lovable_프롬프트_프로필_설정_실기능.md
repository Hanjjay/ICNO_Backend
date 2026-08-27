# Lovable 프롬프트 — 프로필/설정 mock → 실제 기능

> 아래 블록 전체를 복사해서 Lovable에 붙여넣으세요. 대부분 프론트 배선이며, 필요한 백엔드는 이미 준비됨.
> - **팔로우**: Supabase `follows` 테이블 + `profiles.follower_count/following_count` + 카운터 트리거가 **이미 존재**(마켓_소셜_스키마.sql). 새 테이블 만들지 말 것.
> - **오버레이 설정**: 로컬 엔진 `GET/POST /api/settings`에 `overlay_autostart`, `restore_on_exit` 키가 **이미 추가됨**.

---

프로필(`src/pages/Profile.tsx`)과 설정(`src/pages/Settings.tsx`)의 mock을 실제 기능으로 바꿔줘.

## 1) 프로필 — 통계 실집계 (현재 전부 0 하드코딩)
로그인 유저(`auth.uid()`) 기준으로 실제 수치를 집계해서 표시:
- **찜**: 프리셋 찜(`wishlists` where user_id=me) + 아이템 찜(`item_wishlists` where user_id=me) 합계. `/profile/wishlist`.
- **다운로드**: `downloads`(where user_id=me) + `item_downloads`(where user_id=me) 합계. `/profile/downloads`.
- **내 상품**: 내가 올린 마켓 물품 합계 = `market_presets` + `market_icons` + `market_icon_packs` + `market_wallpapers` (각 `owner_id=me` count). `/profile/sales`.
- **팔로잉**: `profiles.following_count`(내 행) 또는 `follows` where follower_id=me count. `/profile/following`.
- **구매**: **항목 자체를 숨겨줘**(결제 시스템 없음). 프로필 통계/바로가기/하위 라우트에서 "구매 내역/구매" 제거.

## 2) 프로필 — 팔로우 기능 실제 구현 (백엔드 이미 있음)
- **팔로우/해제**: 대상 프로필에 대해
  - 팔로우: `(supabase).from("follows").insert({ follower_id: me, following_id: target })`
  - 해제: `.from("follows").delete().eq("follower_id", me).eq("following_id", target)`
  - 카운트(follower_count/following_count)는 트리거가 자동 갱신하므로 클라에서 손대지 말 것.
- **팔로우 여부**: `follows` where follower_id=me and following_id=target 존재 확인 → 버튼 상태(팔로우/팔로잉) 토글.
- **팔로우 목록 페이지**(`/profile/following`): `follows`(follower_id=me)를 `profiles`(following_id 조인)로 가져와 크리에이터 카드로 렌더. "준비 중" 문구 제거. 각 카드에서 팔로우 해제 가능.
- **크리에이터 프로필**(`CreatorProfile.tsx`)과 상세 모달의 팔로우 버튼도 위 로직으로 실제 동작 + `follower_count` 실제 표시. (`followedCreators` 등 mockData 사용 제거)

## 3) 프로필 — 하위 페이지 실데이터
- **찜 목록**(`/profile/wishlist`): 프리셋(기존 `useWishlistedPresets`) + 아이템(아이콘/팩/배경) 찜을 함께 표시. (아이템은 `item_wishlists` 조인)
- **다운로드**(`/profile/downloads`): 프리셋 + 아이템 다운로드 내역.
- **내 상품**(`/profile/sales`): 내가 올린 마켓 프리셋/아이콘/팩/배경 목록 + 각 항목 관리(숨김 `is_hidden` 토글 / 삭제). `owner_id=me` 로 조회.
- 모든 하위 페이지는 mockData(`marketplacePresets, purchasedIds, followedCreators, marketItems` 등) 대신 실제 쿼리로.

## 4) 설정 — 핵심 환경설정 실제 동작
`localStorage` 기반 앱 환경설정 훅(예: `useAppPreferences`)을 만들어 아래를 실제 저장/반영:
- **화면**: 테마(기존 useTheme 유지) · **사이드바 표시**(펼치기/아이콘만/hover → 실제 사이드바에 반영) · **시작 페이지**(홈/탐색/보관함 → 앱 진입 시 해당 라우트로).
- **보관함**: **기본 정렬**(최근순/이름순 → 보관함 목록 기본값) · **즐겨찾기 우선 표시**(핀 우선 정렬 on/off).
- **알림**: 토글들(전체/댓글/평점/다운로드/판매/신고/오류)을 localStorage로 저장(값 유지). (실제 푸시는 없음 — 설정값 저장·복원만.)
- **Windows 적용(오버레이)**: 로컬 엔진 `GET /api/settings`로 초기값 로드, 토글 변경 시 `POST /api/settings`:
  - "앱 시작 시 오버레이 자동 시작" → `overlay_autostart` (앱 로드시 true면 `POST /api/icons/start-overlay` 호출)
  - "앱 종료 시 기본 데스크톱 아이콘 복원" → `restore_on_exit`
  - ※ `/api/settings`는 보낸 필드만 부분 업데이트되니, 이 토글은 `{ overlay_autostart }` / `{ restore_on_exit }` 처럼 해당 키만 POST.
- **계정**: "프로필 편집"→프로필 편집 열기, "다운로드/찜/내 상품"→각 프로필 하위 페이지로 이동. **"구매 내역", "차단된 사용자", "계정 삭제"는 이번 범위 밖이니 숨겨줘.**
- **앱 정보**: 버전 정적 표시 유지, "업데이트 확인"→토스트("최신 버전입니다"), 약관/개인정보/라이선스/피드백은 링크 또는 숨김(과하게 만들지 말 것).

## 5) 규칙
- 새 Supabase 테이블/RPC 만들지 말 것(팔로우·소셜은 기존 것 재사용). 타입 미생성 테이블은 `(supabase as any)` 캐스팅.
- 집계 쿼리는 `count` 옵션(`select("*", { count: "exact", head: true })`)으로 가볍게.
- `.env`는 건드리지 말 것.
- mockData 의존(`purchasedIds, followedCreators, downloadedIds, marketItems` 등)은 실제 쿼리로 대체하고, 결제/구매 관련 코드·UI는 제거.
