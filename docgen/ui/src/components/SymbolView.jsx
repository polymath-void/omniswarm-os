import React, { useState } from 'react';

export default function SymbolView({ symbol, onSelectSymbol }) {
  const [copied, setCopied] = useState(false);

  if (!symbol) {
    return (
      <div style={{
        flex: 1,
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        color: 'var(--text-muted)',
        flexDirection: 'column',
        gap: '8px'
      }}>
        <div style={{ fontSize: '32px' }}>📖</div>
        <div>Select a symbol from the sidebar or press <kbd>/</kbd> to search</div>
      </div>
    );
  }

  const handleCopy = (text) => {
    navigator.clipboard.writeText(text);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const complexityScore = symbol.complexity || 1;
  const complexityColor = complexityScore > 10 ? 'var(--accent-red)' : complexityScore > 5 ? 'var(--accent-yellow)' : 'var(--accent-green)';

  return (
    <div style={{
      flex: 1,
      overflowY: 'auto',
      padding: '24px 32px',
      background: 'var(--bg-primary)'
    }}>
      {/* Header Info */}
      <div style={{ display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between', marginBottom: '16px' }}>
        <div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '10px', marginBottom: '6px' }}>
            <span className={`badge badge-${symbol.type}`}>
              {symbol.type}
            </span>
            <span style={{ fontSize: '12px', color: 'var(--text-secondary)', fontFamily: 'var(--font-mono)' }}>
              {symbol.file}:{symbol.line || 1}
            </span>
            {symbol.complexity && (
              <span style={{
                fontSize: '11px',
                fontFamily: 'var(--font-mono)',
                color: complexityColor,
                background: 'rgba(255,255,255,0.05)',
                padding: '2px 6px',
                borderRadius: '4px',
                border: `1px solid ${complexityColor}`
              }}>
                Complexity: {symbol.complexity}
              </span>
            )}
          </div>
          <h1 style={{
            fontSize: '24px',
            fontWeight: 700,
            color: 'var(--text-primary)',
            fontFamily: 'var(--font-mono)'
          }}>
            {symbol.name}
          </h1>
        </div>

        <button
          onClick={() => handleCopy(symbol.signature || symbol.name)}
          style={{
            padding: '6px 12px',
            fontSize: '12px',
            background: 'var(--bg-secondary)',
            border: '1px solid var(--border-color)',
            borderRadius: '6px',
            color: 'var(--text-primary)',
            cursor: 'pointer',
            display: 'flex',
            alignItems: 'center',
            gap: '6px'
          }}
        >
          {copied ? '✅ Copied' : '📋 Copy Signature'}
        </button>
      </div>

      {/* Signature Card */}
      {symbol.signature && (
        <div style={{
          background: 'var(--bg-secondary)',
          border: '1px solid var(--border-color)',
          borderRadius: '8px',
          padding: '16px',
          marginBottom: '20px'
        }}>
          <div style={{ fontSize: '11px', color: 'var(--text-muted)', textTransform: 'uppercase', marginBottom: '6px', fontWeight: 600 }}>
            Signature
          </div>
          <pre style={{ margin: 0, padding: 0, background: 'transparent', border: 'none', color: 'var(--accent-blue)', fontSize: '13px' }}>
            <code>{symbol.signature}</code>
          </pre>
        </div>
      )}

      {/* Docstring */}
      {symbol.docstring && (
        <div style={{ marginBottom: '24px' }}>
          <h3 style={{ fontSize: '14px', fontWeight: 600, color: 'var(--text-secondary)', marginBottom: '8px', textTransform: 'uppercase' }}>
            Documentation
          </h3>
          <div style={{
            background: 'var(--bg-secondary)',
            border: '1px solid var(--border-color)',
            borderRadius: '8px',
            padding: '16px',
            fontSize: '13px',
            lineHeight: 1.6,
            color: 'var(--text-primary)',
            whiteSpace: 'pre-wrap'
          }}>
            {symbol.docstring}
          </div>
        </div>
      )}

      {/* Arguments Table */}
      {symbol.args && symbol.args.length > 0 && (
        <div style={{ marginBottom: '24px' }}>
          <h3 style={{ fontSize: '14px', fontWeight: 600, color: 'var(--text-secondary)', marginBottom: '8px', textTransform: 'uppercase' }}>
            Parameters ({symbol.args.length})
          </h3>
          <div style={{
            background: 'var(--bg-secondary)',
            border: '1px solid var(--border-color)',
            borderRadius: '8px',
            overflow: 'hidden'
          }}>
            <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '13px' }}>
              <thead>
                <tr style={{ background: 'var(--bg-tertiary)', borderBottom: '1px solid var(--border-color)', textAlign: 'left' }}>
                  <th style={{ padding: '8px 12px', color: 'var(--text-secondary)', fontWeight: 600 }}>Name</th>
                  <th style={{ padding: '8px 12px', color: 'var(--text-secondary)', fontWeight: 600 }}>Type</th>
                </tr>
              </thead>
              <tbody>
                {symbol.args.map((arg, idx) => (
                  <tr key={idx} style={{ borderBottom: '1px solid var(--border-color)' }}>
                    <td style={{ padding: '8px 12px', fontFamily: 'var(--font-mono)', color: 'var(--accent-purple)' }}>
                      {arg.name}
                    </td>
                    <td style={{ padding: '8px 12px', fontFamily: 'var(--font-mono)', color: 'var(--accent-green)' }}>
                      {arg.type}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Call Graph Connections: Calls & Callers */}
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '16px', marginBottom: '24px' }}>
        {/* Outgoing Calls */}
        <div style={{
          background: 'var(--bg-secondary)',
          border: '1px solid var(--border-color)',
          borderRadius: '8px',
          padding: '14px'
        }}>
          <h4 style={{ fontSize: '12px', color: 'var(--text-secondary)', textTransform: 'uppercase', marginBottom: '8px' }}>
            Calls Made ({symbol.calls?.length || 0})
          </h4>
          {(!symbol.calls || symbol.calls.length === 0) ? (
            <span style={{ fontSize: '12px', color: 'var(--text-muted)' }}>None detected</span>
          ) : (
            <div style={{ display: 'flex', flexWrap: 'wrap', gap: '6px' }}>
              {symbol.calls.map((call, idx) => (
                <span
                  key={idx}
                  onClick={() => onSelectSymbol(call)}
                  style={{
                    background: 'var(--bg-tertiary)',
                    border: '1px solid var(--border-color)',
                    padding: '2px 8px',
                    borderRadius: '4px',
                    fontSize: '11px',
                    fontFamily: 'var(--font-mono)',
                    color: 'var(--accent-blue)',
                    cursor: 'pointer'
                  }}
                >
                  {call}()
                </span>
              ))}
            </div>
          )}
        </div>

        {/* Incoming Callers */}
        <div style={{
          background: 'var(--bg-secondary)',
          border: '1px solid var(--border-color)',
          borderRadius: '8px',
          padding: '14px'
        }}>
          <h4 style={{ fontSize: '12px', color: 'var(--text-secondary)', textTransform: 'uppercase', marginBottom: '8px' }}>
            Referenced By ({symbol.callers?.length || 0})
          </h4>
          {(!symbol.callers || symbol.callers.length === 0) ? (
            <span style={{ fontSize: '12px', color: 'var(--text-muted)' }}>No callers recorded</span>
          ) : (
            <div style={{ display: 'flex', flexWrap: 'wrap', gap: '6px' }}>
              {symbol.callers.map((caller, idx) => (
                <span
                  key={idx}
                  onClick={() => onSelectSymbol(caller)}
                  style={{
                    background: 'var(--bg-tertiary)',
                    border: '1px solid var(--border-color)',
                    padding: '2px 8px',
                    borderRadius: '4px',
                    fontSize: '11px',
                    fontFamily: 'var(--font-mono)',
                    color: 'var(--accent-purple)',
                    cursor: 'pointer'
                  }}
                >
                  {caller.split(':').pop()}
                </span>
              ))}
            </div>
          )}
        </div>
      </div>

      {/* Source Code Block */}
      {symbol.source && (
        <div>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '8px' }}>
            <h3 style={{ fontSize: '14px', fontWeight: 600, color: 'var(--text-secondary)', textTransform: 'uppercase' }}>
              Source Implementation (Lines {symbol.line} - {symbol.end_line || symbol.line})
            </h3>
            <button
              onClick={() => handleCopy(symbol.source)}
              style={{
                fontSize: '11px',
                background: 'transparent',
                border: 'none',
                color: 'var(--accent-blue)',
                cursor: 'pointer'
              }}
            >
              Copy Source
            </button>
          </div>
          <pre style={{
            background: 'var(--bg-secondary)',
            border: '1px solid var(--border-color)',
            borderRadius: '8px',
            padding: '16px',
            fontSize: '12px',
            lineHeight: 1.5,
            maxHeight: '400px',
            overflowY: 'auto'
          }}>
            <code>{symbol.source}</code>
          </pre>
        </div>
      )}
    </div>
  );
}
