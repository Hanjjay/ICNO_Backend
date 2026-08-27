# INCO/ICNO 구현 계획서 (검토용 · v2)

작성일: 2026-07-23 (v2: 결정 5개 반영)
대상: 로컬 엔진 안정화 — 보관함 통합 + 프리셋 로컬 저장 + 프리셋 전체 적용
전제: 실제 코드(`backend/main.py`, `engine/icon_overlay.py`, `desktop-aura/src/*`)를 직접 확인한 결과 기준. 확인된 사실과 추론을 구분함.

---

## 0. 이 문서의 사용법

- **검토용 계획서**입니다. 아직 코드를 수정하지 않았습니다.
- 작업은 **백엔드(로컬 Python)** 와 **프론트엔드(Lovable)** 로 나뉩니다.
  - 백엔드 = `icon_project/backend/main.py`, `engine/*` → **Lovable 대상 아님.** 로컬에서 직접 수정.
  - 프론트엔드 = `desktop-aura/*` → **Lovable에 작업 요청** 후 `git pull --ff-only origin main`으로 반영.
- **원칙**: 백엔드 API 스펙을 먼저 확정하고 `openapi.json`을 재생성한 뒤 → Lovable에 프론트 작업 요청. (Lovable이 엔드포인트를 임의로 만들지 않도록)

---

## 1. 확정된 결정 (검토자 답변 반영)

| # | 항목 | 결정 |
|---|---|---|
| 1 | 마켓/팩 아이콘 실제 이미지 소스 | **(a)** 지금은 로컬만. **사용자 직접 업로드 아이콘만** 실제 파일 확보. 마켓/팩(이모지 stand-in)은 클라우드 단계(3순위)에서 처리. |
| 2 | 프리셋 참조 검사 위치 | **(b) 로컬 백엔드**. 프리셋을 `engine/presets.json`에 저장하고, 로컬 FastAPI가 활성 매핑 + 저장 프리셋을 **통합 검사**. (클라우드 아님) |
| 3 | 좌표계 정책 | **(a) 실제 해상도로 스케일 변환**. 변환은 **백엔드 apply 시점**에 수행(백엔드가 실제 작업영역을 알고 있음). |
| 4 | 배경화면 2단계 업로드 | **예.** `wallpaper/upload`로 먼저 올려 경로 확보 → apply에 전달. |
| 5 | Lovable 최신 브랜치 확인 | **예.** 프론트 작업 착수 전 현재 main 상태부터 확인. |

> 2번 확정에 따라, 인수인계 문서의 삭제 참조 검사 "한계"(백엔드가 프리셋을 못 봄)는 **해소**된다. 대신 프리셋 저장을 localStorage → 로컬 API로 옮기는 작업이 추가된다(아래 Phase B2).

---

## 2. 확인된 현재 상태 (사실)

### 2.1 적용이 안 되는 직접 원인
- `library.tsx`의 `requestApply()`(152~199행)는 **`reload-overlay`만** 호출. 실패 시 `start-overlay` 후 재시도가 전부.
- `Upload.tsx`의 `handlePublish()`(309~312행)도 `requestApply(targetId)` 한 줄뿐.
- 즉 **배경화면 업로드 / 아이콘 이미지 업로드 / 매핑 교체 호출이 코드상 전혀 없다.** 오버레이는 기존 `icons_config.json`을 다시 읽을 뿐 → 항상 기존 배치가 뜬다.

### 2.2 근본 문제 — 프론트에 "엔진이 읽을 실제 파일 경로"가 없음
- 엔진 `icon_overlay.py`는 `image_path`를 **절대경로 그대로 사용**(172·218행 `os.path.exists`). 실제 `icons_config.json`도 전부 절대경로.
- 프론트: 마켓/팩 아이콘은 `imageUrl: ""` + 이모지뿐(`iconLibraryService.ts` 72~139행), `synthesizeAssetFromLibrary()`가 이모지로 SVG 즉석 생성(`Upload.tsx` 54~60행), 업로드 아이콘은 blob URL + `image_path=파일명`(740행).
- **결론:** 지금 매핑을 보내도 엔진이 이미지를 못 찾는다. "보관함 아이콘 → 엔진 실제 파일 경로" 파이프라인이 없다. 이것이 모든 작업의 공통 뿌리.

