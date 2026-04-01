import { useState } from 'react';
import Explore from './Explore';
import Archive from './Archive';
import Home from './IncHome';
import TestPage from './TestPage';
// import IconChanger from './IconChanger';  ← 이 줄 삭제 또는 주석 처리
import ApplyWindow from './ApplyWindow';  // 이것만 있으면 됨!
import { Archive as ArchiveIcon, Home as HomeIcon } from 'lucide-react';

function App() {
  const [activePage, setActivePage] = useState('explore');

  const handleNavigate = (page) => {
    setActivePage(page);
  };

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

  // IconChanger 페이지 제거 또는 주석 처리
  // if (activePage === 'icon-changer') {
  //   return <IconChanger onNavigate={handleNavigate} />;
  // }

  // 적용창 (이것만 있으면 됨!)
  if (activePage === 'apply-window') {
    return <ApplyWindow onNavigate={handleNavigate} />;
  }

  if (activePage === 'settings') {
    return <TestPage onNavigate={handleNavigate} />;
  }

  return <Explore onNavigate={handleNavigate} />;
}

export default App;