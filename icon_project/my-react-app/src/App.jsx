import { useState } from 'react';
import IconExplorer from './IconExplorer';
import IconExplorerJ from './IconExplorer_J';
import IconExplorerSeo from './IconExplorer_seo';
import TestPage from './test-page';

function App() {
  // 현재 활성화된 페이지 ('home', 'explore', 'archive', 'settings')
  const [activePage, setActivePage] = useState('explore');

  // 페이지 전환 함수
  const handleNavigate = (page) => {
    setActivePage(page);
  };

  // 현재 페이지 렌더링
  if (activePage === 'home') {
    return <IconExplorerSeo onNavigate={handleNavigate} />;
  }
  
  if (activePage === 'explore') {
    return <IconExplorer onNavigate={handleNavigate} />;
  }
  
  if (activePage === 'archive') {
    return <IconExplorerJ onNavigate={handleNavigate} />;
  }

  if (activePage === 'settings') {
    return <TestPage onNavigate={handleNavigate} />;
  }

  // 기본값: 탐색 페이지
  return <IconExplorer onNavigate={handleNavigate} />;
}

export default App;