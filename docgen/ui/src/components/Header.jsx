import React from 'react';

export default function Header({ project, activeTab, setActiveTab, onOpenSearch, onToggleSidebar, isSidebarOpen }) {
  return (
    <header style={{
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'space-between',
      padding: '0 16px',
      height: '54px',
      background: 'var(--bg-secondary)',
      borderBottom: '1px solid var(--border-color)',
      userSelect: 'none',
      flexShrink: 0,
      gap: '12px',
      zIndex: 20
    }}>
      {/* Brand & Mobile Drawer Trigger */}
      <div style={{ display: 'flex', alignItems: 'center', gap: '10px', flexShrink: 0 }}>
        {/* Hamburger Toggle (for mobile & tablet) */}
        <button
          onClick={onToggleSidebar}
          aria-label="Toggle navigation drawer"
          style={{
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            width: '34px',
            height: '34px',
            background: isSidebarOpen ? 'var(--bg-tertiary)' : 'transparent',
            border: '1px solid var(--border-color)',
            borderRadius: '7px',
            color: 'var(--text-primary)',
            cursor: 'pointer',
            padding: 0
          }}
        >
          <svg style={{ width: '18px', height: '18px' }} fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M4 6h16M4 12h16M4 18h16" />
          </svg>
        </button>

        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          <div style={{
            background: 'linear-gradient(135deg, #3b82f6, #8b5cf6)',
            borderRadius: '7px',
            width: '26px',
            height: '26px',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            fontWeight: 700,
            color: '#fff',
            fontSize: '13px'
          }}>
            ⚡
          </div>
          <span style={{ fontWeight: 700, fontSize: '14px', letterSpacing: '-0.2px', color: 'var(--text-primary)' }}>
            DocGen
          </span>
          <span style={{
            fontSize: '11px',
            color: 'var(--text-muted)',
            fontFamily: 'var(--font-mono)',
            maxWidth: '120px',
            overflow: 'hidden',
            textOverflow: 'ellipsis',
            whiteSpace: 'nowrap'
          }}>
            {project?.name || 'Project'}
          </span>
        </div>
      </div>

      {/* Navigation Tabs (Scrollable on small viewports) */}
      <div
        className="no-scrollbar"
        style={{
          display: 'flex',
          gap: '4px',
          overflowX: 'auto',
          padding: '2px 0',
          flex: 1,
          justifyContent: 'center'
        }}
      >
        {[
          { id: 'overview', label: 'Overview' },
          { id: 'symbols', label: 'Symbols' },
          { id: 'graph', label: 'Graph' },
          { id: 'runner', label: 'Sandbox' }
        ].map(tab => {
          const isActive = activeTab === tab.id;
          return (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id)}
              style={{
                padding: '5px 12px',
                fontSize: '12px',
                fontWeight: isActive ? 600 : 500,
                background: isActive ? 'var(--bg-tertiary)' : 'transparent',
                color: isActive ? 'var(--text-primary)' : 'var(--text-secondary)',
                border: isActive ? '1px solid var(--border-color)' : '1px solid transparent',
                borderRadius: '6px',
                cursor: 'pointer',
                whiteSpace: 'nowrap',
                transition: 'all 0.15s ease'
              }}
            >
              {tab.label}
            </button>
          );
        })}
      </div>

      {/* Search Input Trigger */}
      <div style={{ display: 'flex', alignItems: 'center', gap: '8px', flexShrink: 0 }}>
        <button
          onClick={onOpenSearch}
          style={{
            display: 'flex',
            alignItems: 'center',
            gap: '8px',
            padding: '5px 10px',
            background: 'var(--bg-primary)',
            border: '1px solid var(--border-color)',
            borderRadius: '6px',
            color: 'var(--text-secondary)',
            fontSize: '12px',
            cursor: 'pointer'
          }}
        >
          <svg style={{ width: '13px', height: '13px' }} fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
          </svg>
          <span style={{ display: window.innerWidth < 640 ? 'none' : 'inline' }}>Search</span>
          <kbd style={{
            background: 'var(--bg-tertiary)',
            border: '1px solid var(--border-color)',
            borderRadius: '4px',
            padding: '1px 4px',
            fontSize: '10px',
            fontFamily: 'var(--font-mono)'
          }}>/</kbd>
        </button>
      </div>
    </header>
  );
}
