import React, { useState, useRef } from 'react';
import { Home, Compass, Archive, Settings, ChevronRight } from 'lucide-react';

// 로그인 모달 컴포넌트
function LoginModal({ isOpen, onClose, onLogin }) {
  const handleSubmit = (e) => {
    e.preventDefault();
    const formData = new FormData(e.target);
    const email = formData.get('email');
    const password = formData.get('password');
    
    onLogin({
      name: email.split('@')[0],
      email: email
    });
  };

  if (!isOpen) return null;

  return (
    <div 
      className="fixed inset-0 bg-black/50 flex items-center justify-center z-50"
      onClick={onClose}
    >
      <div 
        className="bg-white rounded-2xl p-8 w-96 shadow-2xl animate-fadeIn"
        onClick={(e) => e.stopPropagation()}
      >
        <div className="flex items-center justify-between mb-6">
          <h2 className="text-2xl font-bold text-gray-900">로그인</h2>
          <button
            onClick={onClose}
            className="text-gray-400 hover:text-gray-600 transition-colors"
          >
            <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>

        <form onSubmit={handleSubmit}>
          <div className="mb-4">
            <label className="block text-sm font-medium text-gray-700 mb-2">
              이메일
            </label>
            <input
              type="email"
              name="email"
              className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-all"
              placeholder="example@email.com"
              required
            />
          </div>

          <div className="mb-6">
            <label className="block text-sm font-medium text-gray-700 mb-2">
              비밀번호
            </label>
            <input
              type="password"
              name="password"
              className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-all"
              placeholder="••••••••"
              required
            />
          </div>

          <button
            type="submit"
            className="w-full bg-gradient-to-r from-blue-500 to-indigo-500 text-white py-3 rounded-lg font-medium hover:from-blue-600 hover:to-indigo-600 transition-all shadow-lg hover:shadow-xl"
          >
            로그인
          </button>

          <div className="mt-4 text-center">
            <button
              type="button"
              className="text-sm text-gray-500 hover:text-gray-700"
            >
              계정이 없으신가요? <span className="text-blue-500 font-medium">회원가입</span>
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}

// 프로필 메뉴 컴포넌트
function ProfileMenu({ isOpen, onClose, userInfo, onLogout }) {
  const menuRef = useRef(null);

  React.useEffect(() => {
    const handleClickOutside = (event) => {
      if (menuRef.current && !menuRef.current.contains(event.target)) {
        onClose();
      }
    };

    if (isOpen) {
      document.addEventListener('mousedown', handleClickOutside);
    }

    return () => {
      document.removeEventListener('mousedown', handleClickOutside);
    };
  }, [isOpen, onClose]);

  if (!isOpen) return null;

  return (
    <div 
      ref={menuRef}
      className="absolute top-full left-4 right-4 mt-2 bg-white rounded-xl shadow-xl border border-gray-200 z-50 overflow-hidden animate-slideDown"
    >
      <div className="p-4 border-b border-gray-100">
        <p className="font-bold text-gray-900">{userInfo.name}</p>
        <p className="text-sm text-gray-500">{userInfo.email}</p>
      </div>
      
      <div className="p-2">
        <button
          onClick={() => {
            onLogout();
            onClose();
          }}
          className="w-full px-4 py-2.5 text-left text-sm text-red-600 hover:bg-red-50 rounded-lg transition-colors flex items-center gap-2"
        >
          <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17 16l4-4m0 0l-4-4m4 4H7m6 4v1a3 3 0 01-3 3H6a3 3 0 01-3-3V7a3 3 0 013-3h4a3 3 0 013 3v1" />
          </svg>
          로그아웃
        </button>
      </div>
    </div>
  );
}

// 샘플 데이터
const monthlyThemes = [
  {
    id: 1,
    title: '겨울테마...',
    bgColor: 'bg-gradient-to-br from-blue-100 via-cyan-50 to-blue-200',
    tags: ['#겨울', '#눈']
  },
  {
    id: 2,
    title: '봄 테마',
    bgColor: 'bg-gradient-to-br from-pink-100 via-rose-50 to-pink-200',
    tags: ['#봄', '#꽃']
  },
  {
    id: 3,
    title: '가을 테마',
    bgColor: 'bg-gradient-to-br from-green-100 via-emerald-50 to-green-200',
    tags: ['#가을', '#단풍']
  },
  {
    id: 4,
    title: '밤 테마',
    bgColor: 'bg-gradient-to-br from-indigo-500 via-blue-600 to-indigo-700',
    isDark: true,
    tags: ['#밤', '#별']
  }
];

const trendingItems = [
  {
    id: 1,
    title: '햄스터',
    tags: ['#귀여운', '#동물', '#깜찍함'],
    bgColor: 'bg-gradient-to-br from-purple-50 to-purple-100'
  },
  {
    id: 2,
    title: '골든 햄스터',
    tags: ['#천', '#솜로'],
    bgColor: 'bg-gradient-to-br from-orange-50 to-amber-100'
  },
  {
    id: 3,
    title: '가을 테마',
    tags: ['#따뜻한', '#이광재'],
    bgColor: 'bg-gradient-to-br from-red-50 to-orange-100'
  },
  {
    id: 4,
    title: '가을 데마',
    tags: [],
    bgColor: 'bg-gradient-to-br from-gray-50 to-slate-100'
  }
];

// 메인 컴포넌트
export default function IconChangerUI() {
  const [activeMenu, setActiveMenu] = useState('home');
  const [hoveredCard, setHoveredCard] = useState(null);
  const [isLoggedIn, setIsLoggedIn] = useState(false);
  const [showProfileMenu, setShowProfileMenu] = useState(false);
  const [showLoginModal, setShowLoginModal] = useState(false);
  const [userInfo, setUserInfo] = useState(null);
  const monthlyScrollRef = useRef(null);
  const trendingScrollRef = useRef(null);

  const scroll = (ref, direction) => {
    if (ref.current) {
      const scrollAmount = 420;
      ref.current.scrollBy({
        left: direction === 'left' ? -scrollAmount : scrollAmount,
        behavior: 'smooth'
      });
    }
  };

  const handleLogin = (userData) => {
    setUserInfo(userData);
    setIsLoggedIn(true);
    setShowLoginModal(false);
  };

  const handleLogout = () => {
    setIsLoggedIn(false);
    setUserInfo(null);
  };

  return (
    <div className="flex h-screen bg-white font-sans">
      {/* 심플한 사이드바 */}
      <aside className="w-44 bg-white border-r border-gray-200 flex flex-col">
        {/* 프로필 */}
        <div className="p-4 border-b border-gray-100 relative">
          <div 
            className="flex items-center gap-2 cursor-pointer hover:bg-gray-50 rounded-lg p-1 transition-colors"
            onClick={() => {
              if (isLoggedIn) {
                setShowProfileMenu(!showProfileMenu);
              } else {
                setShowLoginModal(true);
              }
            }}
          >
            <div className="w-8 h-8 rounded-full bg-gradient-to-br from-red-400 to-pink-400 flex items-center justify-center">
              <span className="text-white text-xs font-medium">
                {isLoggedIn && userInfo ? userInfo.name[0].toUpperCase() : '아'}
              </span>
            </div>
            <span className="text-sm text-gray-700">
              {isLoggedIn && userInfo ? userInfo.name : '아이콘...'}
            </span>
          </div>

          {/* 프로필 메뉴 */}
          {isLoggedIn && userInfo && (
            <ProfileMenu
              isOpen={showProfileMenu}
              onClose={() => setShowProfileMenu(false)}
              userInfo={userInfo}
              onLogout={handleLogout}
            />
          )}
        </div>

        {/* 메뉴 */}
        <nav className="flex-1 py-4">
          <div className="mb-3 px-4">
            <h3 className="text-xs font-bold text-gray-500 mb-2">탐색하기</h3>
          </div>
          <div className="space-y-0.5 px-2">
            {[
              { id: 'home', icon: Home, label: '홈' },
              { id: 'explore', icon: Compass, label: '탐색' },
              { id: 'archive', icon: Archive, label: '보관함' },
              { id: 'settings', icon: Settings, label: '설정' }
            ].map(item => (
              <button
                key={item.id}
                onClick={() => setActiveMenu(item.id)}
                className={`w-full flex items-center gap-2 px-3 py-2 rounded-lg text-sm transition-all ${
                  activeMenu === item.id
                    ? 'bg-red-50 text-red-600 font-medium'
                    : 'text-gray-600 hover:bg-gray-50'
                }`}
              >
                <item.icon className="w-4 h-4" strokeWidth={2} />
                <span>{item.label}</span>
              </button>
            ))}
          </div>
        </nav>
      </aside>

      {/* 메인 콘텐츠 */}
      <main className="flex-1 overflow-y-auto bg-gray-50">
        <div className="max-w-7xl mx-auto px-10 py-10">
          {/* 홈 화면 */}
          {activeMenu === 'home' && (
            <>
              {/* 이달의 인기테마 */}
              <section className="mb-14">
                <div className="flex items-center justify-between mb-6">
                  <h2 className="text-3xl font-bold text-gray-900">이달의 인기테마</h2>
                  <div className="flex items-center gap-2">
                    <button 
                      onClick={() => scroll(monthlyScrollRef, 'left')}
                      className="p-2 rounded-lg hover:bg-gray-200 transition-colors bg-gray-100"
                    >
                      <ChevronRight className="w-5 h-5 text-gray-600 rotate-180" strokeWidth={2} />
                    </button>
                    <button 
                      onClick={() => scroll(monthlyScrollRef, 'right')}
                      className="p-2 rounded-lg hover:bg-gray-200 transition-colors bg-gray-100"
                    >
                      <ChevronRight className="w-5 h-5 text-gray-600" strokeWidth={2} />
                    </button>
                  </div>
                </div>
                
                <div ref={monthlyScrollRef} className="flex gap-6 overflow-x-auto pb-3 scrollbar-hide">
                  {monthlyThemes.map((theme) => (
                    <div
                      key={theme.id}
                      onMouseEnter={() => setHoveredCard(`monthly-${theme.id}`)}
                      onMouseLeave={() => setHoveredCard(null)}
                      className="flex-shrink-0 w-96 cursor-pointer"
                    >
                      <div className={`relative rounded-2xl overflow-hidden transition-all duration-300 ${
                        hoveredCard === `monthly-${theme.id}` 
                          ? 'shadow-xl scale-[1.02] -translate-y-1' 
                          : 'shadow-md'
                      }`}>
                        {/* 배경 */}
                        <div className={`h-60 ${theme.bgColor} flex items-center justify-center relative`}>
                          <div className="text-gray-400 text-sm">이미지 영역</div>
                          
                          {/* 배지 */}
                          {theme.badge && (
                            <div className="absolute top-4 left-4 bg-pink-500 text-white px-3 py-1.5 rounded-full text-sm font-bold shadow-lg">
                              {theme.badge}
                            </div>
                          )}
                        </div>
                        
                        {/* 정보 */}
                        <div className={`p-5 ${theme.isDark ? 'bg-gray-900' : 'bg-white'}`}>
                          <h3 className={`font-bold text-lg mb-2.5 ${theme.isDark ? 'text-white' : 'text-gray-900'}`}>
                            {theme.title}
                          </h3>
                          <div className="flex flex-wrap gap-2">
                            {theme.tags && theme.tags.map((tag, tagIndex) => (
                              <span 
                                key={tagIndex}
                                className={`text-sm px-2.5 py-1 rounded-md ${
                                  theme.isDark 
                                    ? 'text-gray-300 bg-gray-800' 
                                    : 'text-gray-600 bg-gray-100'
                                }`}
                              >
                                {tag}
                              </span>
                            ))}
                          </div>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              </section>

              {/* 요즘 뜨는 */}
              <section>
                <div className="flex items-center justify-between mb-6">
                  <h2 className="text-3xl font-bold text-gray-900">요즘 뜨는</h2>
                  <div className="flex items-center gap-2">
                    <button 
                      onClick={() => scroll(trendingScrollRef, 'left')}
                      className="p-2 rounded-lg hover:bg-gray-200 transition-colors bg-gray-100"
                    >
                      <ChevronRight className="w-5 h-5 text-gray-600 rotate-180" strokeWidth={2} />
                    </button>
                    <button 
                      onClick={() => scroll(trendingScrollRef, 'right')}
                      className="p-2 rounded-lg hover:bg-gray-200 transition-colors bg-gray-100"
                    >
                      <ChevronRight className="w-5 h-5 text-gray-600" strokeWidth={2} />
                    </button>
                  </div>
                </div>
                
                <div ref={trendingScrollRef} className="flex gap-6 overflow-x-auto pb-3 scrollbar-hide">
                  {trendingItems.map((item) => (
                    <div
                      key={item.id}
                      onMouseEnter={() => setHoveredCard(`trending-${item.id}`)}
                      onMouseLeave={() => setHoveredCard(null)}
                      className="flex-shrink-0 w-96 cursor-pointer"
                    >
                      <div className={`bg-white rounded-2xl overflow-hidden transition-all duration-300 ${
                        hoveredCard === `trending-${item.id}`
                          ? 'shadow-xl scale-[1.02] -translate-y-1'
                          : 'shadow-md'
                      }`}>
                        {/* 이미지 영역 */}
                        <div className={`h-60 ${item.bgColor} flex items-center justify-center`}>
                          <div className="text-gray-400 text-sm">이미지 영역</div>
                        </div>
                        
                        {/* 정보 */}
                        <div className="p-5">
                          <h3 className="font-bold text-gray-900 mb-2.5 text-base">{item.title}</h3>
                          <div className="flex flex-wrap gap-2">
                            {item.tags.map((tag, tagIndex) => (
                              <span 
                                key={tagIndex}
                                className="text-sm text-gray-600 bg-gray-100 px-2.5 py-1 rounded-md"
                              >
                                {tag}
                              </span>
                            ))}
                          </div>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              </section>
            </>
          )}

          {/* 탐색 화면 */}
          {activeMenu === 'explore' && (
            <div className="flex items-center justify-center h-96">
              <div className="text-center">
                <Compass className="w-16 h-16 text-gray-300 mx-auto mb-4" />
                <h3 className="text-xl font-bold text-gray-900 mb-2">탐색</h3>
                <p className="text-gray-500">탐색 페이지를 준비 중입니다.</p>
              </div>
            </div>
          )}

          {/* 보관함 화면 */}
          {activeMenu === 'archive' && (
            <div className="flex items-center justify-center h-96">
              <div className="text-center">
                <Archive className="w-16 h-16 text-gray-300 mx-auto mb-4" />
                <h3 className="text-xl font-bold text-gray-900 mb-2">보관함</h3>
                <p className="text-gray-500">보관함 페이지를 준비 중입니다.</p>
              </div>
            </div>
          )}

          {/* 설정 화면 */}
          {activeMenu === 'settings' && (
            <div className="flex items-center justify-center h-96">
              <div className="text-center">
                <Settings className="w-16 h-16 text-gray-300 mx-auto mb-4" />
                <h3 className="text-xl font-bold text-gray-900 mb-2">설정</h3>
                <p className="text-gray-500">설정 페이지를 준비 중입니다.</p>
              </div>
            </div>
          )}
        </div>
      </main>

      {/* 로그인 모달 */}
      <LoginModal
        isOpen={showLoginModal}
        onClose={() => setShowLoginModal(false)}
        onLogin={handleLogin}
      />

      {/* 스타일 */}
      <style>{`
        @import url('https://fonts.googleapis.com/css2?family=Noto+Sans+KR:wght@400;500;700;900&display=swap');
        
        * {
          font-family: 'Noto Sans KR', -apple-system, BlinkMacSystemFont, system-ui, sans-serif;
        }
        
        .scrollbar-hide::-webkit-scrollbar {
          display: none;
        }
        
        .scrollbar-hide {
          -ms-overflow-style: none;
          scrollbar-width: none;
        }

        @keyframes fadeIn {
          from {
            opacity: 0;
            transform: scale(0.95);
          }
          to {
            opacity: 1;
            transform: scale(1);
          }
        }
        
        .animate-fadeIn {
          animation: fadeIn 0.2s ease-out;
        }

        @keyframes slideDown {
          from {
            opacity: 0;
            transform: translateY(-10px);
          }
          to {
            opacity: 1;
            transform: translateY(0);
          }
        }
        
        .animate-slideDown {
          animation: slideDown 0.2s ease-out;
        }
      `}</style>
    </div>
  );
}
