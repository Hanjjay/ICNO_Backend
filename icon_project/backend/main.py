# backend/main.py
import subprocess
import os
import sys
from pathlib import Path
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

app = FastAPI()

# 리액트(Vite 포트 5173)와의 통신을 위한 CORS 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- [기능 1: 계산기 로직] ---
class CalcRequest(BaseModel):
    expression: str

@app.post("/api/calculate")
async def calculate(request: CalcRequest):
    try:
        # 보안 주의: 실제 서비스에서는 eval 대신 안전한 파서를 권장합니다.
        result = eval(request.expression)
        return {"result": str(result)}
    except Exception:
        raise HTTPException(status_code=400, detail="잘못된 수식입니다.")

# --- [기능 2: 데스크톱 런처 실행 로직] ---
@app.post("/api/launch-launcher")
async def launch_launcher():
    try:
        # 프로젝트 루트 경로 찾기 (backend의 부모 디렉토리)
        backend_dir = Path(__file__).parent
        project_root = backend_dir.parent
        
        # 런처 파일 경로: icon_project/engine/icno_changer_luncher.py
        script_path = project_root / "engine" / "icno_changer_luncher.py"
        
        if not script_path.exists():
            raise HTTPException(
                status_code=404, 
                detail=f"런처 파일을 찾을 수 없습니다: {script_path}"
            )

        # 새로운 프로세스로 파이썬 스크립트 실행 (비차단 방식)
        # cwd를 engine 폴더로 설정하여 상대 경로가 올바르게 작동하도록 함
        subprocess.Popen(
            [sys.executable, str(script_path)],
            cwd=str(script_path.parent),  # engine/ 폴더를 작업 디렉토리로 설정
            creationflags=subprocess.CREATE_NEW_CONSOLE if sys.platform == "win32" else 0
        )
        return {"status": "success", "message": "런처가 성공적으로 실행되었습니다."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)