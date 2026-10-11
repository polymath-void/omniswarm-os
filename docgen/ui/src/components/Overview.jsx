import React from 'react';

export default function Overview({ project, symbols, setActiveTab, onSelectSymbol }) {
  const stats = project?.stats || {};
  const symbolList = Object.values(symbols || {});

  const hotspots = symbolList
    .filter(s => s.complexity && s.complexity > 1)
    .sort((a, b) => (b.complexity || 0) - (a.complexity || 0))
    .slice(0, 6);

  return (
    <div style={{
      flex: 1,
      overflowY: 'auto',
      padding: '20px clamp(16px, 3vw, 32px)',
      background: 'var(--bg-primary)'
    }}>
      {/* Hero Welcome Banner */}
      <div style={{
        background: 'linear-gradient(135deg, rgba(59,130,246,0.08), rgba(168,85,247,0.05))',
        border: '1px solid var(--border-color)',
        borderRadius: '12px',
        padding: 'clamp(16px, 3vw, 24px)',
        marginBottom: '20px'
      }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '6px' }}>
          <span style={{ fontSize: '11px', textTransform: 'uppercase', color: 'var(--accent-blue)', fontWeight: 700, letterSpacing: '0.5px' }}>
            Living AST Manifest
          </span>
        </div>
        <h1 style={{ fontSize: 'clamp(20px, 4vw, 26px)', fontWeight: 800, color: 'var(--text-primary)', marginBottom: '6px' }}>
          {project?.name || 'Project'} System Architecture
        </h1>
        <p style={{ color: 'var(--text-secondary)', fontSize: '13px', maxWidth: '680px', lineHeight: 1.5 }}>
          Self-extracting, continuous AST semantic documentation engine with sub-second Merkle cache invalidation and WebAssembly sandbox.
        </p>
      </div>

      {/* Metrics Matrix (Responsive Auto-Fit) */}
      <div style={{
        display: 'grid',
        gridTemplateColumns: 'repeat(auto-fit, minmax(130px, 1fr))',
        gap: '12px',
        marginBottom: '24px'
      }}>
        {[
          { label: 'Files', value: stats.total_files || 0, color: 'var(--text-primary)' },
          { label: 'Lines of Code', value: (stats.total_loc || 0).toLocaleString(), color: 'var(--accent-blue)' },
          { label: 'Classes', value: stats.total_classes || 0, color: 'var(--accent-purple)' },
          { label: 'Functions', value: stats.total_functions || 0, color: 'var(--accent-green)' },
          { label: 'Avg Complexity', value: stats.avg_complexity || 1.0, color: stats.avg_complexity > 5 ? 'var(--accent-red)' : 'var(--accent-green)' }
        ].map((m, idx) => (
          <div
            key={idx}
            style={{
              background: 'var(--bg-secondary)',
              border: '1px solid var(--border-color)',
              borderRadius: '8px',
              padding: '12px 14px'
            }}
          >
            <div style={{ fontSize: '11px', color: 'var(--text-muted)', marginBottom: '4px' }}>{m.label}</div>
            <div style={{ fontSize: '18px', fontWeight: 700, color: m.color, fontFamily: 'var(--font-mono)' }}>
              {m.value}
            </div>
          </div>
        ))}
      </div>

      {/* Architectural Hotspots (High Complexity Nodes) */}
      <div style={{ marginBottom: '24px' }}>
        <h2 style={{ fontSize: '14px', fontWeight: 700, color: 'var(--text-primary)', marginBottom: '12px', display: 'flex', alignItems: 'center', gap: '6px' }}>
          <span>🔥</span> Logic Complexity Hotspots
        </h2>
        <div style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(auto-fit, minmax(260px, 1fr))',
          gap: '10px'
        }}>
          {hotspots.map((h, idx) => (
            <div
              key={idx}
              onClick={() => { onSelectSymbol(h.full_name || h.id); setActiveTab('symbols'); }}
              style={{
                background: 'var(--bg-secondary)',
                border: '1px solid var(--border-color)',
                borderRadius: '8px',
                padding: '10px 14px',
                cursor: 'pointer',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'space-between'
              }}
            >
              <div style={{ overflow: 'hidden', marginRight: '8px' }}>
                <div style={{ fontSize: '12px', fontWeight: 600, color: 'var(--text-primary)', fontFamily: 'var(--font-mono)', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                  {h.name}
                </div>
                <div style={{ fontSize: '10px', color: 'var(--text-muted)' }}>
                  {h.file}:{h.line || 1}
                </div>
              </div>
              <span style={{
                fontSize: '11px',
                fontFamily: 'var(--font-mono)',
                color: h.complexity > 6 ? 'var(--accent-red)' : 'var(--accent-yellow)',
                background: 'rgba(255,255,255,0.04)',
                padding: '2px 6px',
                borderRadius: '4px',
                border: '1px solid var(--border-color)',
                whiteSpace: 'nowrap'
              }}>
                Score: {h.complexity}
              </span>
            </div>
          ))}
        </div>
      </div>

      {/* Quick Action Navigation */}
      <div>
        <h2 style={{ fontSize: '14px', fontWeight: 700, color: 'var(--text-primary)', marginBottom: '12px' }}>
          Quick Workspaces
        </h2>
        <div style={{ display: 'flex', flexWrap: 'wrap', gap: '10px' }}>
          <button
            onClick={() => setActiveTab('symbols')}
            style={{
              padding: '8px 14px',
              borderRadius: '7px',
              background: 'var(--bg-secondary)',
              border: '1px solid var(--border-color)',
              color: 'var(--accent-blue)',
              fontWeight: 600,
              fontSize: '12px',
              cursor: 'pointer'
            }}
          >
            🔍 Symbol Matrix
          </button>
          <button
            onClick={() => setActiveTab('graph')}
            style={{
              padding: '8px 14px',
              borderRadius: '7px',
              background: 'var(--bg-secondary)',
              border: '1px solid var(--border-color)',
              color: 'var(--accent-purple)',
              fontWeight: 600,
              fontSize: '12px',
              cursor: 'pointer'
            }}
          >
            🕸️ Architecture Call Graph
          </button>
          <button
            onClick={() => setActiveTab('runner')}
            style={{
              padding: '8px 14px',
              borderRadius: '7px',
              background: 'var(--bg-secondary)',
              border: '1px solid var(--border-color)',
              color: 'var(--accent-green)',
              fontWeight: 600,
              fontSize: '12px',
              cursor: 'pointer'
            }}
          >
            ▶️ Python Sandbox
          </button>
        </div>
      </div>
    </div>
  );
}
