import { useState } from 'react';
import Explore from './Explore';
import Archive from './Archive';
import Home from './IncHome';
import TestPage from './TestPage';
import { Archive as ArchiveIcon, Home as HomeIcon } from 'lucide-react';

function App() {
  // 현재 활성화된 페이지 ('home', 'explore', 'archive', 'test', 'settings')
  const [activePage, setActivePage] = useState('explore');

  // 페이지 전환 함수
  const handleNavigate = (page) => {
    setActivePage(page);
  };

  // 현재 페이지 렌더링
  if (activePage === 'home') {
    return <Home onNavigate={handleNavigate} />;
  }
  
  if (activePage === 'explore') {
    return <Explore onNavigate={handleNavigate} />;
  }
  
  if (activePage === 'archive') {
    return <Archive onNavigate={handleNavigate} />;
  }

  if (activePage === 'test') {
    return <TestPage onNavigate={handleNavigate} />;
  }

  if (activePage === 'settings') {
    return <TestPage onNavigate={handleNavigate} />;
  }

  // 기본값: 탐색 페이지
  return <Explore onNavigate={handleNavigate} />;
}

export default App;
