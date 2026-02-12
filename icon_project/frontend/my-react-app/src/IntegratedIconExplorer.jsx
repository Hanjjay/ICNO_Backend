import React, { useState, useRef } from 'react';
import { Search, Filter, List, Grid3x3, Calendar, MoreVertical, Home, Compass, Archive, Settings, User, X, Download, Share2, ThumbsUp, Star, Tag, Layers, TrendingUp, Clock, Award, Download as DownloadIcon, ChevronDown, History, ChevronRight, ArrowLeft, Plus, Edit2, Check } from 'lucide-react';

// =============================================================================
// 로그인 모달 컴포넌트
// =============================================================================
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

// =============================================================================
// 메인 통합 컴포넌트
// =============================================================================
export default function IntegratedIconExplorer() {
  // 페이지 상태 관리
  const [activePage, setActivePage] = useState('explore'); // 'home', 'explore', 'archive'
  
  // 공통 상태
  const [isLoggedIn, setIsLoggedIn] = useState(false);
  const [userInfo, setUserInfo] = useState(null);
  const [showLoginModal, setShowLoginModal] = useState(false);
  
  const handleLogin = (userData) => {
    setUserInfo(userData);
    setIsLoggedIn(true);
    setShowLoginModal(false);
  };

  const handleLogout = () => {
    setIsLoggedIn(false);
    setUserInfo(null);
  };

  // 페이지 렌더링
  const renderPage = () => {
    switch(activePage) {
      case 'home':
        return <HomePage isLoggedIn={isLoggedIn} userInfo={userInfo} onShowLogin={() => setShowLoginModal(true)} />;
      case 'explore':
        return <ExplorePage />;
      case 'archive':
        return <ArchivePage />;
      default:
        return <ExplorePage />;
    }
  };

  return (
    <div className="flex h-screen bg-gradient-to-br from-slate-50 to-slate-100 font-sans overflow-hidden">
      {/* 공통 스타일 */}
      <style>{`
        @import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700&family=Crimson+Pro:wght@300;400&display=swap');
        
        * {
          font-family: 'DM Sans', sans-serif;
        }

        .icon-card {
          transition: all 0.4s cubic-bezier(0.34, 1.56, 0.64, 1);
          position: relative;
        }

        .icon-card::before {
          content: '';
          position: absolute;
          top: 0;
          left: 0;
          right: 0;
          bottom: 0;
          background: linear-gradient(135deg, rgba(255,255,255,0.9), rgba(255,255,255,0.4));
          border-radius: 16px;
          opacity: 0;
          transition: opacity 0.3s ease;
        }

        .icon-card:hover::before {
          opacity: 1;
        }

        .icon-card:hover {
          transform: translateY(-8px) scale(1.02);
          box-shadow: 0 20px 40px rgba(0,0,0,0.12);
        }

        .icon-image {
          transition: transform 0.5s cubic-bezier(0.34, 1.56, 0.64, 1);
        }

        .icon-card:hover .icon-image {
          transform: rotate(-5deg) scale(1.1);
        }

        .sidebar-item {
          transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
          position: relative;
        }

        .sidebar-item::before {
          content: '';
          position: absolute;
          left: 0;
          top: 50%;
          transform: translateY(-50%);
          width: 3px;
          height: 0;
          background: linear-gradient(180deg, #ec4899, #f97316);
          border-radius: 0 2px 2px 0;
          transition: height 0.3s ease;
        }

        .sidebar-item:hover::before,
        .sidebar-item.active::before {
          height: 70%;
        }

        .sidebar-item:hover {
          background: linear-gradient(90deg, rgba(236,72,153,0.08), transparent);
          transform: translateX(4px);
        }

        .search-bar {
          transition: all 0.3s ease;
        }

        .search-bar:focus-within {
          transform: scale(1.02);
          box-shadow: 0 4px 20px rgba(236,72,153,0.15);
        }

        @keyframes fadeInUp {
          from {
            opacity: 0;
            transform: translateY(20px);
          }
          to {
            opacity: 1;
            transform: translateY(0);
          }
        }

        .gradient-text {
          background: linear-gradient(135deg, #ec4899 0%, #f97316 100%);
          -webkit-background-clip: text;
          -webkit-text-fill-color: transparent;
          background-clip: text;
        }

        .modal-overlay {
          animation: fadeIn 0.3s ease;
        }

        .modal-content {
          animation: slideUp 0.4s ease;
        }

        @keyframes fadeIn {
          from { opacity: 0; }
          to { opacity: 1; }
        }

        @keyframes slideUp {
          from {
            opacity: 0;
            transform: translateY(50px);
          }
          to {
            opacity: 1;
            transform: translateY(0);
          }
        }

        .star-rating {
          cursor: pointer;
          transition: all 0.2s ease;
        }

        .star-rating:hover {
          transform: scale(1.1);
        }

        .checkbox-custom {
          appearance: none;
          width: 20px;
          height: 20px;
          border: 2px solid #cbd5e1;
          border-radius: 4px;
          cursor: pointer;
          transition: all 0.2s ease;
          position: relative;
        }

        .checkbox-custom:checked {
          background: linear-gradient(135deg, #ec4899, #f97316);
          border-color: #ec4899;
        }

        .checkbox-custom:checked::after {
          content: '✓';
          position: absolute;
          color: white;
          font-size: 14px;
          top: 50%;
          left: 50%;
          transform: translate(-50%, -50%);
        }

        .checkbox-custom:hover {
          border-color: #ec4899;
          transform: scale(1.05);
        }

        .set-badge {
          background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        }
      `}</style>

      {/* 사이드바 */}
      <div className="w-64 bg-white/80 backdrop-blur-md border-r border-slate-200/60 flex flex-col shadow-xl">
        <div className="p-6 border-b border-slate-200/60">
          <div 
            className="flex items-center gap-3 cursor-pointer"
            onClick={() => {
              if (!isLoggedIn) {
                setShowLoginModal(true);
              }
            }}
          >
            <div className="w-10 h-10 bg-gradient-to-br from-pink-500 to-orange-500 rounded-xl flex items-center justify-center shadow-lg">
              <User className="w-5 h-5 text-white" />
            </div>
            <span className="font-semibold text-slate-800 text-lg">
              {isLoggedIn && userInfo ? userInfo.name : '아이콘...'}
            </span>
          </div>
        </div>

        <nav className="flex-1 p-4">
          <div className="space-y-1">
            <div 
              onClick={() => setActivePage('home')}
              className={`sidebar-item flex items-center gap-3 px-4 py-3 rounded-xl cursor-pointer ${
                activePage === 'home' 
                  ? 'active text-slate-900 bg-gradient-to-r from-pink-50 to-transparent' 
                  : 'text-slate-700 hover:text-slate-900'
              }`}
            >
              <Home className="w-5 h-5" />
              <span className={activePage === 'home' ? 'font-semibold' : 'font-medium'}>홈</span>
            </div>
            <div 
              onClick={() => setActivePage('explore')}
              className={`sidebar-item flex items-center gap-3 px-4 py-3 rounded-xl cursor-pointer ${
                activePage === 'explore' 
                  ? 'active text-slate-900 bg-gradient-to-r from-pink-50 to-transparent' 
                  : 'text-slate-700 hover:text-slate-900'
              }`}
            >
              <Compass className="w-5 h-5" />
              <span className={activePage === 'explore' ? 'font-semibold' : 'font-medium'}>탐색</span>
            </div>
            <div 
              onClick={() => setActivePage('archive')}
              className={`sidebar-item flex items-center gap-3 px-4 py-3 rounded-xl cursor-pointer ${
                activePage === 'archive' 
                  ? 'active text-slate-900 bg-gradient-to-r from-pink-50 to-transparent' 
                  : 'text-slate-700 hover:text-slate-900'
              }`}
            >
              <Archive className="w-5 h-5" />
              <span className={activePage === 'archive' ? 'font-semibold' : 'font-medium'}>보관함</span>
            </div>
            <div className="sidebar-item flex items-center gap-3 px-4 py-3 rounded-xl cursor-pointer text-slate-700 hover:text-slate-900">
              <Settings className="w-5 h-5" />
              <span className="font-medium">설정</span>
            </div>
          </div>
        </nav>
      </div>

      {/* 메인 콘텐츠 */}
      {renderPage()}

      {/* 로그인 모달 */}
      <LoginModal 
        isOpen={showLoginModal}
        onClose={() => setShowLoginModal(false)}
        onLogin={handleLogin}
      />
    </div>
  );
}

