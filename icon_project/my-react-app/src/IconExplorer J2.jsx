import React, { useState, useEffect } from 'react';
import { Home, Compass, Archive, Search, X, ArrowLeft, Filter, Plus, Edit2, Check, Download, Share2, ThumbsUp, Star } from 'lucide-react';

// 샘플 보관함 아이템
const initialArchiveItems = [
  {
    id: 1,
    title: '거위밈',
    tags: ['밈', '거위', '재미'],
    images: [
      { 
        id: 1, 
        name: 'Meme2.png', 
        url: '/mnt/user-data/uploads/Meme2.png',
        creator: '밈 제작자',
        rating: 4.7,
        reviewCount: 89,
        downloads: 1234,
        description: '웃긴 거위 밈 이미지입니다. SNS에 공유하기 좋습니다.',
        uploadDate: '2024-01-15'
      },
      { 
        id: 2, 
        name: '거위사진1.jpg', 
        url: '/mnt/user-data/uploads/4d6d8e0a-e874-4293-9276-bc938c7f0d6d.jpg',
        creator: '거위 사진작가',
        rating: 4.5,
        reviewCount: 67,
        downloads: 890,
        description: '귀여운 거위의 모습을 담은 사진입니다.',
        uploadDate: '2024-01-14'
      },
      { 
        id: 3, 
        name: 'HOW_DARE_YOU.jpg', 
        url: '/mnt/user-data/uploads/HOW_DARE_YOU.jpg',
        creator: '밈 제작자',
        rating: 4.9,
        reviewCount: 156,
        downloads: 2341,
        description: '유명한 거위 밈 이미지입니다.',
        uploadDate: '2024-01-13'
      },
      { 
        id: 4, 
        name: 'Meme1.png', 
        url: '/mnt/user-data/uploads/Meme1.png',
        creator: '밈 제작자',
        rating: 4.6,
        reviewCount: 102,
        downloads: 1567,
        description: '다양하게 활용할 수 있는 거위 밈입니다.',
        uploadDate: '2024-01-12'
      }
    ]
  },
  {
    id: 2,
    title: '거위사진',
    tags: ['거위', '동물', '사진'],
    images: [
      { 
        id: 5, 
        name: '거위1.jpg', 
        url: '/mnt/user-data/uploads/5db6184d-c09c-42b8-9834-fc4e8216ab31.jpg',
        creator: '자연 사진작가',
        rating: 4.4,
        reviewCount: 45,
        downloads: 678,
        description: '자연 속 거위의 평화로운 모습입니다.',
        uploadDate: '2024-01-11'
      },
      { 
        id: 6, 
        name: '거위2.jpg', 
        url: '/mnt/user-data/uploads/56f108ed-5da9-42b0-b146-73d9da7d7090.jpg',
        creator: '자연 사진작가',
        rating: 4.3,
        reviewCount: 38,
        downloads: 543,
        description: '물가의 거위 사진입니다.',
        uploadDate: '2024-01-10'
      },
      { 
        id: 7, 
        name: '거위3.jpg', 
        url: '/mnt/user-data/uploads/812c6007-3117-4a82-9723-33dd65f2fd02.jpg',
        creator: '자연 사진작가',
        rating: 4.5,
        reviewCount: 52,
        downloads: 789,
        description: '햇살 아래 거위의 모습입니다.',
        uploadDate: '2024-01-09'
      },
      { 
        id: 8, 
        name: '거위4.jpg', 
        url: '/mnt/user-data/uploads/7066803c-fc13-4cef-8dd3-6d0885ce5e0b.jpg',
        creator: '자연 사진작가',
        rating: 4.6,
        reviewCount: 61,
        downloads: 912,
        description: '거위 무리의 아름다운 장면입니다.',
        uploadDate: '2024-01-08'
      }
    ]
  },
  {
    id: 3,
    title: '거위 gif',
    tags: ['거위', 'GIF', '애니메이션'],
    images: [
      { 
        id: 9, 
        name: 'GooseDance.gif', 
        url: '/mnt/user-data/uploads/GooseDance.gif',
        creator: 'GIF 애니메이터',
        rating: 4.8,
        reviewCount: 178,
        downloads: 3245,
        description: '춤추는 거위 GIF 애니메이션입니다.',
        uploadDate: '2024-01-16'
      },
      { 
        id: 10, 
        name: '거위사진5.jpg', 
        url: '/mnt/user-data/uploads/ff6154a8-37d6-421d-861d-b1f93a6723ce.jpg',
        creator: '거위 사진작가',
        rating: 4.4,
        reviewCount: 56,
        downloads: 723,
        description: '특별한 순간을 담은 거위 사진입니다.',
        uploadDate: '2024-01-07'
      }
    ]
  },
  {
    id: 4,
    title: '고양이밈',
    tags: ['밈', '고양이', '재미'],
    images: [
      { 
        id: 11, 
        name: 'Cat_Dancing.jpg', 
        url: '/mnt/user-data/uploads/Cat_Dancing_.jpg',
        creator: '펫 밈 제작자',
        rating: 4.7,
        reviewCount: 134,
        downloads: 2156,
        description: '춤추는 고양이 밈입니다.',
        uploadDate: '2024-01-15'
      },
      { 
        id: 12, 
        name: 'CAT_DDABONG.jpg', 
        url: '/mnt/user-data/uploads/CAT_DDABONG.jpg',
        creator: '펫 밈 제작자',
        rating: 4.9,
        reviewCount: 203,
        downloads: 3567,
        description: '따봉하는 고양이 밈입니다.',
        uploadDate: '2024-01-14'
      },
      { 
        id: 13, 
        name: 'DOCTOR_CAT.jpg', 
        url: '/mnt/user-data/uploads/DOCTOR_CAT.jpg',
        creator: '펫 밈 제작자',
        rating: 4.8,
        reviewCount: 189,
        downloads: 2987,
        description: '의사 고양이 밈입니다.',
        uploadDate: '2024-01-13'
      }
    ]
  },
  {
    id: 5,
    title: '동물',
    tags: ['동물', '고양이', '거위'],
    images: [
      { 
        id: 14, 
        name: '동물1.jpg', 
        url: '/mnt/user-data/uploads/812c6007-3117-4a82-9723-33dd65f2fd02.jpg',
        creator: '동물 사진작가',
        rating: 4.5,
        reviewCount: 72,
        downloads: 1123,
        description: '자연 속 동물의 모습입니다.',
        uploadDate: '2024-01-12'
      },
      { 
        id: 15, 
        name: '고양이1.jpg', 
        url: '/mnt/user-data/uploads/CAT_DDABONG.jpg',
        creator: '고양이 사진작가',
        rating: 4.6,
        reviewCount: 98,
        downloads: 1456,
        description: '귀여운 고양이 사진입니다.',
        uploadDate: '2024-01-11'
      },
      { 
        id: 16, 
        name: '동물2.jpg', 
        url: '/mnt/user-data/uploads/56f108ed-5da9-42b0-b146-73d9da7d7090.jpg',
        creator: '동물 사진작가',
        rating: 4.4,
        reviewCount: 64,
        downloads: 987,
        description: '평화로운 동물의 순간입니다.',
        uploadDate: '2024-01-10'
      },
      { 
        id: 17, 
        name: '고양이2.jpg', 
        url: '/mnt/user-data/uploads/DOCTOR_CAT.jpg',
        creator: '고양이 사진작가',
        rating: 4.7,
        reviewCount: 112,
        downloads: 1789,
        description: '사랑스러운 고양이의 표정입니다.',
        uploadDate: '2024-01-09'
      },
      { 
        id: 18, 
        name: '동물3.jpg', 
        url: '/mnt/user-data/uploads/5db6184d-c09c-42b8-9834-fc4e8216ab31.jpg',
        creator: '동물 사진작가',
        rating: 4.3,
        reviewCount: 51,
        downloads: 756,
        description: '자연 속 생명의 아름다움입니다.',
        uploadDate: '2024-01-08'
      },
      { 
        id: 19, 
        name: '동물4.jpg', 
        url: '/mnt/user-data/uploads/7066803c-fc13-4cef-8dd3-6d0885ce5e0b.jpg',
        creator: '동물 사진작가',
        rating: 4.5,
        reviewCount: 78,
        downloads: 1234,
        description: '동물들의 평화로운 시간입니다.',
        uploadDate: '2024-01-07'
      }
    ]
  },
  {
    id: 6,
    title: '재미있는 사진',
    tags: ['재미', '밈', '웃긴'],
    images: [
      { 
        id: 20, 
        name: 'Meme1.png', 
        url: '/mnt/user-data/uploads/Meme1.png',
        creator: '재미 제작자',
        rating: 4.6,
        reviewCount: 145,
        downloads: 2234,
        description: '웃음을 주는 밈 이미지입니다.',
        uploadDate: '2024-01-14'
      },
      { 
        id: 21, 
        name: 'HOW_DARE_YOU.jpg', 
        url: '/mnt/user-data/uploads/HOW_DARE_YOU.jpg',
        creator: '재미 제작자',
        rating: 4.8,
        reviewCount: 187,
        downloads: 2876,
        description: '바이럴 밈 이미지입니다.',
        uploadDate: '2024-01-13'
      },
      { 
        id: 22, 
        name: 'Cat_Dancing.jpg', 
        url: '/mnt/user-data/uploads/Cat_Dancing_.jpg',
        creator: '재미 제작자',
        rating: 4.7,
        reviewCount: 156,
        downloads: 2456,
        description: '즐거운 고양이 이미지입니다.',
        uploadDate: '2024-01-12'
      },
      { 
        id: 23, 
        name: 'GooseDance.gif', 
        url: '/mnt/user-data/uploads/GooseDance.gif',
        creator: '재미 제작자',
        rating: 4.9,
        reviewCount: 234,
        downloads: 3789,
        description: '신나는 거위 GIF입니다.',
        uploadDate: '2024-01-11'
      },
      { 
        id: 24, 
        name: 'Meme2.png', 
        url: '/mnt/user-data/uploads/Meme2.png',
        creator: '재미 제작자',
        rating: 4.5,
        reviewCount: 123,
        downloads: 1987,
        description: '유머러스한 밈 이미지입니다.',
        uploadDate: '2024-01-10'
      }
    ]
  },
  {
    id: 7,
    title: '배경화면',
    tags: ['배경', '월페이퍼', '디자인'],
    images: [
      { 
        id: 25, 
        name: '배경1.png', 
        url: '/mnt/user-data/uploads/1742454284.png',
        creator: '디자이너 A',
        rating: 4.8,
        reviewCount: 167,
        downloads: 2567,
        description: '아름다운 배경화면입니다.',
        uploadDate: '2024-01-15'
      },
      { 
        id: 26, 
        name: '배경2.jpg', 
        url: '/mnt/user-data/uploads/7066803c-fc13-4cef-8dd3-6d0885ce5e0b.jpg',
        creator: '디자이너 A',
        rating: 4.7,
        reviewCount: 143,
        downloads: 2234,
        description: '감각적인 월페이퍼입니다.',
        uploadDate: '2024-01-14'
      }
    ]
  },
  {
    id: 8,
    title: 'HONK',
    tags: ['거위', '밈', 'HONK'],
    images: [
      { 
        id: 27, 
        name: 'Meme2.png', 
        url: '/mnt/user-data/uploads/Meme2.png',
        creator: 'HONK 제작자',
        rating: 4.6,
        reviewCount: 134,
        downloads: 2123,
        description: 'HONK 밈 컬렉션입니다.',
        uploadDate: '2024-01-13'
      },
      { 
        id: 28, 
        name: 'honk1.jpg', 
        url: '/mnt/user-data/uploads/ff6154a8-37d6-421d-861d-b1f93a6723ce.jpg',
        creator: 'HONK 제작자',
        rating: 4.5,
        reviewCount: 98,
        downloads: 1654,
        description: '거위 HONK 이미지입니다.',
        uploadDate: '2024-01-12'
      },
      { 
        id: 29, 
        name: 'Meme1.png', 
        url: '/mnt/user-data/uploads/Meme1.png',
        creator: 'HONK 제작자',
        rating: 4.7,
        reviewCount: 156,
        downloads: 2345,
        description: '클래식 HONK 밈입니다.',
        uploadDate: '2024-01-11'
      },
      { 
        id: 30, 
        name: 'GooseDance.gif', 
        url: '/mnt/user-data/uploads/GooseDance.gif',
        creator: 'HONK 제작자',
        rating: 4.9,
        reviewCount: 223,
        downloads: 3456,
        description: 'HONK 애니메이션 GIF입니다.',
        uploadDate: '2024-01-10'
      }
    ]
  }
];

