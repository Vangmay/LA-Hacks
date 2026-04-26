import { useEffect, useMemo, useRef, useState } from 'react'
import { Link, useParams } from 'react-router-dom'
import { ReactFlow, Background, Controls, Handle, Position } from '@xyflow/react'
import '@xyflow/react/dist/style.css'
import dagre from 'dagre'
import { api } from '../api/client'

const LEVELS = ['layperson', 'undergraduate', 'graduate', 'expert']
const TABS = ['explain', 'prerequisites', 'exercises', 'tutor']

function ReaderNode({ data }) {
  const isSelected = data.selectedId === data.id
  const color = isSelected ? '#00AFA3' : data.start_here ? '#FBBF24' : '#64748B'

  return (
    <>
      <Handle type="target" position={Position.Left} className="!w-2 !h-2 !border-0" style={{ background: color }} />
      <div
        className="px-4 py-2 border rounded-md min-w-[170px] transition-all duration-200"
        style={{
          backgroundColor: '#101A1E',
          borderColor: isSelected ? color : `${color}55`,
          boxShadow: isSelected ? `0 0 0 2px ${color}33` : data.start_here ? `0 0 0 1px #FBBF2444` : '0 2px 4px rgba(0,0,0,0.22)',
        }}
      >
        <div className="flex items-center gap-2 mb-1">
          <span className="w-2 h-2 rounded-full inline-block" style={{ background: color, boxShadow: `0 0 5px ${color}` }} />
          <span className="text-[10px] uppercase font-mono opacity-70 text-[#E4E7F0]">{data.atom_type}</span>
          {data.start_here && <span className="ml-auto text-[10px] text-[#FBBF24]">START</span>}
        </div>
        <div className="text-xs font-sans truncate text-[#E4E7F0]">{compactLabel(data.label || data.source_excerpt || data.id)}</div>
      </div>
      <Handle type="source" position={Position.Right} className="!w-2 !h-2 !border-0" style={{ background: color }} />
    </>
  )
}

const nodeTypes = { atom: ReaderNode }

function Skeleton({ lines = 5 }) {
  return (
    <div className="animate-pulse space-y-2">
      {Array.from({ length: lines }).map((_, i) => (
        <div key={i} className="h-3 rounded bg-white/10" style={{ width: i === lines - 1 ? '65%' : '100%' }} />
      ))}
    </div>
  )
}

function ActionsPanel({ nodes, onExport, exporting }) {
  const total = nodes.length

  return (
    <div className="p-4 border-t border-white/10">
      <div className="text-xs uppercase tracking-wider text-[#6B7280] font-semibold mb-3">Study materials</div>
      <button
        onClick={onExport}
        disabled={exporting || total === 0}
        className="w-full px-3 py-2 rounded bg-[#00AFA3]/20 border border-[#00AFA3]/40 text-[#67E8F9] text-xs font-semibold disabled:opacity-40"
      >
        {exporting ? 'Exporting...' : 'Export Study Guide'}
      </button>
    </div>
  )
}

function ExplainTab({ annotation, level, onLevelChange }) {
  if (!annotation) return <Skeleton lines={6} />
  return (
    <div className="space-y-4">
      <div className="flex items-center gap-2">
        <label htmlFor="reader-level" className="text-[10px] uppercase tracking-wider text-[#6B7280]">Level</label>
        <select
          id="reader-level"
          value={level}
          onChange={e => onLevelChange(e.target.value)}
          className="rounded border border-white/10 bg-[#0B1115] px-2.5 py-1 text-xs text-[#E4E7F0] outline-none focus:border-[#00AFA3]"
        >
          {LEVELS.map(l => (
            <option key={l} value={l}>{l}</option>
          ))}
        </select>
      </div>
      <div className="text-sm leading-relaxed text-[#DDE5EE]">{annotation.explanation || 'No explanation generated.'}</div>
      {annotation.key_insight && (
        <div className="border-l-2 border-[#00AFA3] bg-[#00AFA3]/10 rounded-r p-3">
          <div className="text-[10px] uppercase tracking-wider text-[#67E8F9] mb-1">Key insight</div>
          <div className="text-sm text-[#E4E7F0]">{annotation.key_insight}</div>
        </div>
      )}
      {annotation.worked_example && (
        <div>
          <div className="text-[10px] uppercase tracking-wider text-[#6B7280] mb-2">Worked example</div>
          <pre className="text-xs whitespace-pre-wrap bg-[#0B1115] border border-white/10 rounded p-3 overflow-x-auto">{annotation.worked_example}</pre>
        </div>
      )}
    </div>
  )
}

