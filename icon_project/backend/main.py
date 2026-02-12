# backend/main.py
import subprocess
import os
import sys
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
        # 런처 파일 경로 설정 (main.py와 같은 위치에 있다고 가정)
        script_path = os.path.join(os.path.dirname(__file__), "desktop_launcher.py")
        
        if not os.path.exists(script_path):
            raise HTTPException(status_code=404, detail="런처 파일을 찾을 수 없습니다.")

        # 새로운 프로세스로 파이썬 스크립트 실행 (비차단 방식)
        # creationflags=subprocess.CREATE_NEW_CONSOLE 는 윈도우에서 새로운 창으로 실행하게 함
        subprocess.Popen(
            [sys.executable, script_path], 
            creationflags=subprocess.CREATE_NEW_CONSOLE
        )
        return {"status": "success", "message": "런처가 성공적으로 실행되었습니다."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)