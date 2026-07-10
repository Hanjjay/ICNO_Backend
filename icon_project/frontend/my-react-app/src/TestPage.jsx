import { useState } from 'react';

export default function TestPage({ onNavigate }) {
  const [activeMenu, setActiveMenu] = useState('test');
  const [sidebarOpen, setSidebarOpen] = useState(true);
  const [calcExpression, setCalcExpression] = useState("");
  const [calcResult, setCalcResult] = useState("");
  const [launchStatus, setLaunchStatus] = useState("");

  // 계산기 로직
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
        } else {
          setCalcResult("Error");
        }
      } catch (error) {
        setCalcResult("Connection Error");
      }
      return;
    }

    setCalcExpression(calcExpression + val);
  };

  // 런처 실행
  const handleLaunchLauncher = async () => {
    setLaunchStatus("실행 중...");
    
    try {
      const response = await fetch('http://localhost:8000/api/launch-launcher', {
        method: 'POST',
      });
      
      const data = await response.json();
      
      if (response.ok) {
        setLaunchStatus(data.message);
      } else {
        setLaunchStatus("실행 실패");
      }
    } catch (error) {
      setLaunchStatus("Connection Error");
    }
  };

  return (
    <div className="flex h-screen bg-gradient-to-br from-gray-50 to-gray-100">
      {/* 왼쪽 사이드바 */}
      <div className={`bg-white border-r shadow-sm ${sidebarOpen ? 'w-64' : 'w-0'} transition-all duration-300 overflow-hidden`}>
        <div className="p-6">
          <button 
            onClick={() => onNavigate('explore')}
            className="flex items-center gap-2 text-gray-600 hover:text-gray-900 mb-6 transition-colors"
          >
            <span className="text-xl">←</span>
            <span className="text-sm font-medium">아이콘...</span>
          </button>
        </div>

        <nav className="space-y-1 px-3">
          {/* 홈 */}
          <button
            onClick={() => {
              setActiveMenu('home');
              onNavigate('home');
            }}
            className={`w-full flex items-center gap-3 px-4 py-3 rounded-lg transition-colors ${
              activeMenu === 'home' ? 'bg-blue-50 text-blue-600' : 'text-gray-700 hover:bg-gray-50'
            }`}
          >
            <span className="text-lg">🏠</span>
            <span className="text-sm font-medium">홈</span>
          </button>

          {/* 탐색 */}
          <button
            onClick={() => {
              setActiveMenu('explore');
              onNavigate('explore');
            }}
            className={`w-full flex items-center gap-3 px-4 py-3 rounded-lg transition-colors ${
              activeMenu === 'explore' ? 'bg-blue-50 text-blue-600' : 'text-gray-700 hover:bg-gray-50'
            }`}
          >
            <span className="text-lg">🔍</span>
            <span className="text-sm font-medium">탐색</span>
          </button>

          {/* 보관함 */}
          <button
            onClick={() => {
              setActiveMenu('archive');
              onNavigate('archive');
            }}
            className={`w-full flex items-center gap-3 px-4 py-3 rounded-lg transition-colors ${
              activeMenu === 'archive' ? 'bg-blue-50 text-blue-600' : 'text-gray-700 hover:bg-gray-50'
            }`}
          >
            <span className="text-lg">📦</span>
            <span className="text-sm font-medium">보관함</span>
          </button>

          {/* 설정 */}
          <button
            onClick={() => {
              setActiveMenu('settings');
              onNavigate('settings');
            }}
            className={`w-full flex items-center gap-3 px-4 py-3 rounded-lg transition-colors ${
              activeMenu === 'settings' ? 'bg-blue-50 text-blue-600' : 'text-gray-700 hover:bg-gray-50'
            }`}
          >
            <span className="text-lg">⚙️</span>
            <span className="text-sm font-medium">설정</span>
          </button>

          {/* 테스트 페이지 */}
          <button
            onClick={() => {
              setActiveMenu('test');
              onNavigate('test');
            }}
            className={`w-full flex items-center gap-3 px-4 py-3 rounded-lg transition-colors ${
              activeMenu === 'test' ? 'bg-blue-50 text-blue-600' : 'text-gray-700 hover:bg-gray-50'
            }`}
          >
            <span className="text-lg">🧪</span>
            <span className="text-sm font-medium">테스트 페이지</span>
          </button>

          {/* 적용창 - 새로 추가! */}
          <button
            onClick={() => {
              setActiveMenu('apply-window');
              onNavigate('apply-window');
            }}
            className={`w-full flex items-center gap-3 px-4 py-3 rounded-lg transition-colors ${
              activeMenu === 'apply-window' ? 'bg-blue-50 text-blue-600' : 'text-gray-700 hover:bg-gray-50'
            }`}
          >
            <span className="text-lg">🎨</span>
            <span className="text-sm font-medium">적용창</span>
          </button>
        </nav>
      </div>

      {/* 메인 컨텐츠 */}
      <div className="flex-1 overflow-auto">
        <div className="max-w-7xl mx-auto p-8">
          {/* 헤더 */}
          <div className="mb-8">
            <h1 className="text-3xl font-bold text-gray-900 mb-2">보안 도구 테스트 센터</h1>
            <p className="text-gray-600">정보보안 프로젝트의 기능을 실시간으로 체험하고 모니터링합니다.</p>
          </div>

          {/* 카드 그리드 */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {/* 데스크톱 런처 제어 */}
            <div className="bg-white rounded-xl shadow-lg p-6 border border-gray-200">
              <div className="flex items-center justify-between mb-4">
                <h2 className="text-xl font-semibold text-gray-900 flex items-center gap-2">
                  <span className="text-2xl">💻</span>
                  데스크톱 런처 제어
                </h2>
                <span className="px-3 py-1 bg-green-100 text-green-700 rounded-full text-xs font-medium">
                  ACTIVE CONTROL
                </span>
              </div>

              <div className="bg-gray-900 rounded-lg p-8 mb-4">
                <div className="flex flex-col items-center justify-center space-y-4">
                  <div className="w-20 h-20 bg-green-600 rounded-full flex items-center justify-center">
                    <svg className="w-10 h-10 text-white" fill="currentColor" viewBox="0 0 24 24">
                      <path d="M8 5v14l11-7z" />
                    </svg>
                  </div>
                  
                  <div className="text-center">
                    <h3 className="text-white text-xl font-bold mb-2">Desktop Icon Launcher v3.1</h3>
                    <p className="text-gray-400 text-sm">
                      바탕화면 항목을 자동으로 스캔하여 GUI 커스텀 아이콘을 생성하는 프로그램을 기동합니다.
                    </p>
                  </div>
                </div>
              </div>

              <button
                onClick={handleLaunchLauncher}
                className="w-full bg-green-600 hover:bg-green-700 text-white font-semibold py-3 rounded-lg transition-colors"
              >
                런처 프로그램 실행
              </button>

              {launchStatus && (
                <div className="mt-4 p-3 bg-blue-50 border border-blue-200 rounded-lg">
                  <p className="text-sm text-blue-700">{launchStatus}</p>
                </div>
              )}
            </div>

            {/* 백엔드 연산 테스트 */}
            <div className="bg-white rounded-xl shadow-lg p-6 border border-gray-200">
              <div className="flex items-center justify-between mb-4">
                <h2 className="text-xl font-semibold text-gray-900 flex items-center gap-2">
                  <span className="text-2xl">⚙️</span>
                  백엔드 연산 테스트
                </h2>
                <span className="px-3 py-1 bg-purple-100 text-purple-700 rounded-full text-xs font-medium">
                  CONNECTED
                </span>
              </div>

              <div className="bg-gray-900 rounded-lg p-6 mb-4">
                <div className="mb-4">
                  <input
                    type="text"
                    value={calcExpression}
                    readOnly
                    placeholder="0"
                    className="w-full bg-gray-800 text-white text-right text-2xl p-4 rounded-lg border-2 border-gray-700 font-mono"
                  />
                </div>

                <div className="grid grid-cols-4 gap-2">
                  {['7', '8', '9', '/'].map((val) => (
                    <button
                      key={val}
                      onClick={() => handleCalculate(val)}
                      className="bg-gray-700 hover:bg-gray-600 text-white py-3 rounded-lg font-semibold transition-colors"
                    >
                      {val}
                    </button>
                  ))}
                  {['4', '5', '6', '*'].map((val) => (
                    <button
                      key={val}
                      onClick={() => handleCalculate(val)}
                      className="bg-gray-700 hover:bg-gray-600 text-white py-3 rounded-lg font-semibold transition-colors"
                    >
                      {val}
                    </button>
                  ))}
                  {['1', '2', '3', '-'].map((val) => (
                    <button
                      key={val}
                      onClick={() => handleCalculate(val)}
                      className="bg-gray-700 hover:bg-gray-600 text-white py-3 rounded-lg font-semibold transition-colors"
                    >
                      {val}
                    </button>
                  ))}
                  {['0', '.', 'C', '+'].map((val) => (
                    <button
                      key={val}
                      onClick={() => handleCalculate(val)}
                      className="bg-gray-700 hover:bg-gray-600 text-white py-3 rounded-lg font-semibold transition-colors"
                    >
                      {val}
                    </button>
                  ))}
                </div>
              </div>

              <button
                onClick={() => handleCalculate('=')}
                className="w-full bg-purple-600 hover:bg-purple-700 text-white font-semibold py-3 rounded-lg transition-colors"
              >
                Request Analysis
              </button>

              {calcResult && (
                <div className="mt-4 p-4 bg-purple-50 border border-purple-200 rounded-lg">
                  <p className="text-sm text-gray-600 mb-1">Result:</p>
                  <p className="text-2xl font-bold text-purple-700">{calcResult}</p>
                </div>
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