function PrerequisitesTab({ annotation }) {
  if (!annotation) return <Skeleton lines={5} />
  const prereqs = annotation.prerequisites || []
  if (!prereqs.length) return <div className="text-sm text-[#6B7280]">No external prerequisites identified.</div>
  return (
    <div className="space-y-3">
      {prereqs.map((p, i) => (
        <div key={`${p.concept}-${i}`} className="rounded border border-white/10 bg-[#0B1115] p-3">
          <div className="text-sm font-semibold text-[#E4E7F0]">{p.concept}</div>
          <div className="text-xs text-[#AAB4C2] leading-relaxed mt-1">{p.description}</div>
          {dedupeLinks(p.resource_links).length > 0 && (
            <div className="flex flex-wrap gap-2 mt-3">
              {dedupeLinks(p.resource_links).map(link => (
                <a key={link} href={link} target="_blank" rel="noreferrer" className="text-[11px] rounded border px-2 py-1 border-[#00AFA3]/50 text-[#67E8F9] hover:bg-[#00AFA3]/10">
                  read more
                </a>
              ))}
            </div>
          )}
        </div>
      ))}
    </div>
  )
}

function dedupeLinks(links = []) {
  return [...new Set(links.filter(link => typeof link === 'string' && link.startsWith('http')))]
}

function normalizeGraph(g = {}) {
  return {
    nodes: (g.nodes || []).map(n => ({ ...n, id: n.id || n.atom_id })),
    edges: (g.edges || []).map(e => ({
      ...e,
      id: e.id || e.edge_id,
      source: e.source || e.source_id,
      target: e.target || e.target_id,
    })),
    start_here: g.start_here || [],
    stage: g.stage,
    parsed_atoms: g.parsed_atoms || (g.nodes || []).length,
    total_atoms: g.total_atoms || (g.nodes || []).length,
    extraction_batches_completed: g.extraction_batches_completed,
    extraction_batches_total: g.extraction_batches_total,
    recent_atoms: g.recent_atoms || [],
  }
}

function compactLabel(value = '') {
  const words = String(value)
    .replace(/[$\\{}[\]().,;:]/g, ' ')
    .split(/\s+/)
    .filter(Boolean)
  return words.slice(0, 6).join(' ') || String(value)
}

