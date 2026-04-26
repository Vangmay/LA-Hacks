import { useCallback, useEffect, useReducer } from 'react'
import { Link, useParams } from 'react-router-dom'
import { api } from '../../api/client'
import { useResearchStream } from '../../hooks/useResearchStream'
import AgentGraph from '../../components/research/AgentGraph'
import InspectorDrawer from '../../components/research/InspectorDrawer'
import EventTicker from '../../components/research/EventTicker'

const initialState = {
  snapshot: null,
  selected: null,
  events: [],
  error: '',
  connection: 'connecting',
}

function reducer(state, action) {
  switch (action.type) {
    case 'SNAPSHOT':
      return {
        ...state,
        snapshot: action.snapshot,
        selected: state.selected || defaultSelection(action.snapshot),
        error: '',
      }
    case 'SELECT':
      return { ...state, selected: action.selected }
    case 'CONNECTION_ERROR':
      return { ...state, connection: 'disconnected', error: action.error }
    case 'EVENT':
      return applyEvent(state, action.event)
    default:
      return state
  }
}

function applyEvent(state, event) {
  if (event.type === 'run.snapshot') {
    return {
      ...state,
      snapshot: event.payload?.snapshot || state.snapshot,
      selected: state.selected || defaultSelection(event.payload?.snapshot),
      connection: 'connected',
      events: [...state.events, event].slice(-250),
    }
  }

  let snapshot = state.snapshot
  if (snapshot) snapshot = applyEventToSnapshot(snapshot, event)
  return {
    ...state,
    snapshot,
    connection: event.type === 'run.error' ? 'disconnected' : 'connected',
    events: [...state.events, event].slice(-250),
    error: event.type === 'run.error' ? event.payload?.error || 'Research run failed' : state.error,
  }
}

function applyEventToSnapshot(snapshot, event) {
  const payload = event.payload || {}
  const next = structuredClone(snapshot)
  next.metadata = next.metadata || {}

  if (event.type === 'stage.entered') {
    next.metadata.status = payload.stage || next.metadata.status
    next.metadata.stage = payload.stage || next.metadata.stage
  }
  if (event.type === 'run.finalized') {
    next.metadata.status = 'completed'
    next.final_report = {
      available: true,
      path: payload.final_report_path || 'final/research_deep_dive_report.md',
      markdown: payload.final_report_md || '',
    }
  }
  if (event.type === 'investigator.synthesized') {
    const investigator = (next.investigators || []).find((item) => item.id === payload.investigator_id)
    if (investigator) {
      investigator.status = 'completed'
      investigator.synthesis_md = payload.synthesis_md || investigator.synthesis_md
    }
  }
  if (event.type === 'subagent.artifact.updated') {
    const subagent = (next.subagents || []).find((item) => item.id === payload.subagent_id)
    if (subagent) {
      subagent.artifacts = subagent.artifacts || {}
      subagent.artifacts[payload.artifact] = payload.content || ''
      subagent.status = subagent.status === 'planned' ? 'running' : subagent.status
    }
  }
  if (event.type?.startsWith('subagent.tool')) {
    const subagent = (next.subagents || []).find((item) => item.id === payload.subagent_id)
    if (subagent) {
      subagent.status = 'running'
      subagent.tool_events = [...(subagent.tool_events || []), payload.trace_entry || payload].slice(-1200)
    }
  }
  if (event.type === 'subagent.budget') {
    const subagent = (next.subagents || []).find((item) => item.id === payload.subagent_id)
    if (subagent) subagent.budget = { ...(subagent.budget || {}), ...snakeBudget(payload) }
  }
  if (event.type === 'subagent.completed') {
    const subagent = (next.subagents || []).find((item) => item.id === payload.subagent_id)
    if (subagent) {
      subagent.status = payload.error ? 'error' : 'completed'
      subagent.summary = payload.summary || subagent.summary
      if (payload.budget) subagent.budget = { ...(subagent.budget || {}), ...snakeBudget(payload.budget) }
    }
  }
  if (event.type === 'cross_investigator.completed') {
    next.shared = next.shared || {}
    for (const [key, content] of Object.entries(payload.artifacts || {})) {
      next.shared[key] = { path: `shared/${key}.md`, content }
    }
  }
  if (event.type === 'critique.completed') {
    next.critiques = next.critiques || []
    const existing = next.critiques.find((item) => item.critic_id === payload.critic_id)
    if (existing) {
      existing.status = 'completed'
      existing.markdown = payload.critique_md || existing.markdown
    } else {
      next.critiques.push({ critic_id: payload.critic_id, lens: payload.lens, status: 'completed', markdown: payload.critique_md || '' })
    }
  }
  next.counts = {
    investigators: next.investigators?.length || 0,
    subagents: next.subagents?.length || 0,
    completed_subagents: (next.subagents || []).filter((item) => item.status === 'completed').length,
    syntheses: (next.investigators || []).filter((item) => item.synthesis_md).length,
    critiques: (next.critiques || []).filter((item) => item.status === 'completed').length,
    tool_events: (next.subagents || []).reduce((sum, item) => sum + (item.tool_events?.length || 0), 0),
  }
  return next
}

