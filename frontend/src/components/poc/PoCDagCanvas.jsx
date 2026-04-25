import { useMemo } from 'react'

const NODE_W = 140
const NODE_H = 52
const H_GAP = 80
const V_GAP = 24

const STATUS_STYLE = {
  PENDING:    { border: '#1D4ED8', bg: '#1e3a8a22', text: '#93c5fd', label: 'PENDING' },
  REPRODUCED: { border: '#15803D', bg: '#14532d22', text: '#86efac', label: 'REPRODUCED' },
  PARTIAL:    { border: '#B45309', bg: '#78350f22', text: '#fcd34d', label: 'PARTIAL' },
  FAILED:     { border: '#DC2626', bg: '#7f1d1d22', text: '#fca5a5', label: 'FAILED' },
}
const THEORETICAL_STYLE = { border: '#374151', bg: '#11182722', text: '#6b7280' }

function computeLayout(nodes, edges) {
  if (!nodes.length) return {}
  const outgoing = {}
  nodes.forEach(n => { outgoing[n.id] = [] })
  edges.forEach(e => { if (outgoing[e.from]) outgoing[e.from].push(e.to) })

  const levels = {}
  const computing = new Set()
  function getLevel(id) {
    if (levels[id] !== undefined) return levels[id]
    if (computing.has(id)) return 0
    computing.add(id)
    const deps = outgoing[id] || []
    levels[id] = deps.length === 0 ? 0 : Math.max(...deps.map(getLevel)) + 1
    computing.delete(id)
    return levels[id]
  }
  nodes.forEach(n => getLevel(n.id))

  const byLevel = {}
  nodes.forEach(n => {
    const lv = levels[n.id] ?? 0
    if (!byLevel[lv]) byLevel[lv] = []
    byLevel[lv].push(n.id)
  })
  const maxNodesInLevel = Math.max(...Object.values(byLevel).map(l => l.length))
  const totalH = maxNodesInLevel * (NODE_H + V_GAP) - V_GAP

  const positions = {}
  Object.entries(byLevel).forEach(([level, ids]) => {
    const x = parseInt(level) * (NODE_W + H_GAP) + 20
    const colH = ids.length * (NODE_H + V_GAP) - V_GAP
    ids.forEach((id, i) => {
      const y = (totalH - colH) / 2 + i * (NODE_H + V_GAP)
      positions[id] = { x, y }
    })
  })
  return { positions, totalH }
}

export default function PoCDagCanvas({ nodes = [], edges = [], selectedClaimId, showOnlyTestable, onNodeClick }) {
  const visibleNodes = showOnlyTestable
    ? nodes.filter(n => n.testability === 'testable')
    : nodes

  const { positions, totalH } = useMemo(
    () => computeLayout(visibleNodes, edges),
    [visibleNodes, edges]
  )

  if (!visibleNodes.length) {
    return (
      <div className="flex-1 flex items-center justify-center">
        <div className="text-center text-[#4b5563]">
          <div className="text-4xl mb-3">⧖</div>
          <div className="text-sm tracking-widest">BUILDING CLAIM GRAPH...</div>
        </div>
      </div>
    )
  }

  const maxLevel = visibleNodes.length
    ? Math.max(...visibleNodes.map(n => {
        const p = positions[n.id]
        return p ? Math.floor(p.x / (NODE_W + H_GAP)) : 0
      }))
    : 0
  const svgW = (maxLevel + 1) * (NODE_W + H_GAP) + 40
  const svgH = (totalH ?? 300) + 60

  return (
    <div className="flex-1 overflow-auto" style={{ minHeight: 0 }}>
      <svg
        width={Math.max(svgW, 400)}
        height={Math.max(svgH, 300)}
        style={{ display: 'block', minWidth: '100%' }}
      >
        <defs>
          <marker id="arrow" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto">
            <path d="M0,0 L0,6 L8,3 z" fill="#374151" />
          </marker>
        </defs>

        {/* Edges */}
        {edges.map((e, i) => {
          const from = positions[e.from]
          const to = positions[e.to]
          if (!from || !to) return null
          const x1 = from.x + NODE_W / 2
          const y1 = from.y + NODE_H / 2
          const x2 = to.x + NODE_W / 2
          const y2 = to.y + NODE_H / 2
          const mx = (x1 + x2) / 2
          return (
            <path
              key={i}
              d={`M${x1},${y1} C${mx},${y1} ${mx},${y2} ${x2},${y2}`}
              stroke="#374151"
              strokeWidth="1.5"
              fill="none"
              markerEnd="url(#arrow)"
              opacity="0.6"
            />
          )
        })}

        {/* Nodes */}
        {visibleNodes.map(node => {
          const pos = positions[node.id]
          if (!pos) return null
          const isTheoretical = node.testability === 'theoretical'
          const st = isTheoretical ? THEORETICAL_STYLE : (STATUS_STYLE[node.reproduction_status] || STATUS_STYLE.PENDING)
          const isSelected = node.id === selectedClaimId

          return (
            <g
              key={node.id}
              transform={`translate(${pos.x},${pos.y})`}
              style={{ cursor: 'pointer' }}
              onClick={() => onNodeClick(node.id)}
            >
              {/* Glow for selected */}
              {isSelected && (
                <rect
                  x={-4} y={-4}
                  width={NODE_W + 8} height={NODE_H + 8}
                  rx="10"
                  fill="none"
                  stroke={st.border}
                  strokeWidth="3"
                  opacity="0.5"
                  style={{ filter: `drop-shadow(0 0 8px ${st.border})` }}
                />
              )}
              <rect
                width={NODE_W}
                height={NODE_H}
                rx="7"
                fill={st.bg}
                stroke={st.border}
                strokeWidth={isTheoretical ? 0 : 2}
                strokeDasharray={isTheoretical ? '5,4' : undefined}
                style={isSelected ? { filter: `drop-shadow(0 0 6px ${st.border}88)` } : undefined}
              />
              {/* Theoretical overlay */}
              {isTheoretical && (
                <rect width={NODE_W} height={NODE_H} rx="7" fill="none" stroke="#374151" strokeWidth="1.5" strokeDasharray="5,4" />
              )}
              {/* Claim ID */}
              <text
                x={NODE_W / 2}
                y={18}
                textAnchor="middle"
                fill={st.text}
                fontSize="11"
                fontFamily="monospace"
                fontWeight="600"
                opacity={isTheoretical ? 0.55 : 1}
              >
                {node.id.length > 16 ? node.id.slice(0, 15) + '…' : node.id}
              </text>
              {/* Status badge */}
              <text
                x={NODE_W / 2}
                y={36}
                textAnchor="middle"
                fill={isTheoretical ? '#6b7280' : st.border}
                fontSize="9"
                fontFamily="monospace"
                opacity={isTheoretical ? 0.45 : 0.9}
              >
                {isTheoretical ? 'THEORETICAL' : (node.reproduction_status || 'PENDING')}
              </text>
            </g>
          )
        })}
      </svg>
    </div>
  )
}