function BuildProgress({ graph, status, buildStage }) {
  const extractionTotal = graph.extraction_batches_total || 0
  const extractionDone = graph.extraction_batches_completed || 0
  // inExtraction: true whenever the stage says 'extract', regardless of whether batch info has arrived
  const inExtraction = status?.status !== 'complete' && buildStage.toLowerCase().includes('extract')
  const total = inExtraction ? 0 : (graph.total_atoms || status?.total_atoms || graph.nodes.length || 0)
  const parsed = graph.parsed_atoms || graph.nodes.length || 0
  const hasKnownTotal = total > 0
  const stageFloor = stageProgress(buildStage)
  const nextFloor = stageProgress('dependency') // 72 — extraction ends when graph build starts
  const atomPct = hasKnownTotal ? Math.round((parsed / total) * 100) : 0
  // Batch progress starts at stageFloor and advances toward the next stage floor
  const batchPct = inExtraction && extractionTotal > 0
    ? stageFloor + Math.round((extractionDone / extractionTotal) * (nextFloor - stageFloor))
    : 0
  const rawPct = status?.status === 'complete' ? 100 : Math.max(stageFloor, atomPct, batchPct)
  const [maxPct, setMaxPct] = useState(0)
  useEffect(() => {
    setMaxPct(prev => Math.max(prev, rawPct))
  }, [rawPct])
  const pct = maxPct
  const recent = graph.recent_atoms?.length ? graph.recent_atoms : graph.nodes.slice(-5)

  return (
    <div className="border-b border-white/10 bg-[#101A1E] px-6 py-3">
      <div className="flex items-center justify-between gap-4 text-xs">
        <div className="min-w-0">
          <div className="font-semibold text-[#E4E7F0]">{buildStage}</div>
          <div className="text-[#6B7280]">
            {inExtraction
              ? extractionTotal > 0
                ? `${parsed} atoms discovered · batch ${extractionDone}/${extractionTotal}`
                : parsed > 0 ? `${parsed} atoms discovered · starting LLM pass...` : 'Starting extraction...'
              : hasKnownTotal ? `${parsed}/${total} atoms parsed` : 'Discovering atoms...'}
            {graph.edges.length > 0 && ` · ${graph.edges.length} dependencies linked`}
          </div>
        </div>
        <div className="font-mono text-[#67E8F9]">{pct}%</div>
      </div>
      <div className="mt-2 h-2 overflow-hidden rounded-full bg-white/10">
        <div className="h-full rounded-full bg-[#00AFA3] transition-all duration-500" style={{ width: `${pct}%` }} />
      </div>
      {recent.length > 0 && (
        <div className="mt-2 flex flex-wrap gap-2 text-[11px] text-[#AAB4C2]">
          <span className="uppercase tracking-wider text-[#6B7280]">Just parsed</span>
          {recent.slice(-3).map(atom => (
            <span key={atom.id} className="max-w-[260px] truncate rounded border border-white/10 bg-white/5 px-2 py-1">
              {compactLabel(atom.label || atom.id)}
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
  if (normalized.includes('dependency')) return 72
  if (normalized.includes('extract')) return 40
  if (normalized.includes('parsing')) return 20
  if (normalized.includes('preparing')) return 5
  return 0
}

function ExercisesTab({ annotation, sessionId, atomId }) {
  const [answers, setAnswers] = useState({})
  const [results, setResults] = useState({})
  const [grading, setGrading] = useState({})

  if (!annotation) return <Skeleton lines={5} />
  const exercises = annotation.exercises || []
  if (!exercises.length) return <div className="text-sm text-[#6B7280]">No exercises generated.</div>

  async function submit(ex) {
    const answer = (answers[ex.exercise_id] || '').trim()
    if (!answer || grading[ex.exercise_id]) return
    setGrading(g => ({ ...g, [ex.exercise_id]: true }))
    try {
      const res = await api.reader.grade(sessionId, atomId, ex.exercise_id, answer)
      setResults(r => ({ ...r, [ex.exercise_id]: res }))
    } finally {
      setGrading(g => ({ ...g, [ex.exercise_id]: false }))
    }
  }

  return (
    <div className="space-y-4">
      {exercises.map(ex => {
        const result = results[ex.exercise_id]
        const mcq = getMcqParts(ex)
        const isMcq = ex.exercise_type === 'counterexample_mcq' && mcq.options.length > 0
        const selectedAnswer = answers[ex.exercise_id] || ''
        return (
          <div key={ex.exercise_id} className="rounded border border-white/10 bg-[#0B1115] p-3">
            <div className="text-[10px] uppercase tracking-wider text-[#67E8F9] mb-2">{(ex.exercise_type || 'exercise').replace(/_/g, ' ')}</div>
            <div className="text-sm leading-relaxed text-[#E4E7F0] mb-3">{isMcq ? mcq.prompt : ex.prompt}</div>
            {!result ? (
              isMcq ? (
                <div className="space-y-3">
                  <div className="grid gap-2">
                    {mcq.options.map(option => {
                      const value = `${option.label}. ${option.text}`
                      const selected = selectedAnswer === value
                      return (
                        <button
                          key={option.label}
                          type="button"
                          onClick={() => setAnswers(a => ({ ...a, [ex.exercise_id]: value }))}
                          className={`flex items-start gap-3 rounded border px-3 py-2 text-left text-sm transition-colors ${selected ? 'border-[#00AFA3] bg-[#00AFA3]/15 text-[#E4E7F0]' : 'border-white/10 bg-white/5 text-[#AAB4C2] hover:border-white/20'}`}
                        >
                          <span className={`mt-0.5 flex h-5 w-5 shrink-0 items-center justify-center rounded border text-[11px] font-semibold ${selected ? 'border-[#00AFA3] text-[#67E8F9]' : 'border-white/20 text-[#6B7280]'}`}>
                            {option.label}
                          </span>
                          <span className="leading-relaxed">{option.text}</span>
                        </button>
                      )
                    })}
                  </div>
                  <button
                    onClick={() => submit(ex)}
                    disabled={grading[ex.exercise_id] || !selectedAnswer.trim()}
                    className="w-full px-3 py-2 rounded bg-[#00AFA3]/20 border border-[#00AFA3]/40 text-[#67E8F9] text-xs font-semibold disabled:opacity-40"
                  >
                    {grading[ex.exercise_id] ? 'Checking...' : 'Submit answer'}
                  </button>
                </div>
              ) : (
                <div className="flex gap-2">
                  <input
                    value={selectedAnswer}
                    onChange={e => setAnswers(a => ({ ...a, [ex.exercise_id]: e.target.value }))}
                    onKeyDown={e => e.key === 'Enter' && submit(ex)}
                    placeholder="Your answer"
                    className="flex-1 px-3 py-2 rounded bg-white/5 border border-white/10 text-sm outline-none focus:border-[#00AFA3]"
                  />
                  <button
                    onClick={() => submit(ex)}
                    disabled={grading[ex.exercise_id] || !selectedAnswer.trim()}
                    className="px-3 py-2 rounded bg-[#00AFA3]/20 border border-[#00AFA3]/40 text-[#67E8F9] text-xs font-semibold disabled:opacity-40"
                  >
                    {grading[ex.exercise_id] ? 'Checking...' : 'Submit'}
                  </button>
                </div>
              )
            ) : (
              <div className="space-y-2">
                <div className={`text-sm font-semibold ${result.correct ? 'text-[#16A34A]' : 'text-[#EF4444]'}`}>
                  {result.correct ? 'Correct' : 'Not quite'}
                </div>
                <div className="text-xs text-[#AAB4C2]">{result.feedback}</div>
                <div className="text-xs rounded bg-white/5 p-2"><span className="text-[#6B7280]">Answer key: </span>{ex.answer_key}</div>
              </div>
            )}
          </div>
        )
      })}
    </div>
  )
}

function getMcqParts(ex) {
  const explicitOptions = Array.isArray(ex.options) ? ex.options.filter(Boolean).slice(0, 4) : []
  if (explicitOptions.length) {
    return {
      prompt: stripEmbeddedChoices(ex.prompt),
      options: explicitOptions.map((text, index) => ({
        label: String.fromCharCode(65 + index),
        text: String(text).replace(/^\(?[A-D]\)?[\s).:-]+/i, '').trim(),
      })),
    }
  }

  const prompt = ex.prompt || ''
  const start = prompt.search(/\(?A\)?[\s).:-]+/i)
  if (start === -1) return { prompt, options: [] }

  const question = prompt.slice(0, start).trim()
  const choiceText = prompt.slice(start)
  const matches = [...choiceText.matchAll(/\(?([A-D])\)?[\s).:-]+([\s\S]*?)(?=\s*\(?[A-D]\)?[\s).:-]+|$)/gi)]
  return {
    prompt: question || prompt,
    options: matches.map(match => ({
      label: match[1].toUpperCase(),
      text: match[2].trim(),
    })).filter(option => option.text),
  }
}

function stripEmbeddedChoices(prompt = '') {
  const start = prompt.search(/\(?A\)?[\s).:-]+/i)
  return start === -1 ? prompt : prompt.slice(0, start).trim()
}

function TutorTab({ sessionId, atomId, history, onHistory }) {
  const [input, setInput] = useState('')
  const [loading, setLoading] = useState(false)
  const bottomRef = useRef(null)

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [history, loading])

  async function send() {
    const message = input.trim()
    if (!message || loading) return
    const next = [...history, { role: 'user', content: message }]
    onHistory(next)
    setInput('')
    setLoading(true)
    try {
      const res = await api.reader.tutor(sessionId, atomId, message, history)
      onHistory([...next, { role: 'assistant', content: res.response || res.detail || '' }])
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="flex flex-col h-[calc(100vh-250px)] min-h-[360px]">
      <div className="flex-1 overflow-y-auto space-y-3 pr-1">
        {!history.length && <div className="text-sm text-[#6B7280] text-center mt-6">Ask about this atom...</div>}
        {history.map((m, i) => (
          <div key={i} className={`flex ${m.role === 'user' ? 'justify-end' : 'justify-start'}`}>
            <div className={`max-w-[85%] rounded px-3 py-2 text-sm leading-relaxed ${m.role === 'user' ? 'bg-[#2563EB]/20 border border-[#2563EB]/30' : 'bg-white/5 border border-white/10'}`}>
              {m.content}
            </div>
          </div>
        ))}
        {loading && <div className="text-xs text-[#6B7280]">Thinking...</div>}
        <div ref={bottomRef} />
      </div>
      <div className="flex gap-2 pt-3">
        <input
          value={input}
          onChange={e => setInput(e.target.value)}
          onKeyDown={e => e.key === 'Enter' && send()}
          placeholder="Ask about this atom..."
          className="flex-1 px-3 py-2 rounded bg-white/5 border border-white/10 text-sm outline-none focus:border-[#00AFA3]"
        />
        <button onClick={send} disabled={loading || !input.trim()} className="px-3 py-2 rounded bg-[#00AFA3]/20 border border-[#00AFA3]/40 text-[#67E8F9] text-xs font-semibold disabled:opacity-40">
          Send
        </button>
      </div>
    </div>
  )
}

function DetailPanel({ node, annotation, loading, canAnnotate, level, onLevelChange, sessionId, tutorHistories, onTutorHistory }) {
  const [tab, setTab] = useState('explain')

  useEffect(() => {
    setTab('explain')
  }, [node?.id])

  if (!node) return <div className="p-6 text-sm text-[#6B7280]">Select an atom to generate learner materials.</div>

  return (
    <div className="p-4 space-y-4">
      <div>
        <div className="flex items-center gap-2 mb-2">
          <span className="text-xs font-mono uppercase text-[#AAB4C2]">{node.atom_type}</span>
          {node.start_here && <span className="ml-auto text-[10px] text-[#FBBF24]">START</span>}
        </div>
        <div className="text-sm font-medium text-[#E4E7F0]">{compactLabel(node.label || node.id)}</div>
        {node.source_excerpt && (
          <div className="mt-3 rounded border border-white/10 bg-[#0B1115] p-3">
            <div className="text-[10px] uppercase tracking-wider text-[#6B7280] mb-2">Source excerpt</div>
            <div className="text-[11px] font-mono whitespace-pre-wrap text-[#AAB4C2]">{node.source_excerpt}</div>
          </div>
        )}
      </div>

      <div className="flex gap-1 flex-wrap border-b border-white/10 pb-2">
        {TABS.map(name => (
          <button
            key={name}
            onClick={() => setTab(name)}
            className={`px-3 py-1 rounded text-xs capitalize ${tab === name ? 'bg-[#00AFA3]/20 text-[#67E8F9]' : 'text-[#AAB4C2] hover:bg-white/5'}`}
          >
            {name}
          </button>
        ))}
      </div>

      {!canAnnotate ? (
        <div className="rounded border border-white/10 bg-[#0B1115] p-3 text-sm leading-relaxed text-[#AAB4C2]">
          Learner materials will unlock once the dependency graph finishes. You can still inspect the atoms as they appear.
        </div>
      ) : loading ? <Skeleton lines={7} /> : (
        <>
          {tab === 'explain' && <ExplainTab annotation={annotation} level={level} onLevelChange={onLevelChange} />}
          {tab === 'prerequisites' && <PrerequisitesTab annotation={annotation} />}
          {tab === 'exercises' && <ExercisesTab annotation={annotation} sessionId={sessionId} atomId={node.id} />}
          {tab === 'tutor' && (
            <TutorTab
              sessionId={sessionId}
              atomId={node.id}
              history={tutorHistories[node.id] || []}
              onHistory={messages => onTutorHistory(node.id, messages)}
            />
          )}
        </>
      )}
    </div>
  )
}

export default function Reader() {
  const { sessionId } = useParams()
  const [status, setStatus] = useState(null)
  const [graph, setGraph] = useState({ nodes: [], edges: [] })
  const [selectedId, setSelectedId] = useState(null)
  const [annotations, setAnnotations] = useState({})
  const [loadingAnnotation, setLoadingAnnotation] = useState(false)
  const [level, setLevel] = useState('undergraduate')
  const [error, setError] = useState('')
  const [exporting, setExporting] = useState(false)
  const [tutorHistories, setTutorHistories] = useState({})

  useEffect(() => {
    if (!sessionId) return
    let cancelled = false
    let timer = null

    async function loadStatus() {
      try {
        const s = await api.reader.status(sessionId)
        if (cancelled) return
        setStatus(s)
        if (s.comprehension_level) setLevel(s.comprehension_level)
        const g = await api.reader.graph(sessionId)
        if (cancelled) return
        setGraph(normalizeGraph(g))
        if (s.status === 'complete') {
          return
        }
        if (s.status !== 'error') timer = setTimeout(loadStatus, 2000)
      } catch (err) {
        if (!cancelled) setError(err.message || 'Failed to load reader session')
      }
    }

    loadStatus()
    return () => {
      cancelled = true
      if (timer) clearTimeout(timer)
    }
  }, [sessionId])

  async function fetchAnnotation(atomId, nextLevel = level) {
    const cached = annotations[atomId]
    if (cached && cached.level === nextLevel) return
    setLoadingAnnotation(true)
    setError('')
    try {
      const ann = await api.reader.atom(sessionId, atomId, nextLevel)
      if (ann.detail) throw new Error(typeof ann.detail === 'string' ? ann.detail : 'Annotation unavailable')
      setAnnotations(prev => ({ ...prev, [atomId]: ann }))
    } catch (err) {
      setError(err.message || 'Failed to generate learner materials')
    } finally {
      setLoadingAnnotation(false)
    }
  }

  function selectAtom(atomId) {
    setSelectedId(atomId)
    if (status?.status === 'complete') fetchAnnotation(atomId)
  }

  function changeLevel(nextLevel) {
    setLevel(nextLevel)
    if (selectedId && status?.status === 'complete') fetchAnnotation(selectedId, nextLevel)
  }

  async function exportGuide() {
    setExporting(true)
    try {
      const md = await api.reader.studyGuide(sessionId)
      const blob = new Blob([md], { type: 'text/markdown' })
      const url = URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = `study-guide-${sessionId.slice(0, 8)}.md`
      document.body.appendChild(a)
      a.click()
      document.body.removeChild(a)
      URL.revokeObjectURL(url)
    } finally {
      setExporting(false)
    }
  }

  const { rfNodes, rfEdges } = useMemo(() => {
    const dagreGraph = new dagre.graphlib.Graph()
    dagreGraph.setDefaultEdgeLabel(() => ({}))
    dagreGraph.setGraph({ rankdir: 'LR', nodesep: 50, ranksep: 100 })

    const mappedNodes = graph.nodes.map(n => ({
      id: n.id,
      type: 'atom',
      data: { ...n, selectedId },
    }))
    const mappedEdges = graph.edges.map((e, i) => ({
      id: e.id || `e-${e.source}-${e.target}-${i}`,
      source: e.source,
      target: e.target,
      animated: selectedId && (e.source === selectedId || e.target === selectedId),
      style: {
        stroke: selectedId && (e.source === selectedId || e.target === selectedId) ? '#00AFA3' : 'rgba(255,255,255,0.28)',
        strokeWidth: selectedId && (e.source === selectedId || e.target === selectedId) ? 3 : 1.5,
      },
    }))

    mappedNodes.forEach(node => dagreGraph.setNode(node.id, { width: 250, height: 80 }))
    mappedEdges.forEach(edge => dagreGraph.setEdge(edge.source, edge.target))
    dagre.layout(dagreGraph)

    return {
      rfNodes: mappedNodes.map(node => {
        const pos = dagreGraph.node(node.id)
        return { ...node, position: { x: pos.x - 125, y: pos.y - 40 } }
      }),
      rfEdges: mappedEdges,
    }
  }, [graph, selectedId])

  const selected = selectedId ? graph.nodes.find(n => n.id === selectedId) : null
  const annotation = selectedId ? annotations[selectedId] : null
  const title = status?.paper_metadata?.title
  const buildStage = graph.stage || status?.reader_stage || status?.status || 'loading...'
  const canAnnotate = status?.status === 'complete'

  return (
    <div className="min-h-screen w-full bg-[#081113] text-[#E4E7F0] flex flex-col font-sans overflow-hidden">
      <header className="flex items-center justify-between px-6 py-3 bg-[#101A1E] border-b border-white/10 z-10">
        <div className="flex items-center gap-4 min-w-0">
          <Link to="/" className="text-[#67E8F9] text-sm hover:underline">Home</Link>
          <span className="text-sm opacity-60">Learner</span>
          <span className="text-sm font-mono truncate max-w-[260px]">{sessionId}</span>
          {title && <span className="text-xs text-[#6B7280] truncate max-w-[360px]">{title}</span>}
        </div>
        <div className="flex items-center gap-4 text-sm">
          <span className="text-[#6B7280]">Status</span>
          <span className="font-semibold">{buildStage}</span>
          <span>{graph.nodes.length || status?.total_atoms || 0} atoms</span>
          {graph.edges.length > 0 && <span>{graph.edges.length} edges</span>}
        </div>
      </header>

      {error && <div className="px-6 py-2 bg-red-500/10 text-red-300 text-sm">{error}</div>}
      <BuildProgress graph={graph} status={status} buildStage={buildStage} />

      <div className="flex-1 grid grid-cols-[300px_1fr_420px] min-h-0">
        <aside className="bg-[#0B1115] border-r border-white/10 overflow-y-auto flex flex-col">
          <div className="px-4 py-3 text-xs uppercase tracking-wider text-[#6B7280] font-semibold">Atoms</div>
          <div className="flex-1 overflow-y-auto">
            {graph.nodes.length === 0 && (
              <div className="px-4 py-6 text-sm text-[#6B7280]">{status?.status === 'error' ? status.error : buildStage}</div>
            )}
            <ul>
              {graph.nodes.map(n => (
                <li key={n.id}>
                  <button
                    onClick={() => selectAtom(n.id)}
                    className={`w-full text-left px-4 py-2 border-b border-white/5 hover:bg-white/5 ${selectedId === n.id ? 'bg-white/10' : ''}`}
                  >
                    <div className="flex items-center gap-2 font-mono">
                      <span className="text-[10px] uppercase text-[#AAB4C2]">{n.atom_type}</span>
                      {n.start_here && <span className="ml-auto text-[10px] text-[#FBBF24]">START</span>}
                    </div>
                    <div className="text-sm mt-1 line-clamp-2">{compactLabel(n.label || n.id)}</div>
                    {n.section && <div className="text-[11px] text-[#6B7280] mt-0.5 truncate">{n.section}</div>}
                  </button>
                </li>
              ))}
            </ul>
          </div>
          <ActionsPanel nodes={graph.nodes} onExport={exportGuide} exporting={exporting} />
        </aside>

        <main className="relative h-full bg-[#081113]">
          {status?.status === 'processing' && (
            <div className="absolute left-4 top-4 z-10 rounded border border-white/10 bg-[#101A1E]/90 px-3 py-2 text-xs text-[#AAB4C2] shadow">
              <span className="text-[#67E8F9]">{buildStage}</span>
              {graph.nodes.length > 0 && graph.edges.length === 0 && <span> · placing atoms before edges are inferred</span>}
            </div>
          )}
          {rfNodes.length > 0 ? (
            <ReactFlow
              nodes={rfNodes}
              edges={rfEdges}
              nodeTypes={nodeTypes}
              onNodeClick={(_, node) => selectAtom(node.id)}
              fitView
              className="dark"
            >
              <Background color="#1f3438" gap={16} />
              <Controls className="!bg-[#101A1E] !border-white/10 !fill-white" />
            </ReactFlow>
          ) : (
            <div className="flex items-center justify-center h-full text-sm text-[#6B7280]">
              {status?.status === 'processing' ? buildStage : 'Waiting for session...'}
            </div>
          )}
        </main>

        <aside className="bg-[#101A1E] border-l border-white/10 overflow-y-auto">
          <DetailPanel
            node={selected}
            annotation={annotation}
            loading={loadingAnnotation}
            canAnnotate={canAnnotate}
            level={level}
            onLevelChange={changeLevel}
            sessionId={sessionId}
            tutorHistories={tutorHistories}
            onTutorHistory={(atomId, messages) => setTutorHistories(prev => ({ ...prev, [atomId]: messages }))}
          />
        </aside>
      </div>
    </div>
  )
}