// =============================================================================
// 홈 페이지 컴포넌트
// =============================================================================
function HomePage({ isLoggedIn, userInfo, onShowLogin }) {
  const [hoveredCard, setHoveredCard] = useState(null);
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

  const monthlyIcons = [
    { id: 1, title: '겨울 감성', emoji: '❄️', gradient: 'from-blue-400 to-cyan-300', downloads: '12.4K' },
    { id: 2, title: '따뜻한 컬러', emoji: '🔥', gradient: 'from-orange-400 to-red-400', downloads: '8.9K' },
    { id: 3, title: '파스텔 톤', emoji: '🌸', gradient: 'from-pink-300 to-purple-300', downloads: '15.2K' },
    { id: 4, title: '미니멀', emoji: '⚪', gradient: 'from-gray-300 to-gray-400', downloads: '21.8K' },
    { id: 5, title: '네온 글로우', emoji: '✨', gradient: 'from-purple-400 to-pink-400', downloads: '9.3K' }
  ];

  const trendingCollections = [
    { id: 1, name: '모던 UI 아이콘', count: 156, color: 'blue', preview: ['📱', '💻', '🖥️'] },
    { id: 2, name: '소셜 미디어', count: 89, color: 'purple', preview: ['💬', '❤️', '📷'] },
    { id: 3, name: '날씨 아이콘', count: 45, color: 'cyan', preview: ['☀️', '🌧️', '⛈️'] },
    { id: 4, name: '음식 & 음료', count: 234, color: 'orange', preview: ['🍕', '☕', '🍔'] },
    { id: 5, name: '비즈니스', count: 178, color: 'green', preview: ['💼', '📊', '📈'] }
  ];

  return (
    <main className="flex-1 overflow-y-auto bg-gray-50">
      <div className="max-w-7xl mx-auto px-10 py-10">
        {/* 헤더 */}
        <div className="mb-12">
          <h1 className="text-5xl font-bold text-gray-900 mb-4">
            완벽한 아이콘을 찾아보세요
          </h1>
          <p className="text-xl text-gray-600">
            {isLoggedIn && userInfo ? `${userInfo.name}님, 반가워요!` : '수천 개의 고품질 아이콘 중에서 선택하세요'}
          </p>
        </div>

        {/* 이달의 아이콘 */}
        <div className="mb-12">
          <div className="flex items-center justify-between mb-6">
            <h2 className="text-2xl font-bold text-gray-900">이달의 인기 아이콘</h2>
            <div className="flex gap-2">
              <button 
                onClick={() => scroll(monthlyScrollRef, 'left')}
                className="p-2 rounded-full bg-white border border-gray-200 hover:bg-gray-50 transition-colors"
              >
                <ChevronRight className="w-5 h-5 rotate-180" />
              </button>
              <button 
                onClick={() => scroll(monthlyScrollRef, 'right')}
                className="p-2 rounded-full bg-white border border-gray-200 hover:bg-gray-50 transition-colors"
              >
                <ChevronRight className="w-5 h-5" />
              </button>
            </div>
          </div>

          <div 
            ref={monthlyScrollRef}
            className="flex gap-6 overflow-x-auto pb-4 scrollbar-hide"
            style={{ scrollbarWidth: 'none', msOverflowStyle: 'none' }}
          >
            {monthlyIcons.map(icon => (
              <div
                key={icon.id}
                onMouseEnter={() => setHoveredCard(icon.id)}
                onMouseLeave={() => setHoveredCard(null)}
                className="flex-shrink-0 w-80 bg-white rounded-2xl p-6 border border-gray-200 hover:shadow-xl transition-all cursor-pointer transform hover:-translate-y-1"
              >
                <div className={`w-full h-48 bg-gradient-to-br ${icon.gradient} rounded-xl flex items-center justify-center mb-4 transform transition-transform ${hoveredCard === icon.id ? 'scale-110' : ''}`}>
                  <span className="text-7xl">{icon.emoji}</span>
                </div>
                <h3 className="text-lg font-semibold text-gray-900 mb-2">{icon.title}</h3>
                <p className="text-sm text-gray-500">{icon.downloads} 다운로드</p>
              </div>
            ))}
          </div>
        </div>

        {/* 트렌딩 컬렉션 */}
        <div>
          <div className="flex items-center justify-between mb-6">
            <h2 className="text-2xl font-bold text-gray-900">트렌딩 컬렉션</h2>
            <div className="flex gap-2">
              <button 
                onClick={() => scroll(trendingScrollRef, 'left')}
                className="p-2 rounded-full bg-white border border-gray-200 hover:bg-gray-50 transition-colors"
              >
                <ChevronRight className="w-5 h-5 rotate-180" />
              </button>
              <button 
                onClick={() => scroll(trendingScrollRef, 'right')}
                className="p-2 rounded-full bg-white border border-gray-200 hover:bg-gray-50 transition-colors"
              >
                <ChevronRight className="w-5 h-5" />
              </button>
            </div>
          </div>

          <div 
            ref={trendingScrollRef}
            className="flex gap-6 overflow-x-auto pb-4"
            style={{ scrollbarWidth: 'none', msOverflowStyle: 'none' }}
          >
            {trendingCollections.map(collection => (
              <div
                key={collection.id}
                className="flex-shrink-0 w-72 bg-white rounded-2xl p-6 border border-gray-200 hover:shadow-xl transition-all cursor-pointer"
              >
                <div className="flex gap-2 mb-4">
                  {collection.preview.map((emoji, idx) => (
                    <div
                      key={idx}
                      className={`w-16 h-16 bg-${collection.color}-50 rounded-lg flex items-center justify-center text-2xl`}
                    >
                      {emoji}
                    </div>
                  ))}
                </div>
                <h3 className="text-lg font-semibold text-gray-900 mb-1">{collection.name}</h3>
                <p className="text-sm text-gray-500">{collection.count}개 아이콘</p>
              </div>
            ))}
          </div>
        </div>
      </div>
    </main>
  );
}

