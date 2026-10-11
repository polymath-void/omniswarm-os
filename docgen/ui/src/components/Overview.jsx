import React from 'react';

export default function Overview({ project, symbols, setActiveTab, onSelectSymbol }) {
  const stats = project?.stats || {};
  const symbolList = Object.values(symbols || {});

  // Find top complex functions (architectural hotspots)
  const hotspots = symbolList
    .filter(s => s.complexity && s.complexity > 1)
    .sort((a, b) => (b.complexity || 0) - (a.complexity || 0))
    .slice(0, 6);

  return (
    <div style={{
      flex: 1,
      overflowY: 'auto',
      padding: '32px',
      background: 'var(--bg-primary)'
    }}>
      {/* Hero Welcome Banner */}
      <div style={{
        background: 'linear-gradient(135deg, rgba(88,166,255,0.1), rgba(188,140,255,0.1))',
        border: '1px solid var(--border-color)',
        borderRadius: '12px',
        padding: '24px',
        marginBottom: '28px'
      }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '8px' }}>
          <span style={{ fontSize: '18px' }}>⚡</span>
          <span style={{ fontSize: '12px', textTransform: 'uppercase', color: 'var(--accent-blue)', fontWeight: 700, letterSpacing: '0.5px' }}>
            Living AST Architectural Manifest
          </span>
        </div>
        <h1 style={{ fontSize: '28px', fontWeight: 800, color: 'var(--text-primary)', marginBottom: '8px' }}>
          {project?.name || 'OmniSwarm'} System Documentation
        </h1>
        <p style={{ color: 'var(--text-secondary)', fontSize: '14px', maxWidth: '720px' }}>
          Self-extracting, continuous AST semantic documentation engine. Parses modules, classes, call-graphs,
          and type signatures with incremental Merkle caching and client-side Pyodide WebAssembly execution.
        </p>
      </div>

      {/* Metrics Matrix */}
      <div style={{
        display: 'grid',
        gridTemplateColumns: 'repeat(auto-fit, minmax(180px, 1fr))',
        gap: '16px',
        marginBottom: '32px'
      }}>
        {[
          { label: 'Total Files', value: stats.total_files || 0, icon: '📁', color: 'var(--accent-yellow)' },
          { label: 'Lines of Code', value: (stats.total_loc || 0).toLocaleString(), icon: '📝', color: 'var(--accent-blue)' },
          { label: 'Classes Parsed', value: stats.total_classes || 0, icon: '🏛️', color: 'var(--accent-purple)' },
          { label: 'Functions & Methods', value: stats.total_functions || 0, icon: '⚡', color: 'var(--accent-green)' },
          { label: 'Avg Complexity', value: stats.avg_complexity || 1.0, icon: '🧩', color: stats.avg_complexity > 5 ? 'var(--accent-red)' : 'var(--accent-green)' }
        ].map((m, idx) => (
          <div
            key={idx}
            style={{
              background: 'var(--bg-secondary)',
              border: '1px solid var(--border-color)',
              borderRadius: '8px',
              padding: '16px'
            }}
          >
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '8px' }}>
              <span style={{ fontSize: '12px', color: 'var(--text-muted)' }}>{m.label}</span>
              <span style={{ fontSize: '16px' }}>{m.icon}</span>
            </div>
            <div style={{ fontSize: '22px', fontWeight: 700, color: m.color, fontFamily: 'var(--font-mono)' }}>
              {m.value}
            </div>
          </div>
        ))}
      </div>

      {/* Architectural Hotspots (High Complexity Nodes) */}
      <div style={{ marginBottom: '32px' }}>
        <h2 style={{ fontSize: '16px', fontWeight: 700, color: 'var(--text-primary)', marginBottom: '14px', display: 'flex', alignItems: 'center', gap: '8px' }}>
          <span>🔥</span> Critical Logic Hotspots (Cyclomatic Complexity)
        </h2>
        <div style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(auto-fit, minmax(320px, 1fr))',
          gap: '12px'
        }}>
          {hotspots.map((h, idx) => (
            <div
              key={idx}
              onClick={() => { onSelectSymbol(h.full_name || h.id); setActiveTab('symbols'); }}
              style={{
                background: 'var(--bg-secondary)',
                border: '1px solid var(--border-color)',
                borderRadius: '8px',
                padding: '12px 16px',
                cursor: 'pointer',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'space-between'
              }}
            >
              <div>
                <div style={{ fontSize: '13px', fontWeight: 600, color: 'var(--text-primary)', fontFamily: 'var(--font-mono)' }}>
                  {h.name}
                </div>
                <div style={{ fontSize: '11px', color: 'var(--text-muted)' }}>
                  {h.file}:{h.line || 1}
                </div>
              </div>
              <span style={{
                fontSize: '11px',
                fontFamily: 'var(--font-mono)',
                color: h.complexity > 10 ? 'var(--accent-red)' : 'var(--accent-yellow)',
                background: 'rgba(255,255,255,0.05)',
                padding: '2px 8px',
                borderRadius: '4px',
                border: '1px solid var(--border-color)'
              }}>
                Score: {h.complexity}
              </span>
            </div>
          ))}
        </div>
      </div>

      {/* Quick Action Navigation */}
      <div>
        <h2 style={{ fontSize: '16px', fontWeight: 700, color: 'var(--text-primary)', marginBottom: '14px' }}>
          Quick Workspaces
        </h2>
        <div style={{ display: 'flex', gap: '12px' }}>
          <button
            onClick={() => setActiveTab('symbols')}
            style={{
              padding: '10px 18px',
              borderRadius: '8px',
              background: 'var(--bg-secondary)',
              border: '1px solid var(--border-color)',
              color: 'var(--accent-blue)',
              fontWeight: 600,
              fontSize: '13px',
              cursor: 'pointer'
            }}
          >
            🔍 Explore Symbol Matrix
          </button>
          <button
            onClick={() => setActiveTab('graph')}
            style={{
              padding: '10px 18px',
              borderRadius: '8px',
              background: 'var(--bg-secondary)',
              border: '1px solid var(--border-color)',
              color: 'var(--accent-purple)',
              fontWeight: 600,
              fontSize: '13px',
              cursor: 'pointer'
            }}
          >
            🕸️ View Architecture Call Graph
          </button>
          <button
            onClick={() => setActiveTab('runner')}
            style={{
              padding: '10px 18px',
              borderRadius: '8px',
              background: 'var(--bg-secondary)',
              border: '1px solid var(--border-color)',
              color: 'var(--accent-green)',
              fontWeight: 600,
              fontSize: '13px',
              cursor: 'pointer'
            }}
          >
            ▶️ Open In-Browser Python Sandbox
          </button>
        </div>
      </div>
    </div>
  );
}
