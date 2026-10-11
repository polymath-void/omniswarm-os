import React, { useState, useMemo } from 'react';

export default function GraphView({ graph, onSelectSymbol }) {
  const [relationFilter, setRelationFilter] = useState('all');
  const [hoveredNode, setHoveredNode] = useState(null);

  const nodes = graph?.nodes || [];
  const edges = graph?.edges || [];

  const filteredEdges = useMemo(() => {
    if (relationFilter === 'all') return edges.slice(0, 80);
    return edges.filter(e => e.relation === relationFilter).slice(0, 80);
  }, [edges, relationFilter]);

  // Layout node coordinates in a circular / layered lattice
  const nodePositions = useMemo(() => {
    const pos = {};
    const relevantNodeIds = new Set();
    filteredEdges.forEach(e => {
      relevantNodeIds.add(e.source);
      relevantNodeIds.add(e.target);
    });

    const activeNodes = nodes.filter(n => relevantNodeIds.has(n.id)).slice(0, 50);
    const count = activeNodes.length;
    const radius = Math.min(300, 40 + count * 8);
    const centerX = 400;
    const centerY = 350;

    activeNodes.forEach((node, i) => {
      const angle = (i / Math.max(count, 1)) * 2 * Math.PI;
      pos[node.id] = {
        x: centerX + radius * Math.cos(angle),
        y: centerY + radius * Math.sin(angle),
        ...node
      };
    });

    return pos;
  }, [nodes, filteredEdges]);

  return (
    <div style={{ flex: 1, display: 'flex', flexDirection: 'column', background: 'var(--bg-primary)', overflow: 'hidden' }}>
      {/* Controls Bar */}
      <div style={{
        padding: '12px 20px',
        borderBottom: '1px solid var(--border-color)',
        background: 'var(--bg-secondary)',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between'
      }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          <span style={{ fontSize: '13px', fontWeight: 600, color: 'var(--text-secondary)' }}>
            Relation Filter:
          </span>
          {['all', 'calls', 'contains', 'inherits'].map(rel => (
            <button
              key={rel}
              onClick={() => setRelationFilter(rel)}
              style={{
                padding: '4px 10px',
                fontSize: '11px',
                borderRadius: '4px',
                background: relationFilter === rel ? 'var(--bg-tertiary)' : 'transparent',
                color: relationFilter === rel ? 'var(--accent-blue)' : 'var(--text-secondary)',
                border: relationFilter === rel ? '1px solid var(--accent-blue)' : '1px solid var(--border-color)',
                cursor: 'pointer',
                textTransform: 'capitalize'
              }}
            >
              {rel}
            </button>
          ))}
        </div>

        <div style={{ fontSize: '12px', color: 'var(--text-muted)', fontFamily: 'var(--font-mono)' }}>
          Showing {Object.keys(nodePositions).length} nodes, {filteredEdges.length} edges
        </div>
      </div>

      {/* SVG Canvas */}
      <div style={{ flex: 1, position: 'relative', overflow: 'hidden', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
        <svg
          viewBox="0 0 800 700"
          style={{ width: '100%', height: '100%', cursor: 'grab' }}
        >
          <defs>
            <marker id="arrow" viewBox="0 0 10 10" refX="22" refY="5" markerWidth="6" markerHeight="6" orient="auto-start-reverse">
              <path d="M 0 0 L 10 5 L 0 10 z" fill="#8b949e" />
            </marker>
          </defs>

          {/* Render Edges */}
          {filteredEdges.map((edge, idx) => {
            const src = nodePositions[edge.source];
            const dst = nodePositions[edge.target];
            if (!src || !dst) return null;

            const isHighlighted = hoveredNode === edge.source || hoveredNode === edge.target;
            const strokeColor = edge.relation === 'calls' ? '#58a6ff' : edge.relation === 'inherits' ? '#bc8cff' : '#30363d';

            return (
              <line
                key={idx}
                x1={src.x}
                y1={src.y}
                x2={dst.x}
                y2={dst.y}
                stroke={isHighlighted ? '#58a6ff' : strokeColor}
                strokeWidth={isHighlighted ? 2 : 1}
                strokeDasharray={edge.relation === 'calls' ? '4 2' : 'none'}
                opacity={isHighlighted ? 1 : 0.6}
                markerEnd="url(#arrow)"
              />
            );
          })}

          {/* Render Nodes */}
          {Object.values(nodePositions).map(node => {
            const isHovered = hoveredNode === node.id;
            const nodeColor = node.type === 'class' ? '#bc8cff' : node.type === 'module' ? '#d29922' : '#58a6ff';

            return (
              <g
                key={node.id}
                transform={`translate(${node.x}, ${node.y})`}
                onClick={() => onSelectSymbol(node.id)}
                onMouseEnter={() => setHoveredNode(node.id)}
                onMouseLeave={() => setHoveredNode(null)}
                style={{ cursor: 'pointer' }}
              >
                <circle
                  r={isHovered ? 14 : 10}
                  fill={nodeColor}
                  stroke="#0d1117"
                  strokeWidth="2"
                  opacity="0.9"
                />
                <text
                  x={14}
                  y={4}
                  fill={isHovered ? '#fff' : '#c9d1d9'}
                  fontSize={isHovered ? '12px' : '10px'}
                  fontFamily="monospace"
                  fontWeight={isHovered ? 600 : 400}
                >
                  {node.name}
                </text>
              </g>
            );
          })}
        </svg>

        {/* Legend */}
        <div style={{
          position: 'absolute',
          bottom: '16px',
          left: '16px',
          background: 'var(--bg-secondary)',
          border: '1px solid var(--border-color)',
          borderRadius: '8px',
          padding: '10px 14px',
          fontSize: '11px',
          color: 'var(--text-secondary)',
          display: 'flex',
          flexDirection: 'column',
          gap: '6px'
        }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <span style={{ width: '8px', height: '8px', borderRadius: '50%', background: '#bc8cff' }} />
            <span>Class</span>
          </div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <span style={{ width: '8px', height: '8px', borderRadius: '50%', background: '#58a6ff' }} />
            <span>Function / Method</span>
          </div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <span style={{ width: '8px', height: '8px', borderRadius: '50%', background: '#d29922' }} />
            <span>Module</span>
          </div>
        </div>
      </div>
    </div>
  );
}
