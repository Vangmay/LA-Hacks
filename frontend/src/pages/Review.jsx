import { useEffect, useMemo, useReducer, useState } from 'react'
import { Link, useParams } from 'react-router-dom'
import { ReactFlow, Background, Controls, Handle, Position } from '@xyflow/react'
import '@xyflow/react/dist/style.css'
import ReactMarkdown from 'react-markdown'
import remarkBreaks from 'remark-breaks'
import dagre from 'dagre'
import { api } from '../api/client'
import FormalizationPanel from '../features/formalization/components/FormalizationPanel'

const STATUS_COLORS = {
  pending: '#6b7280',
  processing: '#3B82F6',
  checking: '#00eaff',
  no_objection: '#22c55e',
  supported: '#22c55e',
  contested: '#eab308',
  likely_flawed: '#f97316',
  refuted: '#ef4444',
  cascade_risk: '#a855f7',
}

function statusColor(status) {
  if (!status) return STATUS_COLORS.pending
  return STATUS_COLORS[status.toLowerCase()] || STATUS_COLORS.pending
}

const initialState = {
  status: null,
  dag: { nodes: [], edges: [] },
  atoms: {},
  checks: {},
  challenges: {},
  rebuttals: {},
  reportReady: false,
  buildStage: 'Loading DAG',
  recentAtoms: [],
}