export default function ArchiveUI() {
  const [activeMenu, setActiveMenu] = useState('archive');
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedBoard, setSelectedBoard] = useState(null);
  const [archiveItems, setArchiveItems] = useState(initialArchiveItems);
  const [showFilterPanel, setShowFilterPanel] = useState(false);
  const [selectedTags, setSelectedTags] = useState([]);
  const [isEditingTitle, setIsEditingTitle] = useState(false);
  const [editedTitle, setEditedTitle] = useState('');
  const [isEditingTags, setIsEditingTags] = useState(false);
  const [editedTags, setEditedTags] = useState([]);
  const [newTag, setNewTag] = useState('');
  const [selectedImage, setSelectedImage] = useState(null);
  const [userRating, setUserRating] = useState(0);
  const [comment, setComment] = useState('');
  const [comments, setComments] = useState([]);

  // 모든 태그 추출
  const allTags = [...new Set(archiveItems.flatMap(item => item.tags))].sort();

  // 태그 필터 토글
  const toggleTagFilter = (tag) => {
    setSelectedTags(prev => 
      prev.includes(tag) 
        ? prev.filter(t => t !== tag)
        : [...prev, tag]
    );
  };

  // 검색 필터링 (보드 제목, 태그, 이미지 이름 포함)
  const filteredItems = archiveItems.map(item => {
    const matchesTitle = item.title.toLowerCase().includes(searchQuery.toLowerCase());
    const matchesTags = item.tags.some(tag => tag.toLowerCase().includes(searchQuery.toLowerCase()));
    const matchingImages = item.images.filter(img => 
      img.name.toLowerCase().includes(searchQuery.toLowerCase())
    );
    
    const hasMatch = matchesTitle || matchesTags || matchingImages.length > 0;
    const hasSelectedTag = selectedTags.length === 0 || selectedTags.some(tag => item.tags.includes(tag));
    
    return {
      ...item,
      hasMatch,
      matchingImages,
      matchesBoard: matchesTitle || matchesTags
    };
  }).filter(item => (!searchQuery || item.hasMatch) && item.hasSelectedTag !== false)
    .filter(item => selectedTags.length === 0 || selectedTags.some(tag => item.tags.includes(tag)));

  // 보드 제목 수정
  const handleSaveTitle = () => {
    if (editedTitle.trim()) {
      setArchiveItems(prev => prev.map(item => 
        item.id === selectedBoard.id ? { ...item, title: editedTitle } : item
      ));
      setSelectedBoard(prev => ({ ...prev, title: editedTitle }));
      setIsEditingTitle(false);
    }
  };

  // 태그 수정
  const handleSaveTags = () => {
    setArchiveItems(prev => prev.map(item => 
      item.id === selectedBoard.id ? { ...item, tags: editedTags } : item
    ));
    setSelectedBoard(prev => ({ ...prev, tags: editedTags }));
    setIsEditingTags(false);
  };

  // 태그 추가
  const handleAddTag = () => {
    if (newTag.trim() && !editedTags.includes(newTag.trim())) {
      setEditedTags([...editedTags, newTag.trim()]);
      setNewTag('');
    }
  };

  // 태그 제거
  const handleRemoveTag = (tagToRemove) => {
    setEditedTags(editedTags.filter(tag => tag !== tagToRemove));
  };

  // 리뷰 제출
  const handleSubmitComment = () => {
    if (userRating > 0 && comment.trim()) {
      const newComment = {
        id: Date.now(),
        user: '사용자',
        rating: userRating,
        text: comment,
        date: new Date().toLocaleDateString('ko-KR')
      };
      setComments([newComment, ...comments]);
      setUserRating(0);
      setComment('');
    }
  };

  // 별점 클릭
  const handleRatingClick = (rating) => {
    setUserRating(rating);
  };

  // 연관 이미지 찾기 (다른 보드에서도)
  const getRelatedImages = (currentImage) => {
    if (!currentImage || !selectedBoard) return [];
    
    const allImages = archiveItems.flatMap(board => 
      board.images.map(img => ({ ...img, boardTitle: board.title, boardTags: board.tags }))
    );
    
    // 현재 이미지 제외
    const otherImages = allImages.filter(img => img.id !== currentImage.id);
    
    // 같은 태그를 가진 이미지들
    const relatedByTags = otherImages.filter(img => 
      img.boardTags && img.boardTags.some(tag => selectedBoard.tags.includes(tag))
    );
    
    // 중복 제거 및 최대 6개
    const uniqueRelated = relatedByTags
      .filter((img, index, self) => self.findIndex(i => i.id === img.id) === index)
      .slice(0, 6);
    
    return uniqueRelated;
  };

  // ESC 키로 모달 닫기 & 모달 열렸을 때 배경 스크롤 막기
  useEffect(() => {
    const handleEscKey = (e) => {
      if (e.key === 'Escape') {
        if (selectedImage) setSelectedImage(null);
      }
    };
    
    if (selectedImage) {
      document.body.style.overflow = 'hidden';
      window.addEventListener('keydown', handleEscKey);
    } else {
      document.body.style.overflow = 'unset';
      // 모달 닫힐 때 리뷰 상태 초기화
      setUserRating(0);
      setComment('');
      setComments([]);
    }
    
    return () => {
      window.removeEventListener('keydown', handleEscKey);
      document.body.style.overflow = 'unset';
    };
  }, [selectedImage]);

  return (
    <div className="flex h-screen bg-gradient-to-br from-slate-50 to-slate-100 font-sans antialiased">
      {/* 왼쪽 사이드바 */}
      <aside className="w-72 bg-white/80 backdrop-blur-xl border-r border-slate-200/60 flex flex-col shadow-xl">
        {/* 헤더 */}
        <div className="p-6 border-b border-slate-100">
          <h1 className="text-2xl font-bold bg-gradient-to-r from-blue-600 to-purple-600 bg-clip-text text-transparent flex items-center gap-3">
            <div className="p-2 bg-gradient-to-br from-blue-500 to-purple-500 rounded-xl shadow-lg">
              <Archive className="w-6 h-6 text-white" />
            </div>
            보관함
          </h1>
        </div>

        {/* 탐색하기 섹션 */}
        <div className="p-5">
          <h3 className="text-xs font-bold text-slate-400 uppercase tracking-widest mb-4 px-2">
            탐색하기
          </h3>
          <nav className="space-y-2">
            {[
              { id: 'home', icon: Home, label: '홈', gradient: 'from-blue-500 to-cyan-500' },
              { id: 'explore', icon: Compass, label: '탐색', gradient: 'from-purple-500 to-pink-500' },
              { id: 'archive', icon: Archive, label: '보관함', gradient: 'from-orange-500 to-red-500' }
            ].map(item => (
              <button
                key={item.id}
                onClick={() => setActiveMenu(item.id)}
                className={`w-full flex items-center gap-3 px-4 py-3 rounded-xl transition-all duration-300 transform ${
                  activeMenu === item.id
                    ? 'bg-gradient-to-r ' + item.gradient + ' text-white shadow-lg scale-105 font-semibold'
                    : 'text-slate-600 hover:bg-slate-50 hover:scale-102 hover:shadow-md'
                }`}
              >
                <item.icon className="w-5 h-5" />
                <span>{item.label}</span>
              </button>
            ))}
          </nav>
        </div>

        {/* 통계 정보 */}
        <div className="p-5 mt-auto border-t border-slate-100">
          <div className="bg-gradient-to-br from-blue-50 to-purple-50 rounded-xl p-4 border border-blue-100">
            <div className="text-sm text-slate-600 mb-2">전체 보관함</div>
            <div className="text-3xl font-bold bg-gradient-to-r from-blue-600 to-purple-600 bg-clip-text text-transparent">
              {archiveItems.length}
            </div>
            <div className="text-xs text-slate-500 mt-1">컬렉션</div>
          </div>
        </div>
      </aside>

      {/* 메인 콘텐츠 영역 */}
      <main className="flex-1 overflow-y-auto">
        {!selectedBoard ? (
          /* 그리드 뷰 */
          <div className="max-w-[1600px] mx-auto px-10 py-8">
            {/* 상단 검색 영역 */}
            <div className="mb-8">
              <div className="flex gap-3 max-w-2xl relative">
                <div className="relative flex-1">
                  <Search className="absolute left-5 top-1/2 -translate-y-1/2 w-5 h-5 text-slate-400" />
                  <input
                    type="text"
                    placeholder="보관함에서 검색하기..."
                    value={searchQuery}
                    onChange={(e) => setSearchQuery(e.target.value)}
                    className="w-full pl-14 pr-6 py-4 bg-white/80 backdrop-blur-xl border-2 border-slate-200 rounded-2xl text-base focus:outline-none focus:border-blue-400 focus:ring-4 focus:ring-blue-100 transition-all duration-300 shadow-lg hover:shadow-xl placeholder:text-slate-400"
                  />
                </div>
                
                {/* 필터 버튼과 패널 컨테이너 */}
                <div className="relative">
                  <button
                    onClick={() => setShowFilterPanel(!showFilterPanel)}
                    className={`px-6 py-4 rounded-2xl font-semibold transition-all duration-300 shadow-lg hover:shadow-xl flex items-center gap-2 ${
                      showFilterPanel
                        ? 'bg-gradient-to-r from-purple-500 to-pink-500 text-white scale-105'
                        : selectedTags.length > 0
                        ? 'bg-gradient-to-r from-blue-500 to-purple-500 text-white'
                        : 'bg-white/80 backdrop-blur-xl text-slate-700 border-2 border-slate-200'
                    }`}
                  >
                    <Filter className="w-5 h-5" />
                    필터
                    {selectedTags.length > 0 && (
                      <span className="ml-1 px-2 py-0.5 bg-white/30 rounded-full text-xs font-bold">
                        {selectedTags.length}
                      </span>
                    )}
                  </button>

                  {/* 필터 패널 (오버레이) */}
                  {showFilterPanel && (
                    <div className="absolute right-0 top-full mt-2 w-[500px] p-6 bg-white/95 backdrop-blur-xl border-2 border-slate-200 rounded-2xl shadow-2xl z-50 animate-slideDown">
                      <div className="flex items-center justify-between mb-4">
                        <h3 className="font-bold text-slate-900">태그로 필터링</h3>
                        {selectedTags.length > 0 && (
                          <button
                            onClick={() => setSelectedTags([])}
                            className="text-sm text-blue-600 hover:text-blue-700 font-medium"
                          >
                            모두 지우기
                          </button>
                        )}
                      </div>
                      <div className="flex flex-wrap gap-2">
                        {allTags.map(tag => (
                          <button
                            key={tag}
                            onClick={() => toggleTagFilter(tag)}
                            className={`px-4 py-2 rounded-xl font-medium transition-all duration-200 ${
                              selectedTags.includes(tag)
                                ? 'bg-gradient-to-r from-blue-500 to-purple-500 text-white shadow-md scale-105'
                                : 'bg-slate-100 text-slate-700 hover:bg-slate-200'
                            }`}
                          >
                            #{tag}
                          </button>
                        ))}
                      </div>
                    </div>
                  )}
                </div>
              </div>

              {(searchQuery || selectedTags.length > 0) && (
                <div className="mt-4 text-sm text-slate-600">
                  <span className="font-semibold">{filteredItems.length}</span>개의 보드
                  {searchQuery && (
                    <>
                      , <span className="font-semibold">
                        {filteredItems.reduce((sum, item) => sum + item.matchingImages.length, 0)}
                      </span>개의 이미지가 검색되었습니다
                    </>
                  )}
                </div>
              )}
            </div>

            {/* 그리드 레이아웃 */}
            {filteredItems.length > 0 ? (
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-7">
                {filteredItems.map((item, index) => (
                  <div
                    key={item.id}
                    onClick={() => setSelectedBoard(item)}
                    className="group cursor-pointer"
                    style={{ 
                      animation: 'fadeInUp 0.6s ease-out backwards',
                      animationDelay: `${index * 80}ms` 
                    }}
                  >
                    <div className="bg-white rounded-2xl overflow-hidden shadow-lg hover:shadow-2xl transition-all duration-500 hover:-translate-y-2 border border-slate-100">
                      {/* 텍스트 그리드 */}
                      <div className="grid grid-cols-2 gap-1 aspect-square bg-gradient-to-br from-slate-50 to-slate-100 p-4">
                        {(searchQuery && item.matchingImages.length > 0 
                          ? [...item.matchingImages.slice(0, 4), ...item.images.filter(img => !item.matchingImages.includes(img))].slice(0, 4)
                          : item.images.slice(0, 4)
                        ).map((img, imgIndex) => {
                          const isMatching = searchQuery && item.matchingImages.some(m => m.id === img.id);
                          return (
                            <div 
                              key={imgIndex} 
                              className={`flex items-center justify-center rounded-xl p-3 shadow-sm group-hover:shadow-md transition-all duration-300 group-hover:scale-105 border ${
                                isMatching 
                                  ? 'bg-gradient-to-br from-blue-50 to-purple-50 border-blue-300 ring-2 ring-blue-400' 
                                  : 'bg-white border-slate-100'
                              }`}
                            >
                              <div className="text-center">
                                <div className={`text-3xl mb-2 ${isMatching ? 'animate-bounce' : ''}`}>
                                  {isMatching ? '✨' : '📄'}
                                </div>
                                <div className={`text-xs font-medium truncate ${
                                  isMatching ? 'text-blue-600 font-bold' : 'text-slate-600'
                                }`}>
                                  {img.name}
                                </div>
                              </div>
                            </div>
                          );
                        })}
                      </div>
                      
                      {/* 정보 */}
                      <div className="p-5 bg-gradient-to-br from-white to-slate-50">
                        <div className="flex items-start justify-between gap-2 mb-3">
                          <h3 className="font-bold text-slate-900 text-lg">{item.title}</h3>
                          {searchQuery && item.matchingImages.length > 0 && (
                            <span className="px-2 py-1 bg-blue-100 text-blue-700 text-xs font-bold rounded-full whitespace-nowrap">
                              {item.matchingImages.length}개 일치
                            </span>
                          )}
                        </div>
                        <div className="flex flex-wrap gap-1.5">
                          {item.tags.map((tag, idx) => (
                            <span
                              key={idx}
                              className="px-2.5 py-1 bg-gradient-to-r from-blue-50 to-purple-50 text-blue-600 text-xs font-semibold rounded-lg border border-blue-200"
                            >
                              #{tag}
                            </span>
                          ))}
                        </div>
                        <p className="text-sm text-slate-400 font-medium mt-2">
                          {item.images.length}개 항목
                        </p>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <div className="flex flex-col items-center justify-center py-20">
                <div className="w-20 h-20 bg-slate-100 rounded-full flex items-center justify-center mb-4">
                  <Search className="w-10 h-10 text-slate-400" />
                </div>
                <h3 className="text-xl font-semibold text-slate-700 mb-2">검색 결과가 없습니다</h3>
                <p className="text-slate-500">다른 키워드로 검색해보세요</p>
              </div>
            )}
          </div>
        ) : (
          /* 보드 상세 뷰 */
          <div className="h-full flex flex-col">
            {/* 상단 헤더 */}
            <div className="bg-white/80 backdrop-blur-xl border-b border-slate-200 px-8 py-6 shadow-lg">
              <div className="max-w-[1600px] mx-auto">
                <button
                  onClick={() => {
                    setSelectedBoard(null);
                    setIsEditingTitle(false);
                    setIsEditingTags(false);
                  }}
                  className="flex items-center gap-2 text-slate-600 hover:text-slate-900 mb-4 transition-colors group"
                >
                  <ArrowLeft className="w-5 h-5 group-hover:-translate-x-1 transition-transform" />
                  <span className="font-medium">돌아가기</span>
                </button>

                {/* 제목 편집 */}
                <div className="flex items-center gap-3 mb-4">
                  {isEditingTitle ? (
                    <>
                      <input
                        type="text"
                        value={editedTitle}
                        onChange={(e) => setEditedTitle(e.target.value)}
                        className="text-3xl font-bold bg-white border-2 border-blue-400 rounded-xl px-4 py-2 focus:outline-none focus:ring-4 focus:ring-blue-100"
                        autoFocus
                        onKeyPress={(e) => e.key === 'Enter' && handleSaveTitle()}
                      />
                      <button
                        onClick={handleSaveTitle}
                        className="p-2 bg-green-500 text-white rounded-xl hover:bg-green-600 transition-colors"
                      >
                        <Check className="w-5 h-5" />
                      </button>
                      <button
                        onClick={() => setIsEditingTitle(false)}
                        className="p-2 bg-slate-200 text-slate-700 rounded-xl hover:bg-slate-300 transition-colors"
                      >
                        <X className="w-5 h-5" />
                      </button>
                    </>
                  ) : (
                    <>
                      <h2 className="text-3xl font-bold bg-gradient-to-r from-blue-600 to-purple-600 bg-clip-text text-transparent">
                        {selectedBoard.title}
                      </h2>
                      <button
                        onClick={() => {
                          setIsEditingTitle(true);
                          setEditedTitle(selectedBoard.title);
                        }}
                        className="p-2 bg-slate-100 text-slate-700 rounded-xl hover:bg-slate-200 transition-colors"
                      >
                        <Edit2 className="w-4 h-4" />
                      </button>
                    </>
                  )}
                </div>

                {/* 태그 편집 */}
                <div className="flex items-center gap-2 flex-wrap">
                  {isEditingTags ? (
                    <div className="w-full">
                      <div className="flex flex-wrap gap-2 mb-3">
                        {editedTags.map((tag, idx) => (
                          <span
                            key={idx}
                            className="px-3 py-1.5 bg-gradient-to-r from-blue-500 to-purple-500 text-white text-sm font-semibold rounded-lg flex items-center gap-2"
                          >
                            #{tag}
                            <button
                              onClick={() => handleRemoveTag(tag)}
                              className="hover:bg-white/20 rounded-full p-0.5"
                            >
                              <X className="w-3 h-3" />
                            </button>
                          </span>
                        ))}
                      </div>
                      <div className="flex gap-2">
                        <input
                          type="text"
                          value={newTag}
                          onChange={(e) => setNewTag(e.target.value)}
                          placeholder="새 태그 추가..."
                          className="flex-1 px-4 py-2 bg-white border-2 border-slate-300 rounded-xl focus:outline-none focus:border-blue-400 focus:ring-4 focus:ring-blue-100"
                          onKeyPress={(e) => e.key === 'Enter' && handleAddTag()}
                        />
                        <button
                          onClick={handleAddTag}
                          className="px-4 py-2 bg-blue-500 text-white rounded-xl hover:bg-blue-600 transition-colors flex items-center gap-2"
                        >
                          <Plus className="w-4 h-4" />
                          추가
                        </button>
                        <button
                          onClick={handleSaveTags}
                          className="px-4 py-2 bg-green-500 text-white rounded-xl hover:bg-green-600 transition-colors flex items-center gap-2"
                        >
                          <Check className="w-4 h-4" />
                          저장
                        </button>
                        <button
                          onClick={() => setIsEditingTags(false)}
                          className="px-4 py-2 bg-slate-200 text-slate-700 rounded-xl hover:bg-slate-300 transition-colors"
                        >
                          취소
                        </button>
                      </div>
                    </div>
                  ) : (
                    <>
                      {selectedBoard.tags.map((tag, idx) => (
                        <span
                          key={idx}
                          className="px-3 py-1.5 bg-gradient-to-r from-blue-50 to-purple-50 text-blue-600 text-sm font-semibold rounded-lg border border-blue-200"
                        >
                          #{tag}
                        </span>
                      ))}
                      <button
                        onClick={() => {
                          setIsEditingTags(true);
                          setEditedTags([...selectedBoard.tags]);
                        }}
                        className="px-3 py-1.5 bg-slate-100 text-slate-700 rounded-lg hover:bg-slate-200 transition-colors flex items-center gap-1.5 text-sm font-medium"
                      >
                        <Edit2 className="w-3.5 h-3.5" />
                        태그 편집
                      </button>
                    </>
                  )}
                </div>

                <p className="text-slate-500 font-medium mt-3">{selectedBoard.images.length}개 항목</p>
              </div>
            </div>

            {/* 이미지 그리드 */}
            <div className="flex-1 overflow-y-auto px-8 py-8">
              <div className="max-w-[1600px] mx-auto">
                {searchQuery && selectedBoard.matchingImages && selectedBoard.matchingImages.length > 0 && (
                  <div className="mb-6 p-4 bg-blue-50 border border-blue-200 rounded-xl">
                    <p className="text-sm text-blue-700 font-medium">
                      🔍 <span className="font-bold">{selectedBoard.matchingImages.length}개</span>의 이미지가 
                      "<span className="font-bold">{searchQuery}</span>"와(과) 일치합니다
                    </p>
                  </div>
                )}
                <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 xl:grid-cols-5 gap-6">
                  {(searchQuery && selectedBoard.matchingImages && selectedBoard.matchingImages.length > 0
                    ? [
                        ...selectedBoard.matchingImages,
                        ...selectedBoard.images.filter(img => !selectedBoard.matchingImages.some(m => m.id === img.id))
                      ]
                    : selectedBoard.images
                  ).map((image, index) => {
                    const isMatching = searchQuery && selectedBoard.matchingImages && 
                                      selectedBoard.matchingImages.some(m => m.id === image.id);
                    return (
                      <div
                        key={image.id}
                        onClick={() => setSelectedImage({ ...image, boardTitle: selectedBoard.title, boardTags: selectedBoard.tags })}
                        className="group cursor-pointer"
                        style={{ 
                          animation: 'fadeInUp 0.5s ease-out backwards',
                          animationDelay: `${index * 50}ms` 
                        }}
                      >
                        <div className={`bg-white rounded-2xl overflow-hidden shadow-lg hover:shadow-2xl transition-all duration-500 hover:-translate-y-2 border ${
                          isMatching ? 'border-blue-400 ring-4 ring-blue-200' : 'border-slate-100'
                        }`}>
                          {/* 이미지 */}
                          <div className="aspect-square bg-slate-100 overflow-hidden relative">
                            <img
                              src={image.url}
                              alt={image.name}
                              className="w-full h-full object-cover group-hover:scale-110 transition-transform duration-700 ease-out"
                            />
                            {isMatching && (
                              <div className="absolute top-2 right-2 bg-blue-500 text-white px-2 py-1 rounded-full text-xs font-bold shadow-lg">
                                ✓ 일치
                              </div>
                            )}
                          </div>
                          
                          {/* 파일명 */}
                          <div className={`p-4 ${
                            isMatching ? 'bg-gradient-to-br from-blue-50 to-purple-50' : 'bg-gradient-to-br from-white to-slate-50'
                          }`}>
                            <p className={`text-sm font-medium truncate ${
                              isMatching ? 'text-blue-700 font-bold' : 'text-slate-700'
                            }`}>
                              {image.name}
                            </p>
                          </div>
                        </div>
                      </div>
                    );
                  })}
                </div>
              </div>
            </div>
          </div>
        )}
      </main>

      {/* 이미지 상세 모달 */}
      {selectedImage && (
        <div 
          className="fixed inset-0 bg-black/60 backdrop-blur-sm z-50 flex items-center justify-center p-4"
          onClick={(e) => {
            if (e.target === e.currentTarget) {
              setSelectedImage(null);
              setUserRating(0);
              setComment('');
              setComments([]);
            }
          }}
        >
          <div className="bg-white rounded-3xl max-w-4xl w-full max-h-[90vh] overflow-y-auto shadow-2xl animate-slideUp">
            {/* 모달 헤더 */}
            <div className="sticky top-0 bg-white/95 backdrop-blur-xl border-b border-slate-200 px-6 py-4 flex items-center justify-between z-10">
              <h2 className="text-xl font-bold text-slate-800">이미지 상세 정보</h2>
              <button
                onClick={() => {
                  setSelectedImage(null);
                  setUserRating(0);
                  setComment('');
                  setComments([]);
                }}
                className="p-2 hover:bg-slate-100 rounded-xl transition-colors"
              >
                <X className="w-6 h-6 text-slate-600" />
              </button>
            </div>

            <div className="p-6">
              {/* 이미지 */}
              <div className="w-full aspect-video rounded-2xl overflow-hidden bg-gradient-to-br from-slate-100 to-slate-200 mb-6 shadow-lg flex items-center justify-center">
                <img
                  src={selectedImage.url}
                  alt={selectedImage.name}
                  className="w-full h-full object-contain"
                />
              </div>

              {/* 이미지 정보 */}
              <div className="mb-6">
                <h3 className="text-3xl font-bold text-slate-800 mb-2">{selectedImage.name}</h3>
                <p className="text-slate-600 mb-4">{selectedImage.creator}</p>
                
                <div className="flex items-center gap-4 mb-4">
                  <div className="flex items-center gap-1">
                    <Star className="w-5 h-5 fill-yellow-400 text-yellow-400" />
                    <span className="font-bold text-lg">{selectedImage.rating}</span>
                    <span className="text-slate-500 text-sm">({selectedImage.reviewCount})</span>
                  </div>
                  <div className="text-slate-600 text-sm">
                    다운로드 {selectedImage.downloads.toLocaleString()}회
                  </div>
                </div>

                {/* 태그 */}
                <div className="flex flex-wrap gap-2 mb-4">
                  {selectedImage.boardTags.map((tag, idx) => (
                    <span
                      key={idx}
                      className="px-3 py-1 bg-gradient-to-r from-pink-100 to-orange-100 text-pink-700 rounded-full text-xs font-medium"
                    >
                      {tag}
                    </span>
                  ))}
                </div>

                <p className="text-slate-600 mb-6">{selectedImage.description}</p>

                {/* 액션 버튼 */}
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

              {/* 같은 보드의 다른 이미지들 */}
              {selectedBoard && selectedBoard.images.filter(img => img.id !== selectedImage.id).length > 0 && (
                <div className="border-t border-slate-200 pt-6 mb-6">
                  <h4 className="font-bold text-lg mb-4">
                    {selectedBoard.title}의 다른 이미지 ({selectedBoard.images.length - 1}개)
                  </h4>
                  <div className="grid grid-cols-4 gap-4">
                    {selectedBoard.images
                      .filter(img => img.id !== selectedImage.id)
                      .map((img) => (
                        <div
                          key={img.id}
                          onClick={() => {
                            setSelectedImage({ ...img, boardTitle: selectedBoard.title, boardTags: selectedBoard.tags });
                            setUserRating(0);
                            setComment('');
                          }}
                          className="bg-slate-50 rounded-xl p-3 cursor-pointer hover:bg-slate-100 transition border-2 border-transparent hover:border-purple-300"
                        >
                          <div className="w-full aspect-square rounded-lg overflow-hidden bg-slate-200 mb-2">
                            <img
                              src={img.url}
                              alt={img.name}
                              className="w-full h-full object-cover"
                            />
                          </div>
                          <p className="text-sm font-semibold text-slate-800 truncate">{img.name}</p>
                        </div>
                      ))}
                  </div>
                </div>
              )}

              {/* 리뷰 작성 */}
              <div className="border-t border-slate-200 pt-6 mb-6">
                <h3 className="font-bold text-lg mb-4">리뷰 작성</h3>
                
                <div className="flex gap-2 mb-4">
                  {[1, 2, 3, 4, 5].map((star) => (
                    <Star
                      key={star}
                      className={`w-8 h-8 cursor-pointer transition-all hover:scale-110 ${
                        star <= userRating
                          ? 'fill-yellow-400 text-yellow-400'
                          : 'text-slate-300 hover:text-yellow-200'
                      }`}
                      onClick={() => handleRatingClick(star)}
                    />
                  ))}
                </div>

                <textarea
                  value={comment}
                  onChange={(e) => setComment(e.target.value)}
                  placeholder="이 이미지에 대한 의견을 남겨주세요..."
                  className="w-full p-4 border-2 border-slate-200 rounded-xl resize-none focus:border-purple-500 focus:outline-none mb-3"
                  rows="3"
                />

                <button
                  onClick={handleSubmitComment}
                  disabled={!userRating || !comment.trim()}
                  className={`w-full py-3 rounded-xl font-semibold transition ${
                    userRating && comment.trim()
                      ? 'bg-gradient-to-r from-pink-500 to-orange-500 text-white hover:shadow-lg'
                      : 'bg-slate-200 text-slate-400 cursor-not-allowed'
                  }`}
                >
                  리뷰 등록
                </button>
              </div>

              {/* 리뷰 목록 */}
              <div className="border-t border-slate-200 pt-6 mb-6">
                <h3 className="font-bold text-lg mb-4">리뷰 ({comments.length})</h3>
                
                {comments.length > 0 ? (
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
                ) : (
                  <p className="text-slate-500 text-center py-8">아직 리뷰가 없습니다. 첫 리뷰를 작성해보세요!</p>
                )}
              </div>

              {/* 연관 이미지 */}
              <div className="border-t border-slate-200 pt-6">
                <h3 className="font-bold text-lg mb-4">연관 이미지</h3>
                
                {getRelatedImages(selectedImage).length > 0 ? (
                  <div className="grid grid-cols-3 gap-4">
                    {getRelatedImages(selectedImage).map((img) => (
                      <div
                        key={img.id}
                        onClick={() => {
                          // 해당 보드 찾기
                          const board = archiveItems.find(b => b.title === img.boardTitle);
                          setSelectedBoard(board);
                          setSelectedImage({ ...img, boardTitle: img.boardTitle, boardTags: img.boardTags });
                          setUserRating(0);
                          setComment('');
                        }}
                        className="bg-slate-50 rounded-xl p-3 cursor-pointer hover:bg-slate-100 transition"
                      >
                        <div className="w-full aspect-square rounded-lg overflow-hidden bg-slate-200 mb-2">
                          <img
                            src={img.url}
                            alt={img.name}
                            className="w-full h-full object-cover"
                          />
                        </div>
                        <p className="text-sm font-semibold text-slate-800 truncate">{img.name}</p>
                        <div className="flex items-center gap-1 mt-1">
                          <Star className="w-3 h-3 fill-yellow-400 text-yellow-400" />
                          <span className="text-xs text-slate-600">{img.rating}</span>
                        </div>
                      </div>
                    ))}
                  </div>
                ) : (
                  <p className="text-slate-500 text-center py-8">연관 이미지가 없습니다.</p>
                )}
              </div>
            </div>
          </div>
        </div>
      )}

      {/* 글로벌 스타일 */}
      <style>{`
        @import url('https://fonts.googleapis.com/css2?family=Noto+Sans+KR:wght@400;500;600;700;800&display=swap');
        
        * {
          font-family: 'Noto Sans KR', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
        }

        /* 스크롤바 스타일링 */
        ::-webkit-scrollbar {
          width: 10px;
          height: 10px;
        }
        
        ::-webkit-scrollbar-track {
          background: transparent;
        }
        
        ::-webkit-scrollbar-thumb {
          background: linear-gradient(180deg, #cbd5e1 0%, #94a3b8 100%);
          border-radius: 10px;
          border: 2px solid transparent;
          background-clip: padding-box;
        }
        
        ::-webkit-scrollbar-thumb:hover {
          background: linear-gradient(180deg, #94a3b8 0%, #64748b 100%);
          border-radius: 10px;
          border: 2px solid transparent;
          background-clip: padding-box;
        }

        /* 애니메이션 */
        @keyframes fadeInUp {
          from {
            opacity: 0;
            transform: translateY(30px);
          }
          to {
            opacity: 1;
            transform: translateY(0);
          }
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

        @keyframes slideUp {
          from {
            opacity: 0;
            transform: translateY(20px) scale(0.95);
          }
          to {
            opacity: 1;
            transform: translateY(0) scale(1);
          }
        }

        .animate-slideUp {
          animation: slideUp 0.3s ease-out;
        }

        @keyframes bounce {
          0%, 100% {
            transform: translateY(0);
          }
          50% {
            transform: translateY(-10px);
          }
        }

        .animate-bounce {
          animation: bounce 1s ease-in-out infinite;
        }

        /* 부드러운 포커스 효과 */
        input:focus {
          animation: pulse 2s ease-in-out infinite;
        }

        @keyframes pulse {
          0%, 100% {
            box-shadow: 0 0 0 0 rgba(59, 130, 246, 0);
          }
          50% {
            box-shadow: 0 0 0 8px rgba(59, 130, 246, 0.1);
          }
        }

        /* 그라데이션 배경 애니메이션 */
        @keyframes gradientShift {
          0% {
            background-position: 0% 50%;
          }
          50% {
            background-position: 100% 50%;
          }
          100% {
            background-position: 0% 50%;
          }
        }
      `}</style>
    </div>
  );
}