### 2.3 문서(인수인계 13번) 주장과 코드 불일치
- 인수인계가 말한 `PresetIconRef`, `IconAssetSource`, `local_image_path`, `asset_source`, `preview_url` 등이 **현재 코드에 하나도 없음**(검색 0건). 보관함은 여전히 구형 `UserIconAsset` 모델.
- (추론) 미푸시 / 롤백 / 보고 부정확 중 하나 → **Phase 시작 전 Lovable에 최신 상태 확인**(결정 5).

### 2.4 백엔드 현황
- 존재: 매핑 CRUD, `upload`, `images`, `hide/show-desktop`, `settings`, `arrange-grid`, `start/reload-overlay`, `overlay-status`, `pick-file`, `desktop`, `calculate`, `launch-*`.
- **없음:** `presets` 저장, `apply-local`, wallpaper, 보관함 메타(`library`).
- 엔진 오버레이는 **배경화면을 전혀 다루지 않음**(wallpaper/SPI 코드 0건). 배경화면 적용은 신규.

### 2.5 좌표계 (결정 3으로 해결)
- 프론트 편집기는 **논리 1920×1080 캔버스** 픽셀 좌표 저장(`CANVAS_W/H`). 엔진은 실제 데스크톱 픽셀.
- → apply 시 백엔드가 실제 작업영역으로 스케일 변환한다(5장 C 참조).

---

## 3. 목표 아키텍처

```
[보관함 아이콘 = 항상 실제 엔진 파일 경로 보유]        ← Phase A
        │
[보관함 메타 = engine/library.json 기준]              ← Phase B
        │
[프리셋 = engine/presets.json (로컬 백엔드 저장)]      ← Phase B2  (결정 2:b)
   · 아이콘은 asset_id로 참조
        │
POST /api/presets/{id}/apply-local (원자적/롤백)      ← Phase C
   · 좌표는 실제 해상도로 스케일 변환 (결정 3:a)
   · 배경화면은 사전 업로드된 경로 사용 (결정 4)
        │
[icons_config.json 교체 + 배경화면 + 기본아이콘 숨김 + 오버레이 재시작]
```

원칙: 로컬/클라우드 API 분리. 클라우드는 바탕화면을 직접 바꾸지 않음. `display_name`(표시)과 `storage_filename`(실제 파일) 분리. 프리셋은 `asset_id`로 아이콘 참조.

---

## 4. 작업 순서 (권장)

| Phase | 내용 | 담당 | 선행 |
|---|---|---|---|
| **A** | 업로드 파이프라인: 직접 업로드 아이콘이 실제 엔진 파일 경로를 갖도록 | 백엔드(소폭)+프론트(Lovable) | — |
| **B** | 보관함 메타 API (`library.json` list/rename/delete) | 백엔드 | A 저장 규칙 확정 |
| **B2** | 프리셋 로컬 저장 API (`presets.json` CRUD) + 프론트 전환 | 백엔드 + 프론트(Lovable) | A, B |
| **C** | apply-local + wallpaper (원자적/롤백/좌표변환) | 백엔드 | B, B2 |
| **D** | 프론트 apply 교체 + 보관함 UI 단일화 | 프론트(Lovable) | B·B2·C 스펙 확정 |

각 Phase는 독립 테스트 가능하도록 분리. 한 번에 다 바꾸지 않는다(무손상 우선).

---

## 5. 백엔드 API 상세 (스펙 확정용)

> 아래 스펙을 로컬에서 구현·확정하고 `openapi.json`을 재생성한 뒤 Lovable에 프론트를 요청한다.

### 공통 저장소 (신규 파일, 기존과 분리)
- `engine/library.json` — 보관함 아이콘 메타
- `engine/presets.json` — 프리셋(배치·매핑 참조) — **결정 2(b)**
- `engine/wallpapers/` — 업로드된 배경화면 (StaticFiles 마운트)
- `engine/.backup/` — apply 롤백용 백업

기존 `icons_config.json`(활성 매핑)·`settings.json`은 그대로 두고 위 파일들을 **추가**한다.

### A. 업로드 파이프라인 (`upload` 확장)
`POST /api/icons/upload` 응답에 필드 **추가**(기존 `success/filename/url` 유지 → 하위호환):
```json
{
  "success": true,
  "asset_id": "uuid",
  "storage_filename": "7f31c2a8_star.png",
  "local_image_path": "C:\\...\\engine\\custom_icons\\7f31c2a8_star.png",
  "url": "/custom_icons/7f31c2a8_star.png",
  "display_name": "star",
  "duplicate": false
}
```
- 저장 시 sha256 계산 → `library.json`에 동일 해시 있으면 재저장 없이 기존 asset 반환(`duplicate: true`). (인수인계 18)
- `origin`은 `"user-upload"`로 기록.