function reducer(state, action) {
  if (action.type === 'INIT') {
    const atoms = {}
    const nodes = (action.payload.dag?.nodes || []).map(n => ({ ...n, id: n.id || n.atom_id }))
    const edges = (action.payload.dag?.edges || []).map(e => ({ ...e, id: e.id || e.edge_id, source: e.source || e.source_id, target: e.target || e.target_id }))
    for (const n of nodes) {
      atoms[n.id] = n
    }
    return {
      ...state,
      status: action.payload.status,
      dag: {
        nodes,
        edges,
        parsed_atoms: action.payload.dag?.parsed_atoms || nodes.length,
        total_atoms: action.payload.dag?.total_atoms || nodes.length,
        stage: action.payload.dag?.stage,
        extraction_batches_completed: action.payload.dag?.extraction_batches_completed,
        extraction_batches_total: action.payload.dag?.extraction_batches_total,
      },
      atoms,
      buildStage: action.payload.dag?.stage || action.payload.status?.review_stage || action.payload.status?.status || 'Loading DAG',
      recentAtoms: action.payload.dag?.recent_atoms || nodes.slice(-5),
    }
  }

  const { event_type, atom_id, payload } = action
  switch (event_type) {
    case 'source_fetch_complete':
      return { ...state, buildStage: 'Parsing TeX' }
    case 'parse_started':
      return { ...state, buildStage: 'Parsing TeX' }
    case 'parse_complete':
      return { ...state, buildStage: 'Extracting atoms' }
    case 'atom_extraction_started':
      return { ...state, buildStage: 'Extracting atoms' }
    case 'atom_created': {
      const newAtom = { ...payload, id: payload.id || payload.atom_id }
      const exists = Boolean(state.atoms[newAtom.id])
      const nextNodes = exists
        ? state.dag.nodes.map(n => n.id === newAtom.id ? { ...n, ...newAtom } : n)
        : [...state.dag.nodes, newAtom]
      return {
        ...state,
        buildStage: 'Extracting atoms',
        recentAtoms: [...state.recentAtoms, newAtom].slice(-5),
        atoms: { ...state.atoms, [newAtom.id]: newAtom },
        dag: {
          ...state.dag,
          nodes: nextNodes,
          parsed_atoms: nextNodes.length,
          total_atoms: Math.max(state.status?.total_atoms || 0, state.dag.total_atoms || 0, nextNodes.length),
        },
      }
    }
    case 'atom_extraction_complete':
      return {
        ...state,
        buildStage: 'Building dependency graph',
        status: { ...state.status, total_atoms: payload.total_atoms || state.status?.total_atoms },
        dag: { ...state.dag, total_atoms: payload.total_atoms || state.dag.total_atoms || state.dag.nodes.length },
      }
    case 'graph_build_started':
      return { ...state, buildStage: 'Building dependency graph' }
    case 'edge_created': {
      const newEdge = { ...payload, id: payload.id || payload.edge_id, source: payload.source || payload.source_id, target: payload.target || payload.target_id }
      const exists = state.dag.edges.some(e => (e.id && e.id === newEdge.id) || (e.source === newEdge.source && e.target === newEdge.target && e.edge_type === newEdge.edge_type))
      return {
        ...state,
        dag: { ...state.dag, edges: exists ? state.dag.edges : [...state.dag.edges, newEdge] },
      }
    }
    case 'graph_build_complete':
      return { ...state, buildStage: 'Reviewing atoms' }
    case 'check_started':
    case 'check_complete': {
      const atomId = atom_id || payload.atom_id
      if (!atomId) return state
      const existing = state.checks[atomId] || []
      const idx = existing.findIndex(c => c.check_id === payload.check_id)
      const nextChecks = [...existing]
      if (idx >= 0) {
        nextChecks[idx] = { ...nextChecks[idx], ...payload }
      } else {
        nextChecks.push(payload)
      }
      
      const atom = state.atoms[atomId]
      const updatedAtom = atom ? { ...atom, status: 'processing' } : null

      return {
        ...state,
        buildStage: 'Reviewing atoms',
        checks: { ...state.checks, [atomId]: nextChecks },
        ...(updatedAtom && {
          atoms: { ...state.atoms, [atomId]: updatedAtom },
          dag: { ...state.dag, nodes: state.dag.nodes.map(n => n.id === atomId ? updatedAtom : n) }
        })
      }
    }
    case 'challenge_issued': {
      const atomId = atom_id || payload.atom_id
      if (!atomId) return state
      const existing = state.challenges[atomId] || []
      const atom = state.atoms[atomId]
      const updatedAtom = atom ? { ...atom, status: 'processing' } : null

      return {
        ...state,
        buildStage: 'Reviewing atoms',
        challenges: { ...state.challenges, [atomId]: [...existing, payload] },
        ...(updatedAtom && {
          atoms: { ...state.atoms, [atomId]: updatedAtom },
          dag: { ...state.dag, nodes: state.dag.nodes.map(n => n.id === atomId ? updatedAtom : n) }
        })
      }
    }
    case 'rebuttal_issued': {
      const atomId = atom_id || payload.atom_id
      if (!atomId) return state
      const existing = state.rebuttals[atomId] || []
      const atom = state.atoms[atomId]
      const updatedAtom = atom ? { ...atom, status: 'processing' } : null

      return {
        ...state,
        buildStage: 'Reviewing atoms',
        rebuttals: { ...state.rebuttals, [atomId]: [...existing, payload] },
        ...(updatedAtom && {
          atoms: { ...state.atoms, [atomId]: updatedAtom },
          dag: { ...state.dag, nodes: state.dag.nodes.map(n => n.id === atomId ? updatedAtom : n) }
        })
      }
    }
    case 'verdict_emitted': {
      const atomId = atom_id || payload.atom_id
      if (!atomId) return state
      const atom = state.atoms[atomId]
      if (!atom) return state
      const updatedAtom = { ...atom, status: payload.label?.toLowerCase() }
      return {
        ...state,
        buildStage: 'Reviewing atoms',
        status: { ...state.status, completed_atoms: Math.min((state.status?.completed_atoms || 0) + 1, state.status?.total_atoms || state.dag.nodes.length) },
        atoms: { ...state.atoms, [atomId]: updatedAtom },
        dag: {
          ...state.dag,
          nodes: state.dag.nodes.map(n => n.id === atomId ? updatedAtom : n),
        },
      }
    }
    case 'cascade_triggered': {
      const atomId = atom_id || payload.atom_id
      if (!atomId) return state
      const atom = state.atoms[atomId]
      if (!atom) return state
      const updatedAtom = { ...atom, status: 'cascade_risk' }
      return {
        ...state,
        atoms: { ...state.atoms, [atomId]: updatedAtom },
        dag: {
          ...state.dag,
          nodes: state.dag.nodes.map(n => n.id === atomId ? updatedAtom : n),
        },
      }
    }
    case 'report_ready':
      return { ...state, reportReady: true, buildStage: 'Report ready' }
    case 'job_complete':
      return { ...state, buildStage: 'Ready', status: { ...state.status, status: 'completed', completed_atoms: state.status?.total_atoms || state.dag.nodes.length } }
    case 'job_error':
      return { ...state, status: { ...state.status, status: 'error' } }
    default:
      return state
  }
}

