import React from 'react';

export default function Header({ project, activeTab, setActiveTab, onOpenSearch }) {
  const stats = project?.stats || {};

  return (
    <header style={{
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'space-between',
      padding: '0 20px',
      height: '56px',
      background: 'var(--bg-secondary)',
      borderBottom: '1px solid var(--border-color)',
      userSelect: 'none',
      flexShrink: 0
    }}>
      {/* Brand & Project Name */}
      <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
        <div style={{
          background: 'linear-gradient(135deg, #58a6ff, #bc8cff)',
          borderRadius: '8px',
          width: '28px',
          height: '28px',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          fontWeight: 'bold',
          color: '#fff',
          fontSize: '14px'
        }}>
          ⚡
        </div>
        <div>
          <span style={{ fontWeight: 700, fontSize: '15px', color: 'var(--text-primary)' }}>
            Dynamic DocGen
          </span>
          <span style={{
            marginLeft: '8px',
            fontSize: '12px',
            color: 'var(--text-secondary)',
            fontFamily: 'var(--font-mono)'
          }}>
            {project?.name || 'OmniSwarm'}
          </span>
        </div>
      </div>

      {/* Navigation Tabs */}
      <div style={{ display: 'flex', gap: '4px' }}>
        {[
          { id: 'overview', label: '📊 Overview' },
          { id: 'symbols', label: '🔍 Symbols' },
          { id: 'graph', label: '🕸️ Architecture Graph' },
          { id: 'runner', label: '▶️ Live Scratchpad' }
        ].map(tab => (
          <button
            key={tab.id}
            onClick={() => setActiveTab(tab.id)}
            style={{
              padding: '6px 14px',
              fontSize: '13px',
              fontWeight: 500,
              background: activeTab === tab.id ? 'var(--bg-tertiary)' : 'transparent',
              color: activeTab === tab.id ? 'var(--text-primary)' : 'var(--text-secondary)',
              border: activeTab === tab.id ? '1px solid var(--border-color)' : '1px solid transparent',
              borderRadius: '6px',
              cursor: 'pointer',
              transition: 'all 0.15s ease'
            }}
          >
            {tab.label}
          </button>
        ))}
      </div>

      {/* Search Input Trigger */}
      <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
        <button
          onClick={onOpenSearch}
          style={{
            display: 'flex',
            alignItems: 'center',
            gap: '8px',
            padding: '6px 12px',
            background: 'var(--bg-primary)',
            border: '1px solid var(--border-color)',
            borderRadius: '6px',
            color: 'var(--text-secondary)',
            fontSize: '12px',
            cursor: 'pointer',
            minWidth: '180px',
            justifyContent: 'space-between'
          }}
        >
          <span>Find symbol, file, function...</span>
          <kbd style={{
            background: 'var(--bg-tertiary)',
            border: '1px solid var(--border-color)',
            borderRadius: '4px',
            padding: '1px 5px',
            fontSize: '10px',
            fontFamily: 'var(--font-mono)'
          }}>/</kbd>
        </button>

        <span style={{
          fontSize: '11px',
          color: 'var(--accent-green)',
          fontFamily: 'var(--font-mono)',
          background: 'rgba(63, 185, 80, 0.1)',
          padding: '3px 8px',
          borderRadius: '4px',
          border: '1px solid rgba(63, 185, 80, 0.2)'
        }}>
          v1.0.0
        </span>
      </div>
    </header>
  );
}