### B. 보관함 메타 API
`library.json` 항목 스키마:
```json
{
  "asset_id": "uuid",
  "display_name": "노란 별 아이콘",
  "storage_filename": "7f31c2a8_star.png",
  "local_image_path": "C:\\...\\custom_icons\\7f31c2a8_star.png",
  "origin": "user-upload | market-download | icon-pack | local-engine",
  "pack_id": null,
  "sha256": "…",
  "created_at": "ISO",
  "updated_at": "ISO"
}
```
- `GET /api/icons/library` → `{ "assets": [...] }`. (선택) `custom_icons/` 실제 파일과 대조해 고아 항목 플래그.
- `PATCH /api/icons/library/{asset_id}` — body `{ "display_name": "…" }` → **display_name만** 변경. 파일명/경로 불변. (인수인계 16)
- `DELETE /api/icons/library/{asset_id}` — **통합 참조 검사**(결정 2:b):
  - `presets.json`의 모든 프리셋 icons에서 `asset_id` 사용 여부
  - `icons_config.json`(활성 매핑)에서 `local_image_path == image_path` 사용 여부
  - 다른 `library.json` 항목이 동일 `storage_filename` 공유 여부
  - 참조 있으면 `409`:
    ```json
    { "detail": "Icon asset is still in use",
      "references": { "presets": ["preset-uuid"], "active_mappings": ["icon-id"] } }
    ```
  - `?force=true`면 강제 삭제. 참조 없으면 메타 삭제 → 실제 파일 삭제 → 200.

### B2. 프리셋 로컬 저장 API — 결정 2(b)
`presets.json` 항목 스키마(아이콘은 asset_id 참조, 좌표는 논리 1920×1080):
```json
{
  "id": "preset-uuid",
  "name": "밤바다 테마",
  "wallpaper_path": "C:\\...\\engine\\wallpapers\\uuid.jpg",
  "settings": { "mode": "free", "grid_cell_w": 134, "grid_cell_h": 161, "grid_cols": 0 },
  "canvas": { "w": 1920, "h": 1080 },
  "icons": [
    {
      "asset_id": "uuid",
      "icon_name": "Chrome",
      "target_path": "C:\\...\\chrome.lnk",
      "x": 100, "y": 200, "size": 64,
      "show_name": true, "hover_image_path": "",
      "font_family": "맑은 고딕", "font_size": 10, "font_bold": true,
      "font_italic": false, "font_color": "#ffffff", "outline_color": "#000000"
    }
  ],
  "created_at": "ISO", "updated_at": "ISO"
}
```
- `GET /api/presets` → 목록
- `GET /api/presets/{id}` → 단건
- `POST /api/presets` → 생성(신규 id 발급) / `PUT /api/presets/{id}` → 갱신(upsert 허용)
- `DELETE /api/presets/{id}` → 삭제

> `icons[].asset_id`는 `library.json`을 통해 `local_image_path`로 해석된다. 프리셋은 절대경로를 직접 안 갖고 asset_id만 가지므로 파일명 변경·경로 이동에 안전. (인수인계 20의 PresetIconRef 취지)

### C. apply-local + wallpaper — 결정 3·4
- `POST /api/wallpaper/upload` (multipart) → `{ "success": true, "wallpaper_path": "C:\\...\\engine\\wallpapers\\uuid.jpg", "url": "/wallpapers/uuid.jpg" }`
- `POST /api/wallpaper/apply` — body `{ "wallpaper_path": "…" }` → `SystemParametersInfoW(SPI_SETDESKWALLPAPER=20, 0, path, 3)`.
- `POST /api/presets/{id}/apply-local` — **원자적**. 저장된 프리셋을 id로 적용(배경화면 경로는 프리셋에 이미 포함).
  - 처리 순서:
    1. `icons_config.json`, `settings.json`, **현재 배경화면 경로** → `engine/.backup/`에 백업.
    2. 프리셋 로드 → 각 `asset_id`를 `library.json`으로 `local_image_path` 해석. **파일 존재 검증**(없으면 실패). `target_path`는 없어도 경고만.
    3. **좌표 스케일 변환(결정 3:a):** `get_work_area()`로 실제 작업영역 `(W,H)` 획득. `sx=W/canvas.w`, `sy=H/canvas.h`. 각 아이콘 `x'=round(x*sx)`, `y'=round(y*sy)`, `size'=round(size*min(sx,sy))`(비율 유지).
    4. 변환된 매핑으로 `icons_config.json` **일괄 교체**.
    5. `settings.json` 저장.
    6. 배경화면 적용.
    7. Windows 기본 아이콘 숨김.
    8. 오버레이 재시작(`reload-overlay` 로직 재사용).
    9. **어느 단계든 실패 시 전체 롤백**(백업 복원 + 이전 배경화면 복원).

