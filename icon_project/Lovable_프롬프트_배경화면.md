# Lovable 프롬프트 — 배경화면 마켓 + 보관함 (아이콘과 동일 구조)

> 아래 블록 전체를 복사해서 Lovable에 붙여넣으세요.
> 백엔드(로컬 엔진 + Supabase 스키마)는 이미 준비 완료 상태이며, 프론트만 구현하면 됩니다.

---

배경화면(wallpaper)을 **기존 아이콘 마켓/보관함과 완전히 동일한 구조**로 추가해줘.
아이콘은 단일/팩 둘 다 있지만 **배경화면은 "단일 한 장"만** 지원한다(팩 없음).
이미 구현된 아이콘 코드를 그대로 미러링하는 게 목표야. 아래 파일들을 참고 기준으로 삼아줘:

- `src/lib/market-icons.ts` → 배경용 `src/lib/market-wallpapers.ts` 신규
- `src/lib/item-social.ts` → **그대로 재사용**, `ItemType`에 `'wallpaper'` 추가
- `src/lib/icon-meta.ts`(마켓 제작자 origin 저장) → 배경용 origin 저장 추가
- `src/services/marketIconUpload.ts` → `src/services/marketWallpaperUpload.ts` 신규
- `src/services/marketIconDownload.ts` → `src/services/marketWallpaperDownload.ts` 신규
- `src/components/presets/MarketIconCards.tsx` → `MarketWallpaperCard`
- `src/components/presets/MarketIconModal.tsx` → `MarketWallpaperModal`
- `src/components/presets/MarketIconUploadModal.tsx` → 배경 업로드 모달(단일 전용, 팩 UI 제거)

## 1) 백엔드 계약 (이미 구현됨 — 이대로 호출)

**로컬 엔진 (`localEngineApi.ts`)**
- 업로드: `POST /api/wallpaper/upload` (multipart, 기존 `uploadWallpaper` 그대로 사용)
  이제 응답에 `asset_id`, `storage_filename`, `display_name`, `url`, `duplicate`가 추가됨(기존 `wallpaper_path`도 유지).
- 목록: `GET /api/wallpapers/library` → `{ assets: [{ asset_id, display_name, storage_filename, local_image_path, origin, width, height, file_exists, created_at }] }`
  (이미지 표시는 `localEngineUrl('/wallpapers/' + storage_filename)`)
- 이름변경: `PATCH /api/wallpapers/library/{asset_id}` body `{ display_name }`
- 삭제: `DELETE /api/wallpapers/library/{asset_id}?force=true` (프리셋이 참조 중이면 force 없이는 409)
- `localEngineApi.ts`에 `listWallpaperLibrary()`, `renameWallpaperAsset(id, name)`, `deleteWallpaperAsset(id, force)` 메서드를 아이콘 라이브러리 메서드와 동일한 형태로 추가.

**Supabase (테이블 `market_wallpapers`, 이미 생성됨)**
- 컬럼은 `market_icons`와 동일 + 소셜 집계(`comment_count, rating_sum, rating_count`) 포함.
  `id, owner_id, name, description, tags[], image_path, sha256, width, height, format, downloads, likes, views, wishlist_count, comment_count, rating_sum, rating_count, is_public, is_hidden, created_at, updated_at`
- 이미지 버킷은 **기존 `market-preset-images` 재사용**, 경로 규칙 `{auth.uid()}/wallpapers/{uuid}.{ext}`.
- 타입 생성기가 이 테이블을 아직 모를 수 있으니, 아이콘처럼 `(supabase as any).from("market_wallpapers")` 캐스팅 패턴을 사용해.

**소셜(찜·좋아요·별점·댓글·다운로드·신고)**
- 프리셋/아이콘과 **동일한 폴리모픽 `item_*` 테이블 재사용**. `target_type = 'wallpaper'`로 호출.
- 조회수: `(supabase as any).rpc("increment_item_view", { p_type: "wallpaper", p_id })`.
- `src/lib/item-social.ts`의 `ItemType`을 `'icon' | 'pack' | 'wallpaper'`로 확장(로직은 그대로 동작).

## 2) 구현할 프론트 기능 (아이콘과 1:1 대응)

