import { useMemo } from 'react'
import { ReactFlow, Background, Controls, Handle, Position } from '@xyflow/react'
import '@xyflow/react/dist/style.css'
import dagre from 'dagre'

const ROLE_COLORS = {
  constructive: '#67E8F9',
  skeptical: '#f472b6',
  prior_work: '#b388ff',
  recent_or_future_work: '#a3e635',
}

const STATUS_COLORS = {
  planned: '#64748b',
  running: '#67E8F9',
  completed: '#22c55e',
  error: '#ef4444',
}

function statusColor(status) {
  return STATUS_COLORS[status] || STATUS_COLORS.planned
}

function personaColor(taste = {}) {
  const role = taste.diversity_roles?.[0]
  return ROLE_COLORS[role] || '#b388ff'
}

function CompactNode({ data }) {
  const active = data.selected?.kind === data.kind && data.selected?.id === data.id
  const color = data.kind === 'subagent' ? personaColor(data.taste) : statusColor(data.status)
  return (
    <>
      <Handle type="target" position={Position.Top} className="!h-2 !w-2 !border-0" style={{ background: color }} />
      <div
        className={`w-[230px] rounded-md border bg-[#131720] px-3 py-2 shadow-lg transition-all ${active ? 'scale-[1.03]' : ''}`}
        style={{ borderColor: active ? color : `${color}66`, boxShadow: active ? `0 0 0 2px ${color}33` : undefined }}
      >
        <div className="flex items-center gap-2">
          <span className="h-2 w-2 rounded-full" style={{ background: color, boxShadow: `0 0 10px ${color}` }} />
          <span className="min-w-0 flex-1 truncate font-mono text-[10px] uppercase text-white/45">{data.kind}</span>
          <span className="rounded bg-white/5 px-1.5 py-0.5 text-[10px] text-white/50">{data.status || 'ready'}</span>
        </div>
        <div className="mt-2 line-clamp-2 text-sm font-medium text-[#E4E7F0]">{data.title}</div>
        {data.subtitle && <div className="mt-1 truncate text-xs text-white/45">{data.subtitle}</div>}
        {data.kind === 'subagent' && (
          <div className="mt-2 grid grid-cols-2 gap-2 text-[10px] text-white/45">
            <Meter label="research" value={data.budget?.research_used || 0} max={data.budget?.research_max || data.maxToolCalls || 0} />
            <div className="truncate text-right">{data.lastTool || 'no tools yet'}</div>
          </div>
        )}
      </div>
      <Handle type="source" position={Position.Bottom} className="!h-2 !w-2 !border-0" style={{ background: color }} />
    </>
  )
}

function Meter({ label, value, max }) {
  const pct = max ? Math.min(100, Math.round((value / max) * 100)) : 0
  return (
    <div>
      <div className="mb-1 flex justify-between gap-2">
        <span>{label}</span>
        <span className="font-mono">{value}/{max || '-'}</span>
      </div>
      <div className="h-1 overflow-hidden rounded bg-white/10">
        <div className="h-full rounded bg-[#67E8F9]" style={{ width: `${pct}%` }} />
      </div>
    </div>
  )
}

const nodeTypes = { compact: CompactNode }

export default function AgentGraph({ snapshot, selected, onSelect }) {
  const { nodes, edges } = useMemo(() => buildGraph(snapshot, selected), [snapshot, selected])

  if (!nodes.length) {
    return <div className="flex h-full items-center justify-center text-sm text-white/45">No research graph yet.</div>
  }

  return (
    <ReactFlow
      nodes={nodes}
      edges={edges}
      nodeTypes={nodeTypes}
      onNodeClick={(_, node) => onSelect?.({ kind: node.data.kind, id: node.data.id })}
      fitView
      minZoom={0.25}
      className="research-flow"
    >
      <Background color="#2a3240" gap={18} />
      <Controls className="!border-white/10 !bg-[#131720] !fill-white" />
    </ReactFlow>
  )
}

