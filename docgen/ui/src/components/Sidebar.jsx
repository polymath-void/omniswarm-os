import React, { useState, useMemo } from 'react';

export default function Sidebar({ symbols, activeSymbolId, onSelectSymbol }) {
  const [filterText, setFilterText] = useState('');
  const [typeFilter, setTypeFilter] = useState('all');

  const symbolList = useMemo(() => {
    return Object.values(symbols || {});
  }, [symbols]);

  const filtered = useMemo(() => {
    return symbolList.filter(sym => {
      if (typeFilter !== 'all' && sym.type !== typeFilter) return false;
      if (!filterText) return true;
      const q = filterText.toLowerCase();
      return (
        sym.name?.toLowerCase().includes(q) ||
        sym.file?.toLowerCase().includes(q) ||
        sym.type?.toLowerCase().includes(q)
      );
    });
  }, [symbolList, filterText, typeFilter]);

  const counts = useMemo(() => {
    const c = { all: symbolList.length, class: 0, function: 0, method: 0, module: 0 };
    symbolList.forEach(s => {
      if (c[s.type] !== undefined) c[s.type]++;
    });
    return c;
  }, [symbolList]);

  return (
    <aside style={{
      width: '280px',
      background: 'var(--bg-secondary)',
      borderRight: '1px solid var(--border-color)',
      display: 'flex',
      flexDirection: 'column',
      height: '100%',
      flexShrink: 0
    }}>
      {/* Search & Filter Header */}
      <div style={{ padding: '12px', borderBottom: '1px solid var(--border-color)' }}>
        <input
          type="text"
          placeholder="Filter tree..."
          value={filterText}
          onChange={e => setFilterText(e.target.value)}
          style={{
            width: '100%',
            padding: '6px 10px',
            background: 'var(--bg-primary)',
            border: '1px solid var(--border-color)',
            borderRadius: '6px',
            color: 'var(--text-primary)',
            fontSize: '12px',
            outline: 'none',
            fontFamily: 'var(--font-sans)'
          }}
        />

        {/* Type pills */}
        <div style={{ display: 'flex', gap: '4px', marginTop: '8px', overflowX: 'auto' }}>
          {[
            { id: 'all', label: `All (${counts.all})` },
            { id: 'class', label: `Classes (${counts.class})` },
            { id: 'function', label: `Funcs (${counts.function})` },
            { id: 'module', label: `Files (${counts.module})` }
          ].map(t => (
            <button
              key={t.id}
              onClick={() => setTypeFilter(t.id)}
              style={{
                padding: '3px 6px',
                fontSize: '11px',
                borderRadius: '4px',
                background: typeFilter === t.id ? 'var(--bg-tertiary)' : 'transparent',
                color: typeFilter === t.id ? 'var(--accent-blue)' : 'var(--text-secondary)',
                border: typeFilter === t.id ? '1px solid var(--accent-blue)' : '1px solid transparent',
                cursor: 'pointer',
                whiteSpace: 'nowrap'
              }}
            >
              {t.label}
            </button>
          ))}
        </div>
      </div>

      {/* Symbol List */}
      <div style={{ flex: 1, overflowY: 'auto', padding: '6px' }}>
        {filtered.length === 0 ? (
          <div style={{ padding: '20px', textAlign: 'center', color: 'var(--text-muted)', fontSize: '12px' }}>
            No matching symbols
          </div>
        ) : (
          filtered.map(sym => {
            const isSelected = (sym.full_name || sym.id) === activeSymbolId;
            return (
              <div
                key={sym.full_name || sym.id}
                onClick={() => onSelectSymbol(sym.full_name || sym.id)}
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'space-between',
                  padding: '6px 8px',
                  borderRadius: '6px',
                  cursor: 'pointer',
                  marginBottom: '2px',
                  background: isSelected ? 'var(--bg-tertiary)' : 'transparent',
                  borderLeft: isSelected ? '3px solid var(--accent-blue)' : '3px solid transparent'
                }}
              >
                <div style={{ overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap', marginRight: '6px' }}>
                  <div style={{
                    fontSize: '12px',
                    fontWeight: isSelected ? 600 : 400,
                    color: isSelected ? 'var(--text-primary)' : 'var(--text-primary)',
                    fontFamily: 'var(--font-mono)'
                  }}>
                    {sym.name}
                  </div>
                  <div style={{ fontSize: '10px', color: 'var(--text-muted)' }}>
                    {sym.file}:{sym.line || 1}
                  </div>
                </div>

                <span className={`badge badge-${sym.type}`}>
                  {sym.type}
                </span>
              </div>
            );
          })
        )}
      </div>
    </aside>
  );
}