export default function ResearchDeepDive() {
  const { runId } = useParams()
  const [state, dispatch] = useReducer(reducer, initialState)

  const loadSnapshot = useCallback(async () => {
    try {
      const snapshot = await api.research.snapshot(runId)
      dispatch({ type: 'SNAPSHOT', snapshot })
    } catch (err) {
      dispatch({ type: 'CONNECTION_ERROR', error: err.message || 'Failed to load research run' })
    }
  }, [runId])

  useEffect(() => {
    loadSnapshot()
  }, [loadSnapshot])

  useResearchStream(runId, dispatch)

  function handleTickerSelect(event) {
    const payload = event.payload || {}
    if (payload.subagent_id) dispatch({ type: 'SELECT', selected: { kind: 'subagent', id: payload.subagent_id } })
    if (payload.investigator_id && !payload.subagent_id) dispatch({ type: 'SELECT', selected: { kind: 'investigator', id: payload.investigator_id } })
    if (event.type === 'run.finalized') dispatch({ type: 'SELECT', selected: { kind: 'final', id: 'final' } })
  }

  const meta = state.snapshot?.metadata || {}
  const counts = state.snapshot?.counts || {}

  return (
    <div className="flex h-screen w-full flex-col overflow-hidden bg-[#0A0C10] text-[#E4E7F0]">
      <header className="z-10 flex items-center gap-4 border-b border-white/10 bg-[#131720] px-5 py-3">
        <Link to="/research" className="text-sm text-[#67E8F9] hover:underline">Research</Link>
        <div className="min-w-0 flex-1">
          <div className="truncate font-mono text-xs text-white/45">{runId}</div>
          <div className="truncate text-sm font-semibold">{meta.arxiv_url || meta.paper_id || 'Deep-dive workspace'}</div>
        </div>
        <div className="hidden items-center gap-2 text-xs text-white/55 md:flex">
          <Pill label={meta.status || 'loading'} tone={state.connection === 'disconnected' ? 'red' : 'cyan'} />
          <Pill label={`${counts.completed_subagents || 0}/${counts.subagents || 0} subagents`} />
          <Pill label={`${counts.tool_events || 0} tool events`} />
        </div>
      </header>

      {state.error && <div className="border-b border-red-500/20 bg-red-500/10 px-5 py-2 text-sm text-red-200">{state.error}</div>}

      <div className="flex min-h-0 flex-1">
        <main className="min-w-0 flex-1 bg-[#0A0C10]">
          <AgentGraph
            snapshot={state.snapshot}
            selected={state.selected}
            onSelect={(selected) => dispatch({ type: 'SELECT', selected })}
          />
        </main>
        <div className="hidden w-[430px] shrink-0 lg:block">
          <InspectorDrawer
            snapshot={state.snapshot}
            selected={state.selected}
            onSelect={(selected) => dispatch({ type: 'SELECT', selected })}
          />
        </div>
      </div>

      <div className="block max-h-[46vh] overflow-y-auto border-t border-white/10 lg:hidden">
        <InspectorDrawer
          snapshot={state.snapshot}
          selected={state.selected}
          onSelect={(selected) => dispatch({ type: 'SELECT', selected })}
        />
      </div>

      <EventTicker events={state.events} onSelect={handleTickerSelect} />
    </div>
  )
}

function Pill({ label, tone = 'slate' }) {
  const colors = {
    cyan: 'border-[#67E8F9]/30 bg-[#67E8F9]/10 text-[#67E8F9]',
    red: 'border-red-400/30 bg-red-400/10 text-red-200',
    slate: 'border-white/10 bg-white/[0.03] text-white/55',
  }
  return <span className={`rounded border px-2.5 py-1 ${colors[tone]}`}>{label}</span>
}

function defaultSelection(snapshot) {
  const firstRunning = (snapshot?.subagents || []).find((item) => item.status === 'running')
  if (firstRunning) return { kind: 'subagent', id: firstRunning.id }
  const firstSubagent = snapshot?.subagents?.[0]
  if (firstSubagent) return { kind: 'subagent', id: firstSubagent.id }
  const firstInvestigator = snapshot?.investigators?.[0]
  if (firstInvestigator) return { kind: 'investigator', id: firstInvestigator.id }
  return null
}

function snakeBudget(value) {
  return {
    research_used: value.research_used ?? value.researchUsed ?? 0,
    research_max: value.research_max ?? value.researchMax ?? 0,
    workspace_used: value.workspace_used ?? value.workspaceUsed ?? 0,
    workspace_max: value.workspace_max ?? value.workspaceMax ?? 0,
    llm_steps: value.llm_steps ?? value.llmSteps ?? 0,
  }
}
