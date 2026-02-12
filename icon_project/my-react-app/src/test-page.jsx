import React, { useState } from 'react';
import { Home, Compass, Archive, Code, Settings, User, Play, Monitor } from 'lucide-react';

export default function TestPage() {
  const [activeMenu, setActiveMenu] = useState('test');

  // --- [상태 관리: 계산기 및 런처] ---
  const [calcExpression, setCalcExpression] = useState("");
  const [calcResult, setCalcResult] = useState("");
  const [launchStatus, setLaunchStatus] = useState("");

  // 1. 계산기 통신 함수
  const handleCalculate = async (val) => {
    if (val === "C") {
      setCalcExpression("");
      setCalcResult("");
      return;
    }
    if (val === "=") {
      if (!calcExpression) return;
      try {
        const response = await fetch('http://localhost:8000/api/calculate', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ expression: calcExpression }),
        });
        const data = await response.json();
        if (response.ok) {
          setCalcResult(data.result);
          setCalcExpression(data.result);
        } else { setCalcResult("오류"); }
      } catch (err) { setCalcResult("서버 연결 실패"); }
      return;
    }
    setCalcExpression(prev => prev + val);
    setCalcResult("");
  };

  // 2. 데스크톱 런처 실행 함수
  const handleLaunchLauncher = async () => {
    setLaunchStatus("런처 기동 중...");
    try {
      const response = await fetch('http://localhost:8000/api/launch-launcher', {
        method: 'POST',
      });
      const data = await response.json();
      if (response.ok) {
        setLaunchStatus("성공: 런처가 실행되었습니다.");
        setTimeout(() => setLaunchStatus(""), 4000);
      } else {
        setLaunchStatus("실패: " + data.detail);
      }
    } catch (err) {
      setLaunchStatus("서버 연결 실패");
    }
  };

  return (
    <div className="flex h-screen bg-slate-50 font-sans antialiased">
      {/* 사이드바 */}
      <aside className="w-72 bg-white border-r border-slate-200 flex flex-col shadow-sm">
        <div className="p-6 border-b border-slate-100">
          <h1 className="text-xl font-bold text-slate-800 flex items-center gap-2">
            <Archive className="text-blue-600" /> 통합 대시보드
          </h1>
        </div>
        <nav className="p-4 space-y-1">
          {[{ id: 'home', icon: Home, label: '홈' }, { id: 'test', icon: Code, label: '테스트' }].map(item => (
            <button
              key={item.id}
              onClick={() => setActiveMenu(item.id)}
              className={`w-full flex items-center gap-3 px-4 py-3 rounded-xl transition-all ${
                activeMenu === item.id ? 'bg-blue-600 text-white shadow-md' : 'text-slate-600 hover:bg-slate-50'
              }`}
            >
              <item.icon size={20} /> <span>{item.label}</span>
            </button>
          ))}
        </nav>
      </aside>

      {/* 메인 콘텐츠 */}
      <main className="flex-1 overflow-y-auto p-10">
        <header className="mb-10">
          <h2 className="text-3xl font-bold text-slate-900 mb-2">보안 도구 테스트 센터</h2>
          <p className="text-slate-500">정보보안 프로젝트의 기능을 실시간으로 제어하고 모니터링합니다.</p>
        </header>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
          {/* 영역 1: 데스크톱 아이콘 런처 (PySide6 실행 영역) */}
          <section className="bg-white rounded-3xl shadow-lg border border-slate-200 overflow-hidden">
            <div className="bg-emerald-600 p-5 text-white flex justify-between items-center font-bold">
              <span className="flex items-center gap-2"><Monitor size={20} /> 데스크톱 런처 제어</span>
              <span className="text-xs bg-white/20 px-3 py-1 rounded-full uppercase">Active Control</span>
            </div>
            <div className="p-8 h-[420px] bg-slate-900 flex flex-col items-center justify-center text-center">
              <div className="w-24 h-24 bg-emerald-500/10 rounded-full flex items-center justify-center mb-6 border border-emerald-500/20">
                <Play className="text-emerald-400 fill-emerald-400 ml-1" size={40} />
              </div>
              <h3 className="text-white text-xl font-bold mb-3">Desktop Icon Launcher v3.1</h3>
              <p className="text-slate-400 text-sm mb-8 leading-relaxed max-w-xs">
                바탕화면 항목을 자동으로 스캔하여 GIF 커스텀 아이콘을 생성하는 프로그램을 기동합니다.
              </p>
              <button
                onClick={handleLaunchLauncher}
                className="px-10 py-4 bg-emerald-500 hover:bg-emerald-400 text-white font-extrabold rounded-2xl transition-all active:scale-95 shadow-lg shadow-emerald-500/20"
              >
                런처 프로그램 실행
              </button>
              {launchStatus && <p className="mt-4 text-emerald-400 text-sm font-medium animate-pulse">{launchStatus}</p>}
            </div>
          </section>

          {/* 영역 2: 계산기 테스트 (FastAPI 연동) */}
          <section className="bg-white rounded-3xl shadow-lg border border-slate-200 overflow-hidden">
            <div className="bg-indigo-600 p-5 text-white flex justify-between items-center font-bold">
              <span className="flex items-center gap-2"><Settings size={20} /> 백엔드 연산 테스트</span>
              <span className="text-xs bg-white/20 px-3 py-1 rounded-full uppercase">Connected</span>
            </div>
            <div className="p-8 h-[420px] bg-slate-900 flex flex-col">
              <div className="bg-slate-800 p-5 rounded-2xl mb-6 text-right border border-slate-700 shadow-inner">
                <div className="text-slate-500 text-sm font-mono mb-1 h-5">{calcExpression}</div>
                <div className="text-white text-4xl font-bold font-mono tracking-tighter">{calcResult || calcExpression || "0"}</div>
              </div>
              <div className="grid grid-cols-4 gap-3 flex-1">
                {["7", "8", "9", "/", "4", "5", "6", "*", "1", "2", "3", "-", "0", ".", "C", "+"].map(btn => (
                  <button
                    key={btn}
                    onClick={() => handleCalculate(btn)}
                    className="bg-slate-700 hover:bg-slate-600 text-slate-200 font-bold rounded-xl transition-colors text-lg"
                  >
                    {btn}
                  </button>
                ))}
                <button
                  onClick={() => handleCalculate("=")}
                  className="col-span-4 bg-indigo-500 hover:bg-indigo-400 text-white font-bold py-4 rounded-xl shadow-lg shadow-indigo-500/20"
                >
                  Request Analysis
                </button>
              </div>
            </div>
          </section>
        </div>
      </main>
    </div>
  );
}