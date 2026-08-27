# Lovable 프롬프트 — 아이콘 '대상 지정'에 파일과 폴더 둘 다

> 아래 블록을 Lovable에 붙여넣으세요. 백엔드 준비됨: `GET /api/icons/pick-file`(파일/프로그램), `GET /api/icons/pick-folder`(폴더). 둘 다 `{ file_path, name }` 반환.

---

프리셋 에디터의 아이콘 "대상 지정"이 지금 **폴더만** 열립니다. **파일/프로그램 선택도 함께** 되도록 고쳐줘. 기존 기능(파일) 유지 + 폴더 추가가 목표입니다.

1. `src/services/localEngineApi.ts` 에 두 함수가 모두 있어야 함:
   ```ts
   export function pickTargetFile(): Promise<any> { return request("/api/icons/pick-file"); }
   export function pickTargetFolder(): Promise<any> { return request("/api/icons/pick-folder"); }
   ```

2. "대상 지정" 버튼을 **드롭다운 메뉴 2개 항목**으로:
   - **📂 실행 파일/프로그램** → `pickTargetFile()` 호출
   - **📁 폴더** → `pickTargetFolder()` 호출
   각 항목이 **자기 엔드포인트를 확실히 호출**해야 함(지금은 폴더만 호출되는 상태로 보임 — 파일 항목이 pick-file을 부르는지 확인/수정).

3. 두 경우 모두 응답의 `file_path`를 선택 아이콘의 `target_path`로 설정.
   - 아이콘 이름이 기본값(예: "아이콘 N" / `*_source` 같은 자동 이름)일 때만 응답 `name`으로 자동 채움(사용자가 지정한 이름은 덮어쓰지 말 것).

4. 결과가 빈 문자열(`file_path === ""`)이면 사용자가 취소한 것이므로 아무 변화 없이 무시.

5. `target_path`(파일·폴더 경로)는 로컬 실행 경로라 **마켓 공유 시 제외** 규칙 그대로 유지.

6. UI 문구 예: 버튼 라벨 "대상 지정 ▾", 드롭다운에 "📂 실행 파일", "📁 폴더".