function buildGraph(snapshot, selected) {
  const rfNodes = []
  const rfEdges = []
  const rootId = 'run-root'
  const meta = snapshot?.metadata || {}
  rfNodes.push({
    id: rootId,
    type: 'compact',
    data: {
      kind: 'run',
      id: meta.run_id || 'run',
      title: meta.run_id || 'Research run',
      subtitle: meta.research_objective || meta.arxiv_url || '',
      status: meta.status || 'running',
      selected,
    },
  })

  for (const investigator of snapshot?.investigators || []) {
    const invNodeId = `inv:${investigator.id}`
    rfNodes.push({
      id: invNodeId,
      type: 'compact',
      data: {
        kind: 'investigator',
        id: investigator.id,
        title: investigator.section_title || investigator.id,
        subtitle: `${investigator.subagent_ids?.length || 0} subagents`,
        status: investigator.status,
        selected,
      },
    })
    rfEdges.push(edge(rootId, invNodeId))
    for (const subagentId of investigator.subagent_ids || []) {
      const subagent = (snapshot.subagents || []).find((item) => item.id === subagentId)
      if (!subagent) continue
      const subNodeId = `sub:${subagent.id}`
      const toolEvents = subagent.tool_events || []
      const lastTool = [...toolEvents].reverse().find((event) => event.tool_name)?.tool_name
      rfNodes.push({
        id: subNodeId,
        type: 'compact',
        data: {
          kind: 'subagent',
          id: subagent.id,
          title: subagent.taste?.label || subagent.id,
          subtitle: subagent.taste?.archetype_label || subagent.section_title,
          status: subagent.status,
          taste: subagent.taste,
          budget: subagent.budget,
          maxToolCalls: subagent.max_tool_calls,
          lastTool,
          selected,
        },
      })
      rfEdges.push(edge(invNodeId, subNodeId))
      if (investigator.synthesis_md) rfEdges.push(edge(subNodeId, `synth:${investigator.id}`))
    }
    if (investigator.synthesis_md) {
      rfNodes.push({
        id: `synth:${investigator.id}`,
        type: 'compact',
        data: {
          kind: 'synthesis',
          id: investigator.id,
          title: 'Investigator synthesis',
          subtitle: investigator.section_title,
          status: 'completed',
          selected,
        },
      })
    }
  }

  if (snapshot?.shared?.cross_investigator_deep_dive?.content) {
    rfNodes.push({
      id: 'cross',
      type: 'compact',
      data: { kind: 'shared', id: 'cross_investigator_deep_dive', title: 'Cross-investigator deep dive', status: 'completed', selected },
    })
    for (const investigator of snapshot.investigators || []) {
      if (investigator.synthesis_md) rfEdges.push(edge(`synth:${investigator.id}`, 'cross'))
    }
  }

  for (const critique of snapshot?.critiques || []) {
    rfNodes.push({
      id: `critique:${critique.critic_id}`,
      type: 'compact',
      data: {
        kind: 'critique',
        id: critique.critic_id,
        title: critique.critic_id.replaceAll('_', ' '),
        subtitle: critique.lens,
        status: critique.status,
        selected,
      },
    })
    if (snapshot?.shared?.cross_investigator_deep_dive?.content) rfEdges.push(edge('cross', `critique:${critique.critic_id}`))
  }

  if (snapshot?.final_report?.available) {
    rfNodes.push({
      id: 'final',
      type: 'compact',
      data: { kind: 'final', id: 'final', title: 'Final report', subtitle: 'Rendered markdown', status: 'completed', selected },
    })
    for (const critique of snapshot.critiques || []) rfEdges.push(edge(`critique:${critique.critic_id}`, 'final'))
    if (!snapshot.critiques?.length && snapshot?.shared?.cross_investigator_deep_dive?.content) rfEdges.push(edge('cross', 'final'))
  }

  return layout(rfNodes, rfEdges)
}

function edge(source, target) {
  return { id: `${source}->${target}`, source, target, animated: false, style: { stroke: 'rgba(103,232,249,0.35)', strokeWidth: 2 } }
}

function layout(nodes, edges) {
  const graph = new dagre.graphlib.Graph()
  graph.setDefaultEdgeLabel(() => ({}))
  graph.setGraph({ rankdir: 'TB', nodesep: 60, ranksep: 90 })
  nodes.forEach((node) => graph.setNode(node.id, { width: 250, height: 125 }))
  edges.forEach((edge) => graph.setEdge(edge.source, edge.target))
  dagre.layout(graph)
  return {
    nodes: nodes.map((node) => {
      const position = graph.node(node.id)
      return { ...node, position: { x: position.x - 125, y: position.y - 62 } }
    }),
    edges,
  }
}