function AtomNode({ data }) {
  const isSelected = data.selectedId === data.id
  const color = statusColor(data.status)
  
  return (
    <>
      <Handle type="target" position={Position.Left} className="!w-2 !h-2 !border-0" style={{ background: color }} />
      <div 
        className={`px-4 py-2 border rounded-md min-w-[150px] transition-all duration-200`}
        style={{
          backgroundColor: '#131720',
          borderColor: isSelected ? color : `${color}40`,
          boxShadow: isSelected ? `0 0 0 2px ${color}33` : `0 2px 4px rgba(0,0,0,0.2)`
        }}
      >
        <div className="flex items-center gap-2 mb-1">
          <span
            className="w-2 h-2 rounded-full inline-block"
            style={{ background: color, boxShadow: `0 0 4px ${color}80` }}
          />
          <span className="text-[10px] uppercase font-mono opacity-70 text-[#E4E7F0]">{data.atom_type}</span>
        </div>
        <div className="text-xs font-sans truncate text-[#E4E7F0]">{compactLabel(data.label || data.text || data.id)}</div>
      </div>
      <Handle type="source" position={Position.Right} className="!w-2 !h-2 !border-0" style={{ background: color }} />
    </>
  )
}
const nodeTypes = { atom: AtomNode }

function compactLabel(value = '') {
  const words = String(value)
    .replace(/[$\\{}[\]().,;:]/g, ' ')
    .split(/\s+/)
    .filter(Boolean)
  return words.slice(0, 6).join(' ') || String(value)
}

function BuildProgress({ state, nodes, edges, completed, total }) {
  const extractionTotal = state.dag?.extraction_batches_total || 0
  const extractionDone = state.dag?.extraction_batches_completed || 0
  const inExtraction = extractionTotal > 0 && state.buildStage.toLowerCase().includes('extract')
  const parsed = state.dag?.parsed_atoms || nodes.length
  const knownTotal = inExtraction ? 0 : Math.max(total || 0, state.dag?.total_atoms || 0, nodes.length)
  const atomPct = knownTotal ? Math.round((completed / knownTotal) * 100) : 0
  const parsedPct = knownTotal ? Math.round((parsed / knownTotal) * 100) : 0
  const batchPct = extractionTotal ? 25 + Math.round((extractionDone / extractionTotal) * 35) : 0
  const rawPct = state.status?.status === 'complete' || state.status?.status === 'completed'
    ? 100
    : Math.max(stageProgress(state.buildStage), atomPct, parsedPct > 0 ? Math.min(parsedPct, 65) : 0, batchPct)
  const [maxPct, setMaxPct] = useState(rawPct)
  useEffect(() => {
    setMaxPct(prev => Math.max(prev, rawPct))
  }, [rawPct])
  const pct = maxPct
  const recent = state.recentAtoms?.length ? state.recentAtoms : nodes.slice(-5)

  return (
    <div className="border-b border-white/10 bg-[#131720] px-6 py-3 z-10">
      <div className="flex items-center justify-between gap-4 text-xs">
        <div className="min-w-0">
          <div className="font-semibold text-[#E4E7F0]">{state.buildStage}</div>
          <div className="text-white/50">
            {inExtraction
              ? `${parsed} atoms discovered · batch ${extractionDone}/${extractionTotal}`
              : knownTotal ? `${parsed}/${knownTotal} atoms parsed` : 'Discovering atoms...'}
            {knownTotal > 0 && ` · ${completed}/${knownTotal} reviewed`}
            {edges.length > 0 && ` · ${edges.length} dependencies linked`}
          </div>
        </div>
        <div className="font-mono text-[#5B5BD6]">{pct}%</div>
      </div>
      <div className="mt-2 h-2 overflow-hidden rounded-full bg-white/10">
        <div className="h-full rounded-full bg-[#5B5BD6] transition-all duration-500" style={{ width: `${pct}%` }} />
      </div>
      {recent.length > 0 && (
        <div className="mt-2 flex flex-wrap gap-2 text-[11px] text-white/60">
          <span className="uppercase tracking-wider text-white/40">Just parsed</span>
          {recent.slice(-3).map(atom => (
            <span key={atom.id || atom.atom_id} className="max-w-[260px] truncate rounded border border-white/10 bg-white/5 px-2 py-1">
              {compactLabel(atom.label || atom.text || atom.id || atom.atom_id)}
            </span>
          ))}
        </div>
      )}
    </div>
  )
}

function stageProgress(stage = '') {
  const normalized = stage.toLowerCase()
  if (normalized.includes('ready')) return 100
  if (normalized.includes('report')) return 95
  if (normalized.includes('review')) return 72
  if (normalized.includes('dependency')) return 62
  if (normalized.includes('extract')) return 38
  if (normalized.includes('parsing')) return 20
  if (normalized.includes('preparing')) return 8
  return 5
}

