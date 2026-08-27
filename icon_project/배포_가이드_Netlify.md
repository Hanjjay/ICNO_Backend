# ICNO 실제 앱 배포 가이드 (Netlify) — 공모전 프로토타입 URL

빌드는 이미 검증 완료(npm install/ build 성공, `_redirects` 포함, 엔진 없이도 정상). 아래 순서대로만 하면 됩니다.

## 0) 사전 확인
- `desktop-aura\.env` 가 **진짜 프로젝트**인지 확인(빌드에 이 값이 그대로 박힘):
  ```
  VITE_SUPABASE_PROJECT_ID="qdqarbrszfgvjhmsmnab"
  ```
  Lovable이 되돌려놨다면 빌드 전에 다시 고치세요. (`.env.local`로 고정해두면 편함)
- `desktop-aura\public\_redirects` 파일이 있어야 함(이미 생성해 둠). 커밋해두면 유지됩니다:
  ```powershell
  cd C:\Users\서승린\Desktop\desktop-aura
  git add public/_redirects; git commit -m "netlify SPA redirects"; git push
  ```

## 1) 빌드
```powershell
cd C:\Users\서승린\Desktop\desktop-aura
npm install        # 이미 했다면 생략 가능
npm run build      # → dist\ 폴더 생성 (약 10초)
```

## 2) Netlify에 배포 (무료, 로그인 없이 가능)
1. https://app.netlify.com/drop 접속
2. 방금 만들어진 **`dist` 폴더**를 창에 통째로 드래그&드롭
3. 잠시 후 나오는 URL(예: `https://ICNO-xxxx.netlify.app`) 복사 → 이게 제출용 프로토타입 URL

> 폴더 대신 zip을 올려도 됩니다: dist 폴더 안 내용을 zip으로 묶어 Drop에 올려도 배포됩니다.
> (dist 폴더 자체가 아니라 **그 안의 파일들**이 루트가 되게 하세요.)

## 3) Supabase Auth 설정 (심사위원이 회원가입/로그인 가능하게)
Supabase 대시보드(qdqarbrszfgvjhmsmnab) → **Authentication → URL Configuration**:
- **Site URL**: 위에서 받은 Netlify 주소
- **Redirect URLs**: 같은 주소 추가

그리고 **Authentication → Providers → Email** 에서 **"Confirm email" 끄기(OFF)** 를 권장합니다.
→ 심사위원이 가입 즉시 로그인 가능(이메일 인증 대기 없음).
- 인증을 켜둔 채로 두려면, 대신 **데모 계정**(예: demo@icno.app / 비번)을 하나 만들어 제출 게시글 본문에 적어 주세요.

## 4) 동작 확인 (배포 후)
- URL 접속 → 홈/탐색(마켓)/보관함 화면이 뜨는지
- 탐색에서 프리셋·아이콘·배경 카드가 실제로 보이는지(= Supabase 연결 OK)
- 회원가입 → 찜/별점/댓글/팔로우가 저장되는지
- ※ "바탕화면에 적용" 등 로컬 엔진 기능은 브라우저에선 동작 안 함(정상) → **실행 영상**으로 시연

## 참고
- 배포된 사이트는 HTTPS라 `http://127.0.0.1:8000`(로컬 엔진) 호출은 브라우저가 차단하지만, 앱이 이를 조용히 무시하도록 되어 있어 마켓/소셜 화면은 정상 동작합니다.
- 앱을 수정하면 다시 `npm run build` 후 새 `dist`를 같은 방식으로 올리면 됩니다(또는 Netlify를 GitHub 리포에 연결해 자동 배포).