// =============================================================================
// 탐색 페이지 컴포넌트  
// =============================================================================
function ExplorePage() {
  const [viewMode, setViewMode] = useState('grid');
  const [selectedIcon, setSelectedIcon] = useState(null);
  const [userRating, setUserRating] = useState(0);
  const [comment, setComment] = useState('');
  const [comments, setComments] = useState([]);
  const [showFilterPopup, setShowFilterPopup] = useState(false);
  const [selectedTags, setSelectedTags] = useState([]);
  const [filterSearch, setFilterSearch] = useState('');
  const [sortBy, setSortBy] = useState('popular');
  const [showSortDropdown, setShowSortDropdown] = useState(false);

  const sortOptions = [
    { value: 'popular', label: '인기순', icon: TrendingUp },
    { value: 'latest', label: '최신순', icon: Clock },
    { value: 'oldest', label: '오래된 순', icon: History },
    { value: 'rating', label: '평점순', icon: Award },
    { value: 'downloads', label: '다운로드순', icon: DownloadIcon },
  ];

  const availableTags = [
    '귀여운', '심플', '화려한', '미니멀', '3D', '플랫',
    '손그림', '레트로', '모던', '파스텔', '비즈니스', '게임',
    '음식', '동물', '자연', '기술', '사람', '건물', '교통', '날씨',
  ];

  const sampleIcons = [
    { 
      id: 1, 
      title: '스폰지밥 리본', 
      updated: 'Updated today', 
      type: 'pink', 
      image: '🎀',
      creator: '제작자 이름 Q',
      rating: 4.7,
      reviewCount: 110,
      description: '귀여운 핑크 리본 아이콘입니다.',
      downloads: 1234,
      tags: ['귀여운', '파스텔', '플랫'],
      setId: 'set-1',
      setName: '리본 아이콘 세트',
      uploadDate: new Date('2024-01-12'),
      popularity: 950
    },
    { 
      id: 19, 
      title: '스폰지밥 리본 (파란색)', 
      updated: 'Updated today', 
      type: 'blue', 
      image: '💙',
      creator: '제작자 이름 Q',
      rating: 4.6,
      reviewCount: 95,
      description: '시원한 파란색 리본 아이콘입니다.',
      downloads: 1100,
      tags: ['귀여운', '파스텔', '플랫'],
      setId: 'set-1',
      setName: '리본 아이콘 세트',
      uploadDate: new Date('2024-01-12'),
      popularity: 890
    },
    { 
      id: 2, 
      title: '햄스터', 
      updated: 'Updated yesterday', 
      type: 'pink', 
      image: '🐹',
      creator: 'Helena Hills',
      rating: 4.5,
      reviewCount: 89,
      description: '사랑스러운 햄스터 아이콘',
      downloads: 890,
      tags: ['동물', '귀여운', '자연'],
      setId: 'set-2',
      setName: '동물 아이콘 세트',
      uploadDate: new Date('2024-01-11'),
      popularity: 780
    },
    { 
      id: 3, 
      title: '티컵', 
      updated: 'Updated 2 days ago', 
      type: 'pink', 
      image: '☕',
      creator: 'Designer A',
      rating: 4.8,
      reviewCount: 156,
      description: '따뜻한 느낌의 티컵',
      downloads: 2341,
      tags: ['음식', '심플', '모던'],
      setId: null,
      uploadDate: new Date('2024-01-10'),
      popularity: 1200
    },
    { 
      id: 4, 
      title: 'Business Icon', 
      updated: 'Updated 3 days ago', 
      type: 'pink', 
      image: '💼',
      creator: 'Artist B',
      rating: 4.2,
      reviewCount: 45,
      description: '심플한 디자인',
      downloads: 567,
      tags: ['미니멀', '심플', '비즈니스'],
      setId: null,
      uploadDate: new Date('2024-01-09'),
      popularity: 450
    },
    { 
      id: 5, 
      title: 'Tech Icon', 
      updated: 'Updated 4 days ago', 
      type: 'pink', 
      image: '⚙️',
      creator: 'Creator C',
      rating: 4.6,
      reviewCount: 203,
      description: '모던한 스타일',
      downloads: 3456,
      tags: ['모던', '3D', '기술'],
      setId: null,
      uploadDate: new Date('2024-01-08'),
      popularity: 1500
    },
    { 
      id: 6, 
      title: 'Retro Style', 
      updated: 'Updated 5 days ago', 
      type: 'pink', 
      image: '📻',
      creator: 'Designer D',
      rating: 4.9,
      reviewCount: 78,
      description: '우아한 느낌',
      downloads: 1890,
      tags: ['화려한', '레트로'],
      setId: null,
      uploadDate: new Date('2024-01-07'),
      popularity: 980
    },
  ];

  const openIconDetail = (icon) => {
    setSelectedIcon(icon);
    setUserRating(0);
    setComment('');
    setComments([
      { id: 1, user: 'User A', rating: 5, text: '정말 예쁜 아이콘이에요!', date: '2일 전' },
      { id: 2, user: 'User B', rating: 4, text: '마음에 듭니다', date: '5일 전' },
      { id: 3, user: 'User C', rating: 5, text: '완벽해요 ㅎㅎ', date: '1주일 전' },
    ]);
  };

  const closeIconDetail = () => {
    setSelectedIcon(null);
  };

  const handleRatingClick = (rating) => {
    setUserRating(rating);
  };

  const handleSubmitComment = () => {
    if (comment.trim() && userRating > 0) {
      const newComment = {
        id: comments.length + 1,
        user: 'You',
        rating: userRating,
        text: comment,
        date: '방금'
      };
      setComments([newComment, ...comments]);
      setComment('');
      setUserRating(0);
      alert('리뷰가 등록되었습니다!');
    } else {
      alert('별점과 코멘트를 모두 입력해주세요!');
    }
  };

  const getRelatedIcons = (currentIcon) => {
    return sampleIcons
      .filter(icon => icon.type === currentIcon.type && icon.id !== currentIcon.id)
      .slice(0, 6);
  };

  const getSetIcons = (currentIcon) => {
    if (!currentIcon.setId) return [];
    return sampleIcons.filter(icon => 
      icon.setId === currentIcon.setId && icon.id !== currentIcon.id
    );
  };

  const toggleFilterPopup = () => {
    setShowFilterPopup(!showFilterPopup);
  };

  const toggleTag = (tag) => {
    if (selectedTags.includes(tag)) {
      setSelectedTags(selectedTags.filter(t => t !== tag));
    } else {
      setSelectedTags([...selectedTags, tag]);
    }
  };

  const clearFilters = () => {
    setSelectedTags([]);
  };

  const getSortedIcons = (icons) => {
    const sorted = [...icons];
    switch(sortBy) {
      case 'popular':
        return sorted.sort((a, b) => b.popularity - a.popularity);
      case 'latest':
        return sorted.sort((a, b) => b.uploadDate - a.uploadDate);
      case 'oldest':
        return sorted.sort((a, b) => a.uploadDate - b.uploadDate);
      case 'rating':
        return sorted.sort((a, b) => b.rating - a.rating);
      case 'downloads':
        return sorted.sort((a, b) => b.downloads - a.downloads);
      default:
        return sorted;
    }
  };

  const filteredIcons = selectedTags.length > 0
    ? sampleIcons.filter(icon => 
        selectedTags.some(tag => icon.tags.includes(tag))
      )
    : sampleIcons;

  const sortedAndFilteredIcons = getSortedIcons(filteredIcons);
  const filteredTags = availableTags.filter(tag =>
    tag.toLowerCase().includes(filterSearch.toLowerCase())
  );
  const currentSortOption = sortOptions.find(opt => opt.value === sortBy);

  return (
    <div className="flex-1 flex flex-col overflow-hidden">
      {/* Header */}
      <div className="bg-white/80 backdrop-blur-md border-b border-slate-200/60 px-8 py-4 shadow-sm">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-4 flex-1">
            <button className="p-2 hover:bg-slate-100 rounded-lg transition">
              <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
              </svg>
            </button>
            
            <div className="flex-1 max-w-2xl">
              <div className="search-bar relative flex items-center bg-slate-100 rounded-xl px-4 py-2.5">
                <Search className="w-5 h-5 text-slate-400 mr-3" />
                <input 
                  type="text" 
                  placeholder="아이콘 검색..."
                  className="flex-1 bg-transparent border-none outline-none text-slate-700 placeholder-slate-400"
                />
              </div>
            </div>

            <button 
              onClick={toggleFilterPopup}
              className={`flex items-center gap-2 px-4 py-2.5 rounded-xl transition font-medium ${
                selectedTags.length > 0
                  ? 'bg-gradient-to-r from-pink-500 to-orange-500 text-white shadow-lg'
                  : 'hover:bg-slate-100 text-slate-700'
              }`}
            >
              <Filter className="w-4 h-4" />
              <span className="text-sm">필터</span>
              {selectedTags.length > 0 && (
                <span className="bg-white/30 px-2 py-0.5 rounded-full text-xs">
                  {selectedTags.length}
                </span>
              )}
            </button>
          </div>

          <div className="flex items-center gap-2 ml-4">
            <button className="p-2 hover:bg-slate-100 rounded-lg transition">
              <MoreVertical className="w-5 h-5 text-slate-600" />
            </button>
            <div className="w-px h-6 bg-slate-200 mx-2"></div>
            <div className="flex items-center gap-1 bg-slate-100 rounded-lg p-1">
              <button 
                onClick={() => setViewMode('list')}
                className={`p-2 rounded-md transition ${viewMode === 'list' ? 'bg-white shadow-sm' : 'hover:bg-slate-200'}`}
              >
                <List className="w-4 h-4 text-slate-700" />
              </button>
              <button 
                onClick={() => setViewMode('grid')}
                className={`p-2 rounded-md transition ${viewMode === 'grid' ? 'bg-white shadow-sm' : 'hover:bg-slate-200'}`}
              >
                <Grid3x3 className="w-4 h-4 text-slate-700" />
              </button>
              <button 
                onClick={() => setViewMode('calendar')}
                className={`p-2 rounded-md transition ${viewMode === 'calendar' ? 'bg-white shadow-sm' : 'hover:bg-slate-200'}`}
              >
                <Calendar className="w-4 h-4 text-slate-700" />
              </button>
            </div>
          </div>
        </div>
      </div>

      {/* Content */}
      <div className="flex-1 overflow-auto">
        <div className="p-8">
          <div className="mb-8">
            <div className="flex items-center justify-between mb-6">
              <h1 className="text-4xl font-bold gradient-text tracking-tight">아이콘</h1>
              
              <div className="flex items-center gap-3">
                {selectedTags.length > 0 && (
                  <button
                    onClick={clearFilters}
                    className="text-sm text-slate-600 hover:text-pink-500 transition"
                  >
                    필터 초기화
                  </button>
                )}

                <div className="relative">
                  <button
                    onClick={() => setShowSortDropdown(!showSortDropdown)}
                    className="flex items-center gap-2 px-4 py-2 bg-white border-2 border-slate-200 rounded-xl hover:border-pink-300 transition font-medium text-slate-700"
                  >
                    <currentSortOption.icon className="w-4 h-4" />
                    <span className="text-sm">{currentSortOption.label}</span>
                    <ChevronDown className={`w-4 h-4 transition-transform ${showSortDropdown ? 'rotate-180' : ''}`} />
                  </button>

                  {showSortDropdown && (
                    <>
                      <div 
                        className="fixed inset-0 z-10" 
                        onClick={() => setShowSortDropdown(false)}
                      />
                      <div className="absolute right-0 mt-2 w-48 bg-white rounded-xl shadow-2xl border border-slate-200 overflow-hidden z-20">
                        {sortOptions.map((option) => (
                          <button
                            key={option.value}
                            onClick={() => {
                              setSortBy(option.value);
                              setShowSortDropdown(false);
                            }}
                            className={`w-full flex items-center gap-3 px-4 py-3 hover:bg-slate-50 transition ${
                              sortBy === option.value ? 'bg-gradient-to-r from-pink-50 to-orange-50 text-pink-600' : 'text-slate-700'
                            }`}
                          >
                            <option.icon className="w-4 h-4" />
                            <span className="font-medium">{option.label}</span>
                            {sortBy === option.value && (
                              <span className="ml-auto text-pink-500">✓</span>
                            )}
                          </button>
                        ))}
                      </div>
                    </>
                  )}
                </div>
              </div>
            </div>

            {selectedTags.length > 0 && (
              <div className="flex items-center gap-2 flex-wrap mb-6">
                <span className="text-sm text-slate-600 font-medium">필터링:</span>
                {selectedTags.map(tag => (
                  <span
                    key={tag}
                    className="px-3 py-1 bg-gradient-to-r from-pink-100 to-orange-100 text-pink-700 rounded-full text-sm font-medium flex items-center gap-2"
                  >
                    {tag}
                    <X 
                      className="w-3 h-3 cursor-pointer hover:text-pink-900" 
                      onClick={() => toggleTag(tag)}
                    />
                  </span>
                ))}
              </div>
            )}
          </div>

          <div className="grid grid-cols-7 gap-6">
            {sortedAndFilteredIcons.map((icon) => (
              <div
                key={icon.id}
                onClick={() => openIconDetail(icon)}
                className="icon-card bg-white rounded-2xl p-4 cursor-pointer border border-slate-200/60 shadow-sm hover:border-pink-300 relative"
              >
                {icon.setId && (
                  <div className="absolute top-2 right-2 set-badge px-2 py-1 rounded-full flex items-center gap-1">
                    <Layers className="w-3 h-3 text-white" />
                    <span className="text-xs text-white font-medium">세트</span>
                  </div>
                )}
                
                <div className={`icon-image w-full aspect-square rounded-xl flex items-center justify-center text-5xl mb-3 ${
                  icon.type === 'pink' 
                    ? 'bg-gradient-to-br from-pink-100 to-pink-200' 
                    : icon.type === 'purple'
                    ? 'bg-gradient-to-br from-purple-100 to-indigo-200'
                    : icon.type === 'blue'
                    ? 'bg-gradient-to-br from-blue-100 to-cyan-200'
                    : 'bg-gradient-to-br from-slate-100 to-slate-200'
                }`}>
                  {icon.image}
                </div>
                <div className="relative z-10">
                  <h3 className="font-semibold text-slate-800 text-sm mb-1 truncate">{icon.title}</h3>
                  <p className="text-xs text-slate-500">{icon.updated}</p>
                </div>
              </div>
            ))}
          </div>

          {sortedAndFilteredIcons.length === 0 && (
            <div className="text-center py-20">
              <p className="text-slate-500 text-lg">선택한 필터에 맞는 아이콘이 없습니다.</p>
              <button
                onClick={clearFilters}
                className="mt-4 px-6 py-2 bg-gradient-to-r from-pink-500 to-orange-500 text-white rounded-xl hover:shadow-lg transition"
              >
                필터 초기화
              </button>
            </div>
          )}
        </div>
      </div>

      {/* Filter Popup */}
      {showFilterPopup && (
        <div className="fixed inset-0 z-40" onClick={toggleFilterPopup}>
          <div 
            className="absolute right-8 top-20 w-80 bg-white rounded-2xl shadow-2xl border border-slate-200 overflow-hidden"
            onClick={(e) => e.stopPropagation()}
          >
            <div className="bg-gradient-to-r from-pink-500 to-orange-500 p-4 text-white">
              <div className="flex items-center justify-between mb-3">
                <div className="flex items-center gap-2">
                  <Tag className="w-5 h-5" />
                  <h3 className="font-bold text-lg">태그</h3>
                </div>
                <button
                  onClick={toggleFilterPopup}
                  className="p-1 hover:bg-white/20 rounded-lg transition"
                >
                  <X className="w-5 h-5" />
                </button>
              </div>
              
              <div className="relative">
                <Search className="w-4 h-4 absolute left-3 top-1/2 transform -translate-y-1/2 text-white/70" />
                <input
                  type="text"
                  placeholder="검색"
                  value={filterSearch}
                  onChange={(e) => setFilterSearch(e.target.value)}
                  className="w-full pl-10 pr-4 py-2 bg-white/20 border border-white/30 rounded-lg text-white placeholder-white/70 outline-none focus:bg-white/30 transition"
                />
              </div>
            </div>

            <div className="max-h-96 overflow-y-auto p-4">
              <div className="space-y-2">
                {filteredTags.map(tag => (
                  <label
                    key={tag}
                    className="flex items-center gap-3 p-3 rounded-xl hover:bg-slate-50 cursor-pointer transition group"
                  >
                    <input
                      type="checkbox"
                      checked={selectedTags.includes(tag)}
                      onChange={() => toggleTag(tag)}
                      className="checkbox-custom"
                    />
                    <span className="flex-1 text-slate-700 font-medium group-hover:text-pink-600 transition">
                      {tag}
                    </span>
                  </label>
                ))}
              </div>

              {filteredTags.length === 0 && (
                <p className="text-center text-slate-500 py-8">
                  검색 결과가 없습니다.
                </p>
              )}
            </div>

            {selectedTags.length > 0 && (
              <div className="border-t border-slate-200 p-4">
                <button
                  onClick={clearFilters}
                  className="w-full py-2 text-slate-600 hover:text-pink-500 font-medium transition"
                >
                  모두 해제 ({selectedTags.length}개 선택됨)
                </button>
              </div>
            )}
          </div>
        </div>
      )}

      {/* Icon Detail Modal */}
      {selectedIcon && (
        <div className="modal-overlay fixed inset-0 bg-black/50 backdrop-blur-sm z-50 flex items-center justify-center p-4">
          <div className="modal-content bg-white rounded-3xl shadow-2xl max-w-2xl w-full max-h-[90vh] overflow-y-auto">
            <div className="sticky top-0 bg-white border-b border-slate-200 p-6 flex items-center justify-between rounded-t-3xl z-10">
              <div className="flex items-center gap-3">
                <div className="w-10 h-10 bg-gradient-to-br from-pink-500 to-orange-500 rounded-full flex items-center justify-center">
                  <User className="w-5 h-5 text-white" />
                </div>
                <div>
                  <h3 className="font-semibold text-slate-800">{selectedIcon.creator}</h3>
                  <p className="text-xs text-slate-500">제작자</p>
                </div>
              </div>
              <button
                onClick={closeIconDetail}
                className="p-2 hover:bg-slate-100 rounded-full transition"
              >
                <X className="w-5 h-5" />
              </button>
            </div>
            
            <div className="p-6">
              <div className={`w-full aspect-video rounded-2xl flex items-center justify-center text-9xl mb-6 relative ${
                selectedIcon.type === 'pink' 
                  ? 'bg-gradient-to-br from-pink-100 to-pink-200' 
                  : selectedIcon.type === 'purple'
                  ? 'bg-gradient-to-br from-purple-100 to-indigo-200'
                  : selectedIcon.type === 'blue'
                  ? 'bg-gradient-to-br from-blue-100 to-cyan-200'
                  : 'bg-gradient-to-br from-slate-100 to-slate-200'
              }`}>
                {selectedIcon.image}
                
                {selectedIcon.setId && (
                  <div className="absolute top-4 right-4 set-badge px-3 py-2 rounded-xl flex items-center gap-2 shadow-lg">
                    <Layers className="w-4 h-4 text-white" />
                    <span className="text-sm text-white font-semibold">{selectedIcon.setName}</span>
                  </div>
                )}
              </div>

              <div className="mb-6">
                <h2 className="text-3xl font-bold text-slate-800 mb-2">{selectedIcon.title}</h2>
                <p className="text-slate-600 mb-4">{selectedIcon.creator}</p>
                
                <div className="flex items-center gap-4 mb-4">
                  <div className="flex items-center gap-1">
                    <Star className="w-5 h-5 fill-yellow-400 text-yellow-400" />
                    <span className="font-bold text-lg">{selectedIcon.rating}</span>
                    <span className="text-slate-500 text-sm">({selectedIcon.reviewCount})</span>
                  </div>
                  <div className="text-slate-600 text-sm">
                    다운로드 {selectedIcon.downloads.toLocaleString()}회
                  </div>
                </div>

                <div className="flex gap-2 mb-4">
                  {selectedIcon.tags.map(tag => (
                    <span key={tag} className="px-3 py-1 bg-gradient-to-r from-pink-100 to-orange-100 text-pink-700 rounded-full text-xs font-medium">
                      {tag}
                    </span>
                  ))}
                </div>

                <p className="text-slate-600 mb-6">{selectedIcon.description}</p>

                <div className="flex gap-3">
                  <button className="flex-1 bg-gradient-to-r from-purple-600 to-indigo-600 text-white py-3 rounded-xl font-semibold hover:shadow-lg transition flex items-center justify-center gap-2">
                    <Download className="w-5 h-5" />
                    다운로드
                  </button>
                  <button className="px-6 py-3 border-2 border-purple-600 text-purple-600 rounded-xl font-semibold hover:bg-purple-50 transition">
                    <Share2 className="w-5 h-5" />
                  </button>
                  <button className="px-6 py-3 border-2 border-slate-300 text-slate-600 rounded-xl font-semibold hover:bg-slate-50 transition">
                    <ThumbsUp className="w-5 h-5" />
                  </button>
                </div>
              </div>

              {getSetIcons(selectedIcon).length > 0 && (
                <div className="border-t border-slate-200 pt-6 mb-6">
                  <div className="flex items-center gap-2 mb-4">
                    <Layers className="w-5 h-5 text-purple-600" />
                    <h3 className="font-bold text-lg">이 세트의 다른 아이콘</h3>
                    <span className="text-sm text-slate-500">({getSetIcons(selectedIcon).length}개)</span>
                  </div>
                  
                  <div className="grid grid-cols-4 gap-4">
                    {getSetIcons(selectedIcon).map((icon) => (
                      <div
                        key={icon.id}
                        onClick={() => openIconDetail(icon)}
                        className="bg-slate-50 rounded-xl p-3 cursor-pointer hover:bg-slate-100 transition border-2 border-transparent hover:border-purple-300"
                      >
                        <div className={`w-full aspect-square rounded-lg flex items-center justify-center text-4xl mb-2 ${
                          icon.type === 'pink' 
                            ? 'bg-gradient-to-br from-pink-100 to-pink-200' 
                            : icon.type === 'blue'
                            ? 'bg-gradient-to-br from-blue-100 to-cyan-200'
                            : 'bg-gradient-to-br from-slate-100 to-slate-200'
                        }`}>
                          {icon.image}
                        </div>
                        <p className="text-sm font-semibold text-slate-800 truncate">{icon.title}</p>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              <div className="border-t border-slate-200 pt-6 mb-6">
                <h3 className="font-bold text-lg mb-4">리뷰 작성</h3>
                
                <div className="flex gap-2 mb-4">
                  {[1, 2, 3, 4, 5].map((star) => (
                    <Star
                      key={star}
                      className={`w-8 h-8 cursor-pointer star-rating ${
                        star <= userRating
                          ? 'fill-yellow-400 text-yellow-400'
                          : 'text-slate-300'
                      }`}
                      onClick={() => handleRatingClick(star)}
                    />
                  ))}
                </div>

                <textarea
                  value={comment}
                  onChange={(e) => setComment(e.target.value)}
                  placeholder="이 아이콘에 대한 의견을 남겨주세요..."
                  className="w-full p-4 border-2 border-slate-200 rounded-xl resize-none focus:border-purple-500 focus:outline-none mb-3"
                  rows="3"
                />

                <button
                  onClick={handleSubmitComment}
                  className="w-full bg-gradient-to-r from-pink-500 to-orange-500 text-white py-3 rounded-xl font-semibold hover:shadow-lg transition"
                >
                  리뷰 등록
                </button>
              </div>

              <div className="border-t border-slate-200 pt-6 mb-6">
                <h3 className="font-bold text-lg mb-4">리뷰 ({comments.length})</h3>
                
                <div className="space-y-4">
                  {comments.map((cmt) => (
                    <div key={cmt.id} className="bg-slate-50 rounded-xl p-4">
                      <div className="flex items-start justify-between mb-2">
                        <div className="flex items-center gap-2">
                          <div className="w-8 h-8 bg-gradient-to-br from-pink-400 to-orange-400 rounded-full flex items-center justify-center text-white text-sm font-semibold">
                            {cmt.user[0]}
                          </div>
                          <span className="font-semibold text-slate-800">{cmt.user}</span>
                        </div>
                        <span className="text-xs text-slate-500">{cmt.date}</span>
                      </div>
                      <div className="flex gap-1 mb-2">
                        {[1, 2, 3, 4, 5].map((star) => (
                          <Star
                            key={star}
                            className={`w-4 h-4 ${
                              star <= cmt.rating
                                ? 'fill-yellow-400 text-yellow-400'
                                : 'text-slate-300'
                            }`}
                          />
                        ))}
                      </div>
                      <p className="text-slate-700">{cmt.text}</p>
                    </div>
                  ))}
                </div>
              </div>

              <div className="border-t border-slate-200 pt-6">
                <h3 className="font-bold text-lg mb-4">연관 아이콘</h3>
                
                <div className="grid grid-cols-3 gap-4">
                  {getRelatedIcons(selectedIcon).map((icon) => (
                    <div
                      key={icon.id}
                      onClick={() => openIconDetail(icon)}
                      className="bg-slate-50 rounded-xl p-3 cursor-pointer hover:bg-slate-100 transition"
                    >
                      <div className={`w-full aspect-square rounded-lg flex items-center justify-center text-4xl mb-2 ${
                        icon.type === 'pink' 
                          ? 'bg-gradient-to-br from-pink-100 to-pink-200' 
                          : 'bg-gradient-to-br from-slate-100 to-slate-200'
                      }`}>
                        {icon.image}
                      </div>
                      <p className="text-sm font-semibold text-slate-800 truncate">{icon.title}</p>
                      <div className="flex items-center gap-1 mt-1">
                        <Star className="w-3 h-3 fill-yellow-400 text-yellow-400" />
                        <span className="text-xs text-slate-600">{icon.rating}</span>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

// =============================================================================
// 보관함 페이지 컴포넌트
// =============================================================================
function ArchivePage() {
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedBoard, setSelectedBoard] = useState(null);
  
  const archiveBoards = [
    {
      id: 1,
      title: '거위밈',
      tags: ['밈', '거위', '재미'],
      imageCount: 8,
      preview: '🦆'
    },
    {
      id: 2,
      title: '고양이밈',
      tags: ['밈', '고양이', '재미'],
      imageCount: 5,
      preview: '🐱'
    },
    {
      id: 3,
      title: '디자인 아이콘',
      tags: ['디자인', 'UI', '아이콘'],
      imageCount: 12,
      preview: '🎨'
    },
    {
      id: 4,
      title: '프로젝트 리소스',
      tags: ['프로젝트', '리소스'],
      imageCount: 20,
      preview: '📁'
    }
  ];

  return (
    <div className="flex-1 overflow-y-auto bg-gradient-to-br from-slate-50 to-slate-100">
      <div className="p-8">
        <div className="mb-8">
          <h1 className="text-4xl font-bold gradient-text mb-4">보관함</h1>
          <p className="text-slate-600">저장한 아이콘을 관리하세요</p>
        </div>

        {/* Search */}
        <div className="mb-8">
          <div className="relative">
            <Search className="w-5 h-5 absolute left-4 top-1/2 transform -translate-y-1/2 text-slate-400" />
            <input
              type="text"
              placeholder="보관함에서 검색하기..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="w-full pl-12 pr-4 py-3 bg-white border-2 border-slate-200 rounded-xl focus:border-pink-500 focus:outline-none transition"
            />
          </div>
        </div>

        {/* Boards Grid */}
        <div className="grid grid-cols-4 gap-6">
          {archiveBoards.map(board => (
            <div
              key={board.id}
              onClick={() => setSelectedBoard(board)}
              className="bg-white rounded-2xl p-6 border-2 border-slate-200 hover:border-pink-300 cursor-pointer transition shadow-sm hover:shadow-xl"
            >
              <div className="w-full aspect-square bg-gradient-to-br from-pink-100 to-purple-100 rounded-xl flex items-center justify-center text-6xl mb-4">
                {board.preview}
              </div>
              <h3 className="font-bold text-slate-800 mb-2">{board.title}</h3>
              <div className="flex gap-2 mb-2">
                {board.tags.map(tag => (
                  <span key={tag} className="px-2 py-1 bg-slate-100 text-slate-600 rounded-lg text-xs">
                    {tag}
                  </span>
                ))}
              </div>
              <p className="text-sm text-slate-500">{board.imageCount}개 아이템</p>
            </div>
          ))}

          {/* Add New Board */}
          <div className="bg-white/50 border-2 border-dashed border-slate-300 rounded-2xl p-6 flex flex-col items-center justify-center cursor-pointer hover:border-pink-400 hover:bg-white transition">
            <Plus className="w-12 h-12 text-slate-400 mb-2" />
            <p className="text-slate-600 font-medium">새 보드 만들기</p>
          </div>
        </div>
      </div>
    </div>
  );
}
