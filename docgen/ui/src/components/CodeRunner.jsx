import React, { useState, useEffect } from 'react';

export default function CodeRunner({ symbol }) {
  const defaultSnippet = `# Test snippet for ${symbol?.name || 'DocGen'}
# Runs in-browser WebAssembly via Pyodide

print("⚡ Testing Live Execution...")
for i in range(1, 4):
    print(f"Step {i}: Verification OK")

result = {"status": "SUCCESS", "target": "${symbol?.name || 'DocGen'}"}
print("Final Output:", result)
`;

  const [code, setCode] = useState(defaultSnippet);
  const [output, setOutput] = useState('');
  const [isRunning, setIsRunning] = useState(false);

  useEffect(() => {
    if (symbol?.name) {
      setCode(`# Live test for ${symbol.name}\nprint("Testing ${symbol.name}...")\n`);
    }
  }, [symbol]);

  const runCode = async () => {
    setIsRunning(true);
    setOutput('🚀 Initializing execution environment...\n');

    try {
      if (!window.loadPyodide && !window.__pyodide_instance) {
        setOutput(prev => prev + '⏳ Loading Pyodide WebAssembly runtime from CDN...\n');
        const script = document.createElement('script');
        script.src = 'https://cdn.jsdelivr.net/pyodide/v0.25.0/full/pyodide.js';
        document.head.appendChild(script);

        await new Promise((resolve, reject) => {
          script.onload = resolve;
          script.onerror = () => reject(new Error('Failed to load Pyodide from CDN'));
        });
      }

      if (!window.__pyodide_instance) {
        setOutput(prev => prev + '⏳ Bootstrapping Pyodide Wasm engine...\n');
        window.__pyodide_instance = await window.loadPyodide({
          stdout: (text) => setOutput(prev => prev + text + '\n'),
          stderr: (text) => setOutput(prev => prev + '[ERR] ' + text + '\n')
        });
      }

      setOutput(prev => prev + '▶ Executing Python code:\n-----------------------------\n');
      const start = performance.now();
      const res = await window.__pyodide_instance.runPythonAsync(code);
      const elapsed = ((performance.now() - start) / 1000).toFixed(3);

      if (res !== undefined) {
        setOutput(prev => prev + `\n[Return Value]: ${res}\n`);
      }
      setOutput(prev => prev + `\n-----------------------------\n✅ Completed in ${elapsed}s`);
    } catch (err) {
      setOutput(prev => prev + `\n❌ Execution Error:\n${err.message}`);
    } finally {
      setIsRunning(false);
    }
  };

  const isMobile = typeof window !== 'undefined' && window.innerWidth < 768;

  return (
    <div style={{ flex: 1, display: 'flex', flexDirection: 'column', background: 'var(--bg-primary)', overflow: 'hidden' }}>
      {/* Top Header */}
      <div style={{
        padding: '10px 16px',
        borderBottom: '1px solid var(--border-color)',
        background: 'var(--bg-secondary)',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
        flexShrink: 0
      }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          <span style={{ fontSize: '13px', fontWeight: 600, color: 'var(--text-primary)' }}>
            🐍 WebAssembly Sandbox
          </span>
          <span style={{
            fontSize: '11px',
            color: 'var(--accent-green)',
            background: 'rgba(16, 185, 129, 0.1)',
            padding: '1px 6px',
            borderRadius: '4px',
            border: '1px solid rgba(16, 185, 129, 0.2)'
          }}>
            In-Browser
          </span>
        </div>

        <button
          onClick={runCode}
          disabled={isRunning}
          style={{
            padding: '5px 14px',
            background: isRunning ? 'var(--bg-tertiary)' : 'var(--accent-green)',
            color: '#fff',
            fontWeight: 600,
            fontSize: '12px',
            border: 'none',
            borderRadius: '6px',
            cursor: isRunning ? 'not-allowed' : 'pointer',
            display: 'flex',
            alignItems: 'center',
            gap: '6px'
          }}
        >
          {isRunning ? '⏳ Running...' : '▶ Run Code'}
        </button>
      </div>

      {/* Code Editor & Output (Responsive Split) */}
      <div style={{
        flex: 1,
        display: 'grid',
        gridTemplateColumns: isMobile ? '1fr' : '1fr 1fr',
        gridTemplateRows: isMobile ? '1fr 1fr' : '1fr',
        overflow: 'hidden'
      }}>
        {/* Editor */}
        <div style={{
          display: 'flex',
          flexDirection: 'column',
          borderRight: isMobile ? 'none' : '1px solid var(--border-color)',
          borderBottom: isMobile ? '1px solid var(--border-color)' : 'none'
        }}>
          <div style={{ padding: '6px 12px', background: 'var(--bg-tertiary)', fontSize: '11px', color: 'var(--text-secondary)' }}>
            Python Code Editor
          </div>
          <textarea
            value={code}
            onChange={e => setCode(e.target.value)}
            spellCheck="false"
            style={{
              flex: 1,
              background: 'var(--bg-primary)',
              border: 'none',
              padding: '14px',
              color: 'var(--text-primary)',
              fontFamily: 'var(--font-mono)',
              fontSize: '12px',
              lineHeight: 1.5,
              resize: 'none',
              outline: 'none'
            }}
          />
        </div>

        {/* Terminal Output */}
        <div style={{ display: 'flex', flexDirection: 'column', background: '#06090e' }}>
          <div style={{ padding: '6px 12px', background: 'var(--bg-tertiary)', fontSize: '11px', color: 'var(--text-secondary)' }}>
            Execution Console (stdout / stderr)
          </div>
          <pre style={{
            flex: 1,
            margin: 0,
            padding: '14px',
            background: 'transparent',
            border: 'none',
            color: '#34d399',
            fontSize: '12px',
            lineHeight: 1.5,
            whiteSpace: 'pre-wrap',
            overflowY: 'auto'
          }}>
            {output || 'Click "▶ Run Code" to execute Python natively in your browser...'}
          </pre>
        </div>
      </div>
    </div>
  );
}
