import React, { useState, useEffect, useRef } from 'react';

export default function SearchModal({ isOpen, onClose, searchIndex, onSelectSymbol }) {
  const [query, setQuery] = useState('');
  const [selectedIndex, setSelectedIndex] = useState(0);
  const inputRef = useRef(null);

  useEffect(() => {
    if (isOpen) {
      setTimeout(() => inputRef.current?.focus(), 50);
      setQuery('');
      setSelectedIndex(0);
    }
  }, [isOpen]);

  const results = (searchIndex || []).filter(item => {
    if (!query) return true;
    const q = query.toLowerCase();
    return (
      item.name?.toLowerCase().includes(q) ||
      item.file?.toLowerCase().includes(q) ||
      item.doc?.toLowerCase().includes(q) ||
      item.sig?.toLowerCase().includes(q)
    );
  }).slice(0, 15);

  const handleKeyDown = (e) => {
    if (e.key === 'Escape') {
      onClose();
    } else if (e.key === 'ArrowDown') {
      e.preventDefault();
      setSelectedIndex(prev => Math.min(prev + 1, results.length - 1));
    } else if (e.key === 'ArrowUp') {
      e.preventDefault();
      setSelectedIndex(prev => Math.max(prev - 1, 0));
    } else if (e.key === 'Enter') {
      e.preventDefault();
      if (results[selectedIndex]) {
        onSelectSymbol(results[selectedIndex].id);
        onClose();
      }
    }
  };

  if (!isOpen) return null;

  return (
    <div
      onClick={onClose}
      style={{
        position: 'fixed',
        top: 0,
        left: 0,
        right: 0,
        bottom: 0,
        background: 'rgba(0, 0, 0, 0.7)',
        backdropFilter: 'blur(3px)',
        display: 'flex',
        alignItems: 'flex-start',
        justifyContent: 'center',
        paddingTop: '80px',
        zIndex: 9999
      }}
    >
      <div
        onClick={e => e.stopPropagation()}
        style={{
          width: '640px',
          maxWidth: '90vw',
          background: 'var(--bg-secondary)',
          border: '1px solid var(--border-color)',
          borderRadius: '12px',
          boxShadow: '0 20px 40px rgba(0,0,0,0.5)',
          overflow: 'hidden',
          display: 'flex',
          flexDirection: 'column'
        }}
      >
        {/* Input Field */}
        <div style={{
          display: 'flex',
          alignItems: 'center',
          padding: '12px 16px',
          borderBottom: '1px solid var(--border-color)',
          gap: '10px'
        }}>
          <span style={{ fontSize: '16px' }}>🔍</span>
          <input
            ref={inputRef}
            type="text"
            placeholder="Search classes, functions, files, or docstrings..."
            value={query}
            onChange={e => { setQuery(e.target.value); setSelectedIndex(0); }}
            onKeyDown={handleKeyDown}
            style={{
              flex: 1,
              background: 'transparent',
              border: 'none',
              outline: 'none',
              color: 'var(--text-primary)',
              fontSize: '15px',
              fontFamily: 'var(--font-sans)'
            }}
          />
          <kbd style={{
            fontSize: '11px',
            background: 'var(--bg-tertiary)',
            border: '1px solid var(--border-color)',
            padding: '2px 6px',
            borderRadius: '4px',
            color: 'var(--text-secondary)'
          }}>ESC to close</kbd>
        </div>

        {/* Results List */}
        <div style={{ maxHeight: '420px', overflowY: 'auto', padding: '8px' }}>
          {results.length === 0 ? (
            <div style={{ padding: '24px', textAlign: 'center', color: 'var(--text-muted)' }}>
              No symbols matched "{query}"
            </div>
          ) : (
            results.map((item, idx) => {
              const isSelected = idx === selectedIndex;
              return (
                <div
                  key={item.id}
                  onClick={() => { onSelectSymbol(item.id); onClose(); }}
                  onMouseEnter={() => setSelectedIndex(idx)}
                  style={{
                    padding: '8px 12px',
                    borderRadius: '6px',
                    background: isSelected ? 'var(--bg-tertiary)' : 'transparent',
                    borderLeft: isSelected ? '3px solid var(--accent-blue)' : '3px solid transparent',
                    cursor: 'pointer',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'space-between',
                    marginBottom: '2px'
                  }}
                >
                  <div style={{ overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                      <span style={{
                        fontWeight: 600,
                        fontSize: '13px',
                        color: 'var(--text-primary)',
                        fontFamily: 'var(--font-mono)'
                      }}>
                        {item.name}
                      </span>
                      <span style={{ fontSize: '11px', color: 'var(--text-secondary)' }}>
                        {item.file}:{item.line}
                      </span>
                    </div>
                    {item.doc && (
                      <div style={{
                        fontSize: '11px',
                        color: 'var(--text-muted)',
                        overflow: 'hidden',
                        textOverflow: 'ellipsis',
                        marginTop: '2px'
                      }}>
                        {item.doc}
                      </div>
                    )}
                  </div>

                  <span className={`badge badge-${item.type}`}>
                    {item.type}
                  </span>
                </div>
              );
            })
          )}
        </div>

        {/* Footer shortcuts */}
        <div style={{
          padding: '8px 16px',
          background: 'var(--bg-primary)',
          borderTop: '1px solid var(--border-color)',
          fontSize: '11px',
          color: 'var(--text-muted)',
          display: 'flex',
          justifyContent: 'space-between'
        }}>
          <span>Navigate with <kbd>↑</kbd> <kbd>↓</kbd></span>
          <span>Select with <kbd>Enter</kbd></span>
        </div>
      </div>
    </div>
  );
}
