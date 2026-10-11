import React, { useState, useEffect } from 'react';
import Header from './components/Header';
import Sidebar from './components/Sidebar';
import Overview from './components/Overview';
import SymbolView from './components/SymbolView';
import GraphView from './components/GraphView';
import CodeRunner from './components/CodeRunner';
import SearchModal from './components/SearchModal';

export default function App() {
  const [manifest, setManifest] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [activeTab, setActiveTab] = useState('overview');
  const [activeSymbolId, setActiveSymbolId] = useState(null);
  const [isSearchOpen, setIsSearchOpen] = useState(false);
  const [isSidebarOpen, setIsSidebarOpen] = useState(false);

  useEffect(() => {
    fetch('./docs_manifest.json')
      .then(res => {
        if (!res.ok) throw new Error(`HTTP error ${res.status}`);
        return res.json();
      })
      .then(data => {
        setManifest(data);
        setLoading(false);
        const firstSym = Object.values(data.symbols || {}).find(s => s.type === 'class' || s.type === 'function');
        if (firstSym) {
          setActiveSymbolId(firstSym.full_name || firstSym.id);
        }
      })
      .catch(err => {
        console.error('Failed to load docs_manifest.json:', err);
        setError('Could not load docs_manifest.json. Please run "docgen build" first.');
        setLoading(false);
      });
  }, []);

  // Global keyboard shortcuts
  useEffect(() => {
    const handleKeyDown = (e) => {
      if (e.key === '/' && !['INPUT', 'TEXTAREA'].includes(document.activeElement.tagName)) {
        e.preventDefault();
        setIsSearchOpen(true);
      }
    };
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, []);

  const handleSelectSymbol = (symId) => {
    let target = symId;
    if (manifest?.symbols && !manifest.symbols[symId]) {
      const match = Object.values(manifest.symbols).find(s => s.name === symId);
      if (match) target = match.full_name || match.id;
    }
    setActiveSymbolId(target);
    setActiveTab('symbols');
    setIsSidebarOpen(false);
  };

  if (loading) {
    return (
      <div style={{
        height: '100vh',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        background: 'var(--bg-primary)',
        color: 'var(--text-secondary)',
        fontFamily: 'var(--font-mono)',
        fontSize: '13px'
      }}>
        ⚡ Bootstrapping Living AST Manifest...
      </div>
    );
  }

  if (error) {
    return (
      <div style={{
        height: '100vh',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        background: 'var(--bg-primary)',
        color: 'var(--accent-red)',
        flexDirection: 'column',
        gap: '12px',
        padding: '20px',
        textAlign: 'center'
      }}>
        <div style={{ fontSize: '20px' }}>⚠️ {error}</div>
        <div style={{ fontSize: '13px', color: 'var(--text-secondary)' }}>
          Run: <code>docgen build</code>
        </div>
      </div>
    );
  }

  const activeSymbol = manifest?.symbols ? manifest.symbols[activeSymbolId] : null;

  return (
    <div style={{ height: '100vh', display: 'flex', flexDirection: 'column', overflow: 'hidden' }}>
      <Header
        project={manifest?.project}
        activeTab={activeTab}
        setActiveTab={setActiveTab}
        onOpenSearch={() => setIsSearchOpen(true)}
        onToggleSidebar={() => setIsSidebarOpen(prev => !prev)}
        isSidebarOpen={isSidebarOpen}
      />

      <div style={{ flex: 1, display: 'flex', overflow: 'hidden', position: 'relative' }}>
        {/* Sidebar visible when on Symbols or Graph, or toggled on mobile */}
        {(activeTab === 'symbols' || activeTab === 'graph' || isSidebarOpen) && (
          <Sidebar
            symbols={manifest?.symbols}
            activeSymbolId={activeSymbolId}
            onSelectSymbol={handleSelectSymbol}
            isOpen={isSidebarOpen}
            onClose={() => setIsSidebarOpen(false)}
          />
        )}

        {/* Main Workspace Tabs */}
        {activeTab === 'overview' && (
          <Overview
            project={manifest?.project}
            symbols={manifest?.symbols}
            setActiveTab={setActiveTab}
            onSelectSymbol={handleSelectSymbol}
          />
        )}

        {activeTab === 'symbols' && (
          <SymbolView
            symbol={activeSymbol}
            onSelectSymbol={handleSelectSymbol}
          />
        )}

        {activeTab === 'graph' && (
          <GraphView
            graph={manifest?.graph}
            onSelectSymbol={handleSelectSymbol}
          />
        )}

        {activeTab === 'runner' && (
          <CodeRunner
            symbol={activeSymbol}
          />
        )}
      </div>

      <SearchModal
        isOpen={isSearchOpen}
        onClose={() => setIsSearchOpen(false)}
        searchIndex={manifest?.search_index}
        onSelectSymbol={handleSelectSymbol}
      />
    </div>
  );
}