> 좌표 변환을 백엔드에서 하므로 프론트는 논리 1920×1080 좌표만 저장/전송하면 된다(프론트 부담 최소).

### 담당
- A-1, B, B2, C 전부 백엔드 로컬 직접 수정. 각 단계 후 `openapi.json` 재생성 필수.

---

## 6. Lovable 작업 요청문 (복붙용 · 스펙 확정 후 사용)

> **백엔드 API 확정 + `openapi.json` 갱신·첨부 후**에만 보낼 것.

### 6.0 (먼저) 현재 상태 확인 — 결정 5
```
현재 main 브랜치의 아이콘 보관함 관련 코드 상태를 알려줘.
src/types/preset.ts, src/services/iconLibraryService.ts, src/components/presets/IconEditModal.tsx 에
PresetIconRef, IconAssetSource, local_image_path, asset_source, preview_url 식별자가 실제로 존재하는지,
있다면 어느 커밋인지 확인해줘. 내 로컬 pull 결과엔 없어서 반영 여부를 확인하려는 거야.
```

### 6.1 Phase A — 업로드 파이프라인
```
목표: 사용자가 아이콘을 "직접 업로드"할 때 로컬 엔진 FastAPI에 실제 파일을 저장하고
그 절대경로(local_image_path)를 보관함 메타데이터에 보관하도록 연동해줘.

규칙:
- 엔드포인트/응답 형식은 첨부한 openapi.json 기준으로만 사용. 임의 생성 금지.
- POST /api/icons/upload 응답에 asset_id, local_image_path, storage_filename, duplicate가 추가됐어.
  업로드 성공 시 이 값들을 보관함 항목에 저장. local_image_path는 이후 적용에서 엔진이 읽을
  실제 경로이므로 반드시 보관.
- 이미 local_image_path가 있는 아이콘은 재업로드하지 마(중복 방지).
- 실패 시 mock 성공 처리 금지, 오류 표시.
- 참고: 마켓/팩 다운로드 아이콘은 이번 범위 아님(이모지 stand-in 유지). 직접 업로드만 실제 파일 처리.
```

### 6.2 Phase B2 — 프리셋을 로컬 백엔드에 저장
```
목표: 프리셋 저장을 localStorage 대신 로컬 FastAPI(engine/presets.json)로 전환해줘.

규칙:
- 엔드포인트/형식은 첨부한 openapi.json 기준. 임의 생성 금지.
- 프리셋 저장/수정: POST /api/presets (신규) 또는 PUT /api/presets/{id} (수정).
  목록: GET /api/presets, 단건: GET /api/presets/{id}, 삭제: DELETE /api/presets/{id}.
- 프리셋 icons[]는 절대경로가 아니라 asset_id로 아이콘을 참조해야 함(local_image_path 직접 저장 금지).
- 좌표(x/y)는 1920x1080 논리 캔버스 값 그대로 저장. 해상도 변환은 백엔드가 적용 시 처리하므로
  프론트는 변환하지 말 것.
- 기존 localStorage 프리셋이 있으면 최초 진입 시 백엔드로 1회 마이그레이션(있으면).
```

### 6.3 Phase D — 프리셋 전체 적용 교체
```
목표: "적용하기"가 reload-overlay만 부르던 것을 백엔드 원자적 적용으로 교체해줘.

규칙:
- 엔드포인트/형식은 첨부한 openapi.json 기준. 임의 생성 금지.
- 적용 흐름:
  1) 배경화면 파일이 있으면 POST /api/wallpaper/upload 로 올려 wallpaper_path 확보.
  2) 프리셋을 저장(POST/PUT /api/presets)해 preset id 확보(배경 경로 포함).
  3) POST /api/presets/{id}/apply-local 호출.
- 성공 토스트는 실제 2xx 이후에만.
- 기존 requestApply의 reload/start-overlay 직접 호출은 apply-local 성공 흐름으로 대체.
- 좌표 변환은 백엔드가 하므로 프론트에서 스케일 변환하지 말 것.
```

