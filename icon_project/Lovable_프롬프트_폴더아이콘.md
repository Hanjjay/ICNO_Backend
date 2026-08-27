# Lovable 프롬프트 — 아이콘 대상으로 '폴더' 지정 (에디터)

> 아래 블록을 Lovable에 붙여넣으세요. 백엔드는 이미 준비됨: `GET /api/icons/pick-folder`
> (네이티브 폴더 선택 → `{ file_path, name }` 반환, `pick-file`과 동일한 형태).

---

프리셋 에디터에서 아이콘의 대상(target)을 지정할 때, **파일뿐 아니라 폴더도 지정**할 수 있게 해줘.

1. `src/services/localEngineApi.ts` 에 폴더 선택 함수 추가 (기존 `pickTargetFile`과 동일한 형태):
   ```ts
   export function pickTargetFolder(): Promise<any> {
     return request("/api/icons/pick-folder");
   }
   ```
   반환값은 `{ file_path, name }` 로 `pickTargetFile`과 동일하니, 기존에 `target_path`/이름을 처리하던 로직을 그대로 재사용하면 됨.

2. 에디터(`Upload.tsx` 등)에서 현재 `pickTargetFile()`로 "실행 파일 선택" 버튼이 있는 곳 옆에,
   **"폴더 선택"** 버튼(또는 드롭다운 옵션)을 추가해 `pickTargetFolder()`를 호출하고,
   결과의 `file_path`를 해당 아이콘의 `target_path`로 설정. (이름 미지정 시 `name`을 아이콘 이름 기본값으로 사용해도 됨)

3. UI 문구: 버튼 두 개 → "📂 실행 파일" / "📁 폴더", 또는 하나의 "대상 지정" 버튼에 드롭다운으로 파일/폴더 선택.

4. 주의: `target_path`는 로컬 실행 경로라 **마켓 공유 시에는 제외**되는 기존 규칙 그대로 유지(폴더 경로도 동일하게 공유 대상에서 제외).