export default function Review() {
  const { jobId } = useParams()
  const [state, dispatch] = useReducer(reducer, initialState)
  const [selectedId, setSelectedId] = useState(null)
  const [error, setError] = useState('')
  
  const [isReportOpen, setIsReportOpen] = useState(false)
  const [reportContent, setReportContent] = useState('')

  useEffect(() => {
    if (!jobId) return
    let cancelled = false
    let eventSource = null

    async function load() {
      try {
        const [s, d] = await Promise.all([
          api.review.status(jobId),
          api.review.dag(jobId),
        ])
        if (cancelled) return
        dispatch({ type: 'INIT', payload: { status: s, dag: d } })

        eventSource = api.review.stream(jobId)
        eventSource.addEventListener('dag_update', (e) => {
          try {
            const data = JSON.parse(e.data)
            dispatch(data)
            if (data.event_type === 'job_complete' || data.event_type === 'job_error') {
              eventSource.close() // Close connection cleanly when job finishes
            }
          } catch (err) {
            console.error('Failed to parse SSE event', err)
          }
        })
        eventSource.onerror = (err) => {
          console.error('SSE Error', err)
          if (eventSource.readyState === EventSource.CLOSED) {
            // This happens normally if the server closes the connection
            // We shouldn't spam errors if the job might just be done.
          } else {
            setError('Lost connection to server or job not found. Stop retrying.')
            eventSource.close()
          }
        }
      } catch (err) {
        if (!cancelled) setError(err.message || 'Failed to load job')
      }
    }
    load()
    return () => {
      cancelled = true
      if (eventSource) eventSource.close()
    }
  }, [jobId])

  const handleOpenReport = async () => {
    try {
      const md = await api.review.reportMarkdown(jobId)
      setReportContent(md)
      setIsReportOpen(true)
    } catch (err) {
      alert('Failed to load report')
    }
  }

  const nodes = state.dag?.nodes || []
  const edges = state.dag?.edges || []
  
  const { rfNodes, rfEdges } = useMemo(() => {
    const dagreGraph = new dagre.graphlib.Graph()
    dagreGraph.setDefaultEdgeLabel(() => ({}))
    dagreGraph.setGraph({ rankdir: 'LR', nodesep: 50, ranksep: 100 })

    const mappedNodes = nodes.map((n) => ({
      id: n.id,
      type: 'atom',
      data: { ...n, selectedId },
    }))

    const mappedEdges = edges.map((e, i) => {
      const sourceStatus = state.atoms[e.source]?.status
      const targetStatus = state.atoms[e.target]?.status
      const isRisk = sourceStatus === 'cascade_risk' || targetStatus === 'cascade_risk'
      const color = sourceStatus ? statusColor(sourceStatus) : 'rgba(255,255,255,0.4)'
      
      return {
        id: `e-${e.source}-${e.target}-${i}`,
        source: e.source,
        target: e.target,
        animated: isRisk,
        style: { stroke: isRisk ? '#ef4444' : `${color}A0`, strokeWidth: isRisk ? 3 : 2 }
      }
    })

    mappedNodes.forEach((node) => {
      dagreGraph.setNode(node.id, { width: 250, height: 80 })
    })

    mappedEdges.forEach((edge) => {
      dagreGraph.setEdge(edge.source, edge.target)
    })

    dagre.layout(dagreGraph)

    const layoutedNodes = mappedNodes.map((node) => {
      const nodeWithPosition = dagreGraph.node(node.id)
      return {
        ...node,
        position: {
          x: nodeWithPosition.x - 250 / 2,
          y: nodeWithPosition.y - 80 / 2,
        },
      }
    })

    return { rfNodes: layoutedNodes, rfEdges: mappedEdges }
  }, [nodes, edges, selectedId, state.atoms])

  const selected = selectedId ? state.atoms[selectedId] : null
  const completed = state.status?.completed_atoms ?? 0
  const total = state.status?.total_atoms ?? nodes.length

  const handleExport = () => {
    if (!reportContent) return
    const blob = new Blob([reportContent], { type: 'text/markdown' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `report_${jobId}.md`
    document.body.appendChild(a)
    a.click()
    document.body.removeChild(a)
    URL.revokeObjectURL(url)
  }

  return (
    <div className="min-h-screen w-full bg-[#0A0C10] text-[#E4E7F0] flex flex-col font-sans relative overflow-hidden">
      <header className="flex items-center justify-between px-6 py-3 bg-[#131720] border-b border-white/10 z-10">
        <div className="flex items-center gap-4">
          <Link to="/" className="text-[#5B5BD6] text-sm hover:underline">← Home</Link>
          <span className="text-sm opacity-60">Job</span>
          <span className="text-sm font-mono">{jobId}</span>
        </div>
        <div className="flex items-center gap-4 text-sm">
          <span className="opacity-60">Status:</span>
          <span className="font-semibold">{state.status?.status || 'loading…'}</span>
          <span className="opacity-60">·</span>
          <span>{completed}/{total} atoms</span>
          
          {state.reportReady && (
            <button
              onClick={handleOpenReport}
              className="ml-4 px-3 py-1 bg-[#5B5BD6] text-white rounded text-xs font-semibold hover:bg-[#4a4ac2]"
            >
              View Report
            </button>
          )}
        </div>
      </header>

      {error && (
        <div className="px-6 py-2 bg-red-500/10 text-red-300 text-sm z-10">{error}</div>
      )}
      <BuildProgress state={state} nodes={nodes} edges={edges} completed={completed} total={total} />

      <div className="flex-1 grid grid-cols-[280px_1fr_380px] min-h-0">
        <aside className="bg-[#0D1017] border-r border-white/10 overflow-y-auto">
          <div className="px-4 py-3 text-xs uppercase tracking-wider opacity-60 font-sans">Atoms</div>
          {nodes.length === 0 && (
            <div className="px-4 py-2 text-sm opacity-50">Waiting for atoms…</div>
          )}
          <ul className="pb-4">
            {nodes.map((n) => {
              const active = n.id === selectedId
              return (
                <li key={n.id}>
                  <button
                    onClick={() => setSelectedId(n.id)}
                    className={`w-full text-left px-4 py-2 border-b border-white/5 hover:bg-white/5 ${active ? 'bg-white/10' : ''}`}
                  >
                    <div className="flex items-center gap-2 font-mono">
                      <span
                        className="w-2 h-2 rounded-full inline-block"
                        style={{ background: statusColor(n.status) }}
                      />
                      <span className="text-[10px] uppercase opacity-70">{n.atom_type}</span>
                    </div>
                    <div className="text-sm mt-1 line-clamp-2 font-sans">{compactLabel(n.label || n.id)}</div>
                    {n.section && (
                      <div className="text-[11px] opacity-50 mt-0.5 truncate">{n.section}</div>
                    )}
                  </button>
                </li>
              )
            })}
          </ul>
        </aside>

        <main className="relative flex-1 h-full bg-[#0A0C10]">
          {rfNodes.length > 0 ? (
            <ReactFlow
              nodes={rfNodes}
              edges={rfEdges}
              nodeTypes={nodeTypes}
              onNodeClick={(_, node) => setSelectedId(node.id)}
              fitView
              className="dark"
            >
              <Background color="#333" gap={16} />
              <Controls className="!bg-[#131720] !border-white/10 !fill-white" />
            </ReactFlow>
          ) : (
            <div className="flex items-center justify-center h-full text-sm opacity-50">
              Initializing DAG...
            </div>
          )}
        </main>

        <aside className="bg-[#131720] border-l border-white/10 overflow-y-auto">
          {!selected ? (
            <div className="p-6 text-sm opacity-50">Select an atom to inspect.</div>
          ) : (
            <div className="p-4 space-y-4">
              <div className="flex items-center gap-2 font-mono">
                <span
                  className="w-2.5 h-2.5 rounded-full inline-block"
                  style={{ background: statusColor(selected.status) }}
                />
                <span className="text-xs uppercase opacity-70">{selected.atom_type}</span>
                <span className="ml-auto text-xs opacity-60">{selected.status}</span>
              </div>
              <div className="text-sm font-sans font-medium">{compactLabel(selected.label || selected.id)}</div>
              
              {selected.source_excerpt && (
                <div className="mt-2 bg-[#0D1017] border border-white/10 rounded p-3">
                  <div className="text-[10px] uppercase tracking-wider opacity-50 mb-2 font-sans">Source excerpt</div>
                  <div className="text-[11px] font-mono whitespace-pre-wrap opacity-80">{selected.source_excerpt}</div>
                </div>
              )}

              <FormalizationPanel jobId={jobId} atom={selected} />

              {(state.checks[selected.id] || []).length > 0 && (
                <div className="mt-4">
                  <div className="text-[10px] uppercase tracking-wider opacity-50 mb-2 font-sans">Checks</div>
                  <ul className="space-y-2">
                    {state.checks[selected.id].map((c, i) => (
                      <li key={i} className="text-[11px] font-mono bg-black/20 p-2 rounded">
                        <span style={{ color: statusColor(c.status) }}>{c.status}</span> - {c.tier || c.check_type || 'check'}
                      </li>
                    ))}
                  </ul>
                </div>
              )}

              {/* Threaded Chat UI for Challenges and Rebuttals */}
              {(state.challenges[selected.id] || []).length > 0 && (
                <div className="mt-6 space-y-6">
                  <div className="text-[10px] uppercase tracking-wider opacity-50 mb-4 font-sans border-b border-white/10 pb-2">Review Thread</div>
                  {(state.challenges[selected.id] || []).map((c, i) => {
                    const matchingRebuttals = (state.rebuttals[selected.id] || []).filter(r => r.challenge_id === c.challenge_id)
                    return (
                      <div key={i} className="flex flex-col gap-3">
                        {/* Challenge Bubble */}
                        <div className="bg-[#1a1315] border border-red-900/30 rounded-lg p-3 relative">
                          <div className="absolute -left-1.5 top-3 w-3 h-3 bg-[#1a1315] border-l border-b border-red-900/30 rotate-45" />
                          <div className="flex items-center gap-2 mb-2 flex-wrap relative z-10">
                            <span className="text-[10px] uppercase font-mono px-1.5 py-0.5 rounded bg-red-900/40 text-red-300">
                              {c.severity || 'HIGH'}
                            </span>
                            <span className="text-[10px] uppercase font-mono px-1.5 py-0.5 rounded bg-white/10 text-white/70">
                              {(c.challenge_type || c.attacker_agent || 'CHALLENGE').replace(/_/g, ' ')}
                            </span>
                          </div>
                          <div className="text-[13px] font-sans text-red-100/90 leading-relaxed relative z-10">
                            {c.challenge_text || JSON.stringify(c)}
                          </div>
                        </div>

                        {/* Rebuttal Bubbles */}
                        {matchingRebuttals.length > 0 && (
                          <div className="flex flex-col gap-3 pl-6 border-l-2 border-white/5 ml-3">
                            {matchingRebuttals.map((r, j) => (
                              <div key={j} className="bg-[#121820] border border-blue-900/30 rounded-lg p-3 relative">
                                <div className="absolute -left-1.5 top-3 w-3 h-3 bg-[#121820] border-l border-b border-blue-900/30 rotate-45" />
                                <div className="flex items-center gap-2 mb-2 flex-wrap relative z-10">
                                  <span className="text-[10px] uppercase font-mono px-1.5 py-0.5 rounded bg-blue-900/40 text-blue-300">
                                    {(r.response_type || 'REBUTTAL').replace(/_/g, ' ')}
                                  </span>
                                </div>
                                <div className="text-[13px] font-sans text-blue-100/90 leading-relaxed relative z-10">
                                  {r.rebuttal_text || JSON.stringify(r)}
                                </div>
                              </div>
                            ))}
                          </div>
                        )}
                      </div>
                    )
                  })}
                </div>
              )}

            </div>
          )}
        </aside>
      </div>

      <div 
        className={`absolute top-0 right-0 h-full w-[600px] bg-[#131720] border-l border-white/20 shadow-2xl transition-transform duration-300 z-50 overflow-y-auto ${isReportOpen ? 'translate-x-0' : 'translate-x-full'}`}
      >
        <div className="p-6">
          <div className="flex items-center justify-between mb-6">
            <h2 className="text-xl font-semibold">Review Report</h2>
            <div className="flex items-center gap-2">
              <button 
                onClick={handleExport}
                className="px-3 py-1 bg-[#5B5BD6] hover:bg-[#4b4bc0] text-white rounded text-sm transition-colors shadow-lg"
              >
                Export Markdown
              </button>
              <button 
                onClick={() => setIsReportOpen(false)}
                className="px-3 py-1 bg-white/10 hover:bg-white/20 rounded text-sm transition-colors"
              >
                Close
              </button>
            </div>
          </div>
          <div className="prose prose-invert prose-sm max-w-none prose-pre:bg-[#0d1117] prose-pre:border prose-pre:border-white/10 prose-headings:font-bold prose-a:text-blue-400">
            <ReactMarkdown remarkPlugins={[remarkBreaks]}>{reportContent}</ReactMarkdown>
          </div>
        </div>
      </div>
    </div>
  )
}