### 6.4 Phase D — 보관함 UI 단일화
```
목표: "내 보관함"에서 출처별 탭(사용자 업로드/내 보관함/아이콘 팩) 구분을 없애고
모든 아이콘을 하나의 목록에서 동일하게 선택·사용하게 해줘.

규칙:
- 출처(origin)는 UI 탭이 아니라 내부 메타데이터로만 유지.
- 아이콘 팩 아이콘도 각각 독립 asset_id로 개별 선택 가능.
- 목록은 GET /api/icons/library 를 기준 데이터로(localStorage는 캐시/임시 편집).
- 이름 수정은 PATCH /api/icons/library/{asset_id} (display_name만).
- 삭제는 DELETE /api/icons/library/{asset_id}. 409(참조 있음)면 사용 중 프리셋/매핑을 알리고
  [취소 / 보관함에서만 숨기기 / 강제 삭제] 선택지 제공.
- 메타는 있는데 실제 파일이 없으면 placeholder + "로컬 파일을 찾을 수 없습니다" 표시.
  배치정보(asset_id, x/y/size)는 사용자가 바꾸기 전까지 유지.
```

---

## 7. 테스트 / 검증 체크리스트

- **A:** 업로드 후 `engine/custom_icons/`에 실제 파일 + `library.json` 항목 생성. 같은 파일 재업로드 시 `duplicate: true`.
- **B:** `GET /api/icons/library`가 실제 파일과 일치. `PATCH`가 display_name만 바꾸고 파일명 불변.
- **B2:** 프론트에서 프리셋 저장 → `engine/presets.json`에 기록. icons가 asset_id로 저장됨(절대경로 아님). 재진입 시 asset_id로 동일 아이콘 복원.
- **B+B2 참조검사:** 프리셋에 쓰인 아이콘을 DELETE → `409` + `references.presets`에 해당 프리셋 id. `?force=true`로 삭제 성공.
- **C (실제 Windows 필요):**
  - `apply-local` → `icons_config.json`이 프리셋으로 **교체**됨.
  - 배경화면 실제 변경. 기본 아이콘 숨김 + 오버레이만 표시(중복 없음).
  - **다른 해상도(예: 2560×1440)에서 배치가 화면 비율대로 맞는지**(좌표 스케일 검증).
  - 잘못된 asset(파일 없음) 넣어 실패 유발 → **롤백되어 이전 상태 복원**.
- **D:** Network 탭에서 upload→presets→apply-local 순서 확인. 성공 토스트 2xx 이후.

> C는 Windows API·오버레이·실제 바탕화면을 다루므로 **실제 PC 수동 검증 필수**. 리눅스 샌드박스에선 로직 리뷰까지만 가능.

---

## 8. 위험 요소 및 무손상 원칙

- apply-local은 **백업 후 교체, 실패 시 롤백**. 부분 적용 금지(인수인계 10 B안 보류 이유와 동일).
- 기존 엔드포인트 시그니처 유지, 필드는 추가만(하위호환). `upload` 응답 확장이 대표 예.
- `library.json`·`presets.json`·`wallpapers/`는 기존 파일과 **분리된 신규** → 기존 오버레이 동작 무영향.
- 좌표 변환을 백엔드로 일원화 → 프론트/백엔드 이중 변환으로 인한 어긋남 방지.
- Phase 경계마다 `openapi.json` 재생성. 빠뜨리면 프론트가 옛 스펙으로 붙는다.
- B2에서 localStorage→백엔드 전환 시 **마이그레이션 1회** 처리(기존 저장 프리셋 유실 방지).

---

## 9. 다음 액션 (요약)

1. Lovable에 6.0(현재 상태 확인) 먼저 발송.
2. 백엔드 Phase A → B → B2 → C 순으로 로컬 구현, 각 단계 후 `openapi.json` 재생성.
3. `openapi.json` 첨부해 Lovable에 6.1 → 6.2 → 6.3 → 6.4 순으로 요청.
4. `git pull --ff-only origin main`으로 반영, 7장 체크리스트로 검증(C는 실제 PC).
5. 안정화 후 3순위(클라우드) 착수 — 이때 마켓/팩 아이콘 실제 파일화(결정 1의 보류분) 포함.