**(a) 마켓 업로드**
- 보관함 배경화면 카드의 `⋯` 드롭다운에 **"마켓에 올리기"** 추가(아이콘/프리셋과 동일 위치).
- 업로드 모달: 이미지 미리보기(단일), 이름/설명/태그/공개여부 입력 → `market-preset-images`에 업로드 후 `market_wallpapers` insert. `marketWallpaperUpload.ts`의 `publishWallpaper(...)`로 구현. `sanitizeText`는 아이콘과 동일하게 `/\p{C}/gu` 사용.

**(b) 탐색(Explore) — 마켓 배경화면 섹션**
- `Explore.tsx`에 `useMarketWallpapers()` 훅으로 "마켓 배경화면" 섹션 추가(아이콘 섹션 바로 아래/옆).
- 카드는 **썸네일 꽉 채우기**(배경은 `object-cover`, 16:9 비율 타일 권장). 카드 클릭 → 상세 모달 오픈(다운로드 버튼은 카드에 두지 말 것).
- 검색/필터는 기존 Explore 필터에 자연스럽게 편입.

**(c) 상세 모달 (`MarketWallpaperModal`)**
- 아이콘 모달과 동일 구성: 큰 미리보기 + `CreatorCard`(아바타/이름/팔로워) + 다운로드 + 찜/별점/댓글/공유/신고.
- 소셜은 `useItemSocial('wallpaper', id)` / `useItemComments('wallpaper', id)`로.
- 다운로드: `marketWallpaperDownload.ts`의 `downloadMarketWallpaper(name, imageUrl, ownerId?)` →
  이미지를 받아 `POST /api/wallpaper/upload`로 로컬 보관함에 저장하고, origin(제작자 ownerId, marketType:'wallpaper')을 저장. 그 후 `registerDownload`(item_downloads insert)로 카운트.

**(d) 보관함 — 배경화면 탭/섹션**
- 보관함에 **배경화면** 탭(또는 섹션) 신설. `GET /api/wallpapers/library`로 목록 표시.
- 각 카드: 썸네일(`object-cover`), 이름, `⋯` 드롭다운(이름 변경 / 마켓에 올리기 / 삭제).
- **삭제**는 `DELETE /api/wallpapers/library/{asset_id}` 호출(실제 파일 삭제 — 새로고침해도 안 돌아옴). 프리셋 참조로 409가 오면 "이 배경을 쓰는 프리셋이 있어요. 그래도 삭제할까요?" 확인 후 `?force=true`로 재요청.
- **이름 변경**은 `PATCH`로. UI는 아이콘 이름 변경 다이얼로그와 동일하게.
- 마켓에서 다운받은 배경이면 아이콘처럼 제작자 `CreatorCard`를 상세에 함께 표시(origin 기반).

**(e) 프리셋 에디터 "배경화면 불러오기"에 보관함 연동 (핵심 요구사항)**
- `Upload.tsx`의 배경화면 불러오기 부분(현재 `handleWallpaper`가 파일 업로드로 처리, `LibraryWallpaper` 타입이 이미 있음)에 **"보관함에서 선택"** 옵션 추가.
- 보관함 배경 목록(`GET /api/wallpapers/library`)을 그리드로 보여주고, 하나 선택하면 **재업로드 없이** 그 배경의 로컬 경로/URL을 그대로 사용:
  `setWallpaper({ file: stub, url: localEngineUrl('/wallpapers/'+storage_filename) })`, `setWallpaperPath(local_image_path)`.
- 즉 "직접 올리기"와 "보관함에서 선택" 두 경로 모두 지원. 새로 올린 배경은 자동으로 보관함에도 남음(백엔드가 기록).

## 3) 주의
- 아이콘에서 쓰던 `(supabase as any)` 캐스팅 패턴 유지(타입 생성기가 새 테이블을 모를 수 있음).
- `.env`는 건드리지 말 것(Supabase 프로젝트 설정 유지).
- 공유(마켓) 데이터에는 로컬 절대경로(`local_image_path`)를 넣지 말 것 — Storage 경로만.
- 기존 아이콘/프리셋 동작을 깨지 않도록, 위 파일들을 **복제 후 배경용으로 수정**하는 방식으로.
