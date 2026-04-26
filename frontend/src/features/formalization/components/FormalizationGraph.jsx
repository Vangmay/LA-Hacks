import { useMemo } from 'react'
import { ReactFlow, Background, Controls, Handle, Position } from '@xyflow/react'
import dagre from 'dagre'
import '@xyflow/react/dist/style.css'

const STATUS_COLORS = {
  idle: '#64748b',
  queued: '#64748b',
  building_context: '#a78bfa',
  llm_thinking: '#67E8F9',
  axle_running: '#f59e0b',
  complete: '#22c55e',
  error: '#ef4444',
  skipped: '#94a3b8',
  fully_verified: '#22c55e',
  conditionally_verified: '#84cc16',
  formalized_only: '#facc15',
  disproved: '#ef4444',
  formalization_failed: '#fb7185',
  not_a_theorem: '#94a3b8',
  gave_up: '#f97316',
}

function statusColor(value) {
  return STATUS_COLORS[value] || STATUS_COLORS.queued
}

function FormalNode({ data }) {
  const active = data.selected?.kind === data.kind && data.selected?.id === data.id
  const color = statusColor(data.label || data.status)
  return (
    <>
      <Handle type="target" position={Position.Top} className="!h-2 !w-2 !border-0" style={{ background: color }} />
      <div
        className={`w-[245px] rounded-md border bg-[#131720] px-3 py-2 shadow-lg transition-all ${active ? 'scale-[1.03]' : ''}`}
        style={{ borderColor: active ? color : `${color}66`, boxShadow: active ? `0 0 0 2px ${color}33` : undefined }}
      >
        <div className="flex items-center gap-2">
          <span className="h-2 w-2 rounded-full" style={{ background: color, boxShadow: `0 0 10px ${color}` }} />
          <span className="min-w-0 flex-1 truncate font-mono text-[10px] uppercase text-white/45">{displayKind(data.kind)}</span>
          <span className="rounded bg-white/5 px-1.5 py-0.5 text-[10px] text-white/50">{formatStatus(data.label || data.status)}</span>
        </div>
        <div className="mt-2 line-clamp-2 text-sm font-medium text-[#E4E7F0]">{data.title}</div>
        {data.subtitle && <div className="mt-1 truncate text-xs text-white/45">{data.subtitle}</div>}
        {data.kind === 'atom' && (
          <div className="mt-2 grid grid-cols-3 gap-2 text-[10px] text-white/45">
            <Meter label="axle" value={data.axleCalls || 0} max={data.maxAxleCalls || 0} color="#f59e0b" />
            <Metric label="artifacts" value={data.artifacts || 0} />
            <Metric label="llm" value={data.llmCalls || 0} />
          </div>
        )}
        {data.kind === 'run' && (
          <div className="mt-2 grid grid-cols-3 gap-2 text-[10px] text-white/45">
            <Metric label="atoms" value={data.counts?.atoms || 0} />
            <Metric label="active" value={data.counts?.running_atoms || 0} />
            <Metric label="tools" value={data.counts?.tool_calls || 0} />
          </div>
        )}
      </div>
      <Handle type="source" position={Position.Bottom} className="!h-2 !w-2 !border-0" style={{ background: color }} />
    </>
  )
}

function Metric({ label, value }) {
  return (
    <div className="min-w-0">
      <div className="truncate">{label}</div>
      <div className="font-mono text-white/70">{value}</div>
    </div>
  )
}

function Meter({ label, value, max, color }) {
  const pct = max ? Math.min(100, Math.round((value / max) * 100)) : 0
  return (
    <div className="min-w-0">
      <div className="mb-1 flex justify-between gap-1">
        <span>{label}</span>
        <span className="font-mono">{value}/{max || '-'}</span>
      </div>
      <div className="h-1 overflow-hidden rounded bg-white/10">
        <div className="h-full rounded" style={{ width: `${pct}%`, background: color }} />
      </div>
    </div>
  )
}

const nodeTypes = { formal: FormalNode }

export default function FormalizationGraph({ state, selected, onSelect }) {
  const { nodes, edges } = useMemo(() => buildGraph(state, selected), [state, selected])

  if (!nodes.length) {
    return <div className="flex h-full items-center justify-center text-sm text-white/45">No formalization run yet.</div>
  }

  return (
    <ReactFlow
      nodes={nodes}
      edges={edges}
      nodeTypes={nodeTypes}
      onNodeClick={(_, node) => onSelect?.({ kind: node.data.kind, id: node.data.id })}
      fitView
      minZoom={0.25}
      className="formalization-flow"
    >
      <Background color="#2a3240" gap={18} />
      <Controls className="!border-white/10 !bg-[#131720] !fill-white" />
    </ReactFlow>
  )
}

function buildGraph(state, selected) {
  const nodes = []
  const edges = []
  const rootId = 'run-root'
  nodes.push({
    id: rootId,
    type: 'formal',
    data: {
      kind: 'run',
      id: state.runId || 'run',
      title: state.runId || 'Lean formalization run',
      subtitle: `${state.runtime?.model_name || 'model'} - ${state.runtime?.parallelism || '-'} atom workers`,
      status: state.status || 'idle',
      counts: state.counts || {},
      selected,
    },
  })

  for (const atomId of state.atomOrder || []) {
    const atom = state.atoms[atomId] || { atom_id: atomId }
    const nodeId = `atom:${atomId}`
    const axleCalls = (atom.tool_calls || []).filter((call) => String(call.tool_name || '').startsWith('axle_')).length
    nodes.push({
      id: nodeId,
      type: 'formal',
      data: {
        kind: 'atom',
        id: atomId,
        title: compactLabel(atom.text || atom.atom_id),
        subtitle: [atom.atom_type, atom.section_heading].filter(Boolean).join(' - '),
        status: atom.status,
        label: atom.label,
        artifacts: atom.artifacts?.length || 0,
        axleCalls,
        llmCalls: atom.llm_call_count || atom.thoughts?.length || 0,
        maxAxleCalls: atom.max_axle_calls || state.runtime?.max_axle_calls_per_atom,
        selected,
      },
    })
    edges.push(edge(rootId, nodeId, atom.label || atom.status))
  }

  return layout(nodes, edges)
}

function edge(source, target, status) {
  const color = statusColor(status)
  return {
    id: `${source}->${target}`,
    source,
    target,
    animated: ['building_context', 'llm_thinking', 'axle_running'].includes(status),
    style: { stroke: `${color}99`, strokeWidth: 2 },
  }
}

function layout(nodes, edges) {
  const graph = new dagre.graphlib.Graph()
  graph.setDefaultEdgeLabel(() => ({}))
  graph.setGraph({ rankdir: 'TB', nodesep: 55, ranksep: 85 })
  nodes.forEach((node) => graph.setNode(node.id, { width: 265, height: 130 }))
  edges.forEach((edge) => graph.setEdge(edge.source, edge.target))
  dagre.layout(graph)
  return {
    nodes: nodes.map((node) => {
      const position = graph.node(node.id)
      return { ...node, position: { x: position.x - 132, y: position.y - 65 } }
    }),
    edges,
  }
}

function displayKind(kind) {
  if (kind === 'atom') return 'atom agent'
  return String(kind || '').replaceAll('_', ' ')
}

function formatStatus(value = '') {
  return String(value || 'idle').replaceAll('_', ' ')
}

function compactLabel(value = '') {
  const text = String(value || '').replace(/\s+/g, ' ').trim()
  return text.length > 88 ? `${text.slice(0, 85)}...` : text || 'Atom'
}
