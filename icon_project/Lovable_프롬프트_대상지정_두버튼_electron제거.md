# Lovable 프롬프트 — 대상 지정: 두 버튼 + Electron 분기 제거(파일 선택 복구)

> Lovable에 붙여넣으세요. 백엔드 준비됨: `GET /api/icons/pick-file`(파일/프로그램), `GET /api/icons/pick-folder`(폴더). 둘 다 `{ file_path, name }` 반환.

---

`src/pages/Upload.tsx` 의 아이콘 "연결 대상" 지정 UI를 아래처럼 고쳐줘.

## 1) Electron 분기 제거 — 파일 선택이 편집 화면에서 안 열리는 버그 수정
현재 `pickTargetForSelected(kind)` 안에 `window.electronAPI` 를 우선 사용하는 분기가 있는데,
파일일 때 잡히는 `selectIconFile ?? selectFile` 이 **폴더 전용으로 동작하는 빌드**라 파일 선택이 깨진다.
이 앱은 로컬 FastAPI 엔진(127.0.0.1:8000)으로 파일/폴더를 선택하므로, **Electron 분기 전체를 제거**하고
항상 백엔드 엔드포인트를 쓰게 해줘:

```ts
const pickTargetForSelected = async (kind: "file" | "folder") => {
  if (!selected) return;
  const isDefaultName = (n?: string) =>
    !n || /^아이콘\s*\d+$/.test(n.trim()) || /_source$/i.test(n.trim());
  try {
    const res = kind === "folder" ? await pickTargetFolder() : await pickTargetFile();
    const path = res?.file_path ?? "";
    if (!path) return; // 취소 → 변화 없음
    const patch: any = { target_path: path };
    if (res?.name && isDefaultName(selected.name)) patch.name = res.name;
    update(selected.id, patch);
  } catch (err) {
    toast({
      title: kind === "folder" ? "폴더 선택에 실패했습니다." : "파일 선택에 실패했습니다.",
      description: "ICNO 로컬 엔진(python main.py)이 실행 중인지 확인해주세요.",
      variant: "destructive",
    });
  }
};
```
(즉 `window.electronAPI` / `electronPicker` 관련 코드는 이 함수에서 삭제.)

## 2) 드롭다운 → 버튼 2개 나란히
"대상 지정 ▾" 드롭다운을 없애고, **버튼 2개를 나란히** 배치:

```
[ 📂 실행 파일 ]   [ 📁 폴더 ]
```
- "📂 실행 파일" onClick → `pickTargetForSelected("file")`
- "📁 폴더" onClick → `pickTargetForSelected("folder")`
- 이미 `target_path` 가 있으면 그 아래에 현재 대상(파일/폴더명)과 "해제" 버튼을 지금처럼 유지.
- 두 버튼은 `flex gap-1.5` 로 한 줄, 각 `flex-1` 로 반반 너비. 크기/스타일은 기존 버튼과 동일하게.

## 3) 규칙 유지
- 취소 시 변화 없음, 아이콘 이름이 기본값일 때만 선택 항목 이름으로 자동 채움.
- `target_path`(파일·폴더 경로)는 마켓 공유 시 제외되는 기존 규칙 그대로.
