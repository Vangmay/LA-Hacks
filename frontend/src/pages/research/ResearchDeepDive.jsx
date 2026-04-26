import { useCallback, useEffect, useReducer, useRef } from 'react'
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
    case 'CONNECTION_STATE':
      return { ...state, connection: action.connection, error: action.error || state.error }
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

  let snapshot = state.snapshot || emptySnapshot(event.run_id)
  snapshot = applyEventToSnapshot(snapshot, event)
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
  next.investigators = next.investigators || []
  next.subagents = next.subagents || []
  next.shared = next.shared || {}
  next.critiques = next.critiques || []

  if (event.type === 'run.started') {
    next.metadata = {
      ...next.metadata,
      run_id: payload.run_id || event.run_id || next.metadata.run_id,
      arxiv_url: payload.arxiv_url || next.metadata.arxiv_url,
      paper_id: payload.paper_id || next.metadata.paper_id,
      research_objective: payload.objective || next.metadata.research_objective,
      mode: payload.mode || next.metadata.mode,
      workspace_path: payload.workspace_path || next.metadata.workspace_path,
      status: 'running',
      stage: 'bootstrap',
    }
  }

  if (event.type === 'stage.entered') {
    if (next.metadata.status !== 'completed') {
      next.metadata.status = payload.stage || next.metadata.status
      next.metadata.stage = payload.stage || next.metadata.stage
    }
  }
  if (event.type === 'stage.completed') {
    next.metadata.last_completed_stage = payload.stage || next.metadata.last_completed_stage
  }
  if (event.type === 'investigator.planned') {
    const investigator = upsertInvestigator(next, payload.investigator_id, {
      id: payload.investigator_id,
      section_id: payload.section_id || '',
      section_title: payload.section_title || payload.investigator_id,
      workspace_path: payload.workspace_path || '',
      subagent_ids: payload.subagent_ids || [],
      synthesis_md: '',
    })
    investigator.subagent_ids = unique([...(investigator.subagent_ids || []), ...(payload.subagent_ids || [])])
  }
  if (event.type === 'subagent.planned') {
    const subagent = upsertSubagent(next, payload.subagent_id, {
      id: payload.subagent_id,
      investigator_id: payload.investigator_id || '',
      section_id: payload.section_id || '',
      section_title: payload.section_title || '',
      workspace_path: payload.workspace_path || '',
      taste: payload.taste || {},
      allowed_tools: payload.allowed_tools || [],
      max_tool_calls: payload.max_tool_calls || 0,
      model_role: payload.model_role || '',
      artifacts: {},
      artifact_meta: {},
      tool_events: [],
      budget: { research_used: 0, research_max: payload.max_tool_calls || 0, workspace_used: 0, workspace_max: 0, llm_steps: 0 },
    })
    subagent.taste = payload.taste || subagent.taste || {}
    subagent.allowed_tools = payload.allowed_tools || subagent.allowed_tools || []
    subagent.max_tool_calls = payload.max_tool_calls || subagent.max_tool_calls || 0
    subagent.budget = { ...(subagent.budget || {}), research_max: subagent.max_tool_calls || subagent.budget?.research_max || 0 }
    linkSubagent(next, subagent.investigator_id || payload.investigator_id, subagent.id)
  }
  if (event.type === 'subagent.started') {
    const subagent = upsertSubagent(next, payload.subagent_id, {
      id: payload.subagent_id,
      investigator_id: payload.investigator_id || '',
      artifacts: {},
      tool_events: [],
      budget: {},
    })
    markRunning(subagent)
    subagent.model_provider = payload.model_provider || subagent.model_provider
    subagent.model_name = payload.model_name || subagent.model_name
    subagent.model_role = payload.model_role || subagent.model_role
    linkSubagent(next, subagent.investigator_id || payload.investigator_id, subagent.id)
  }
  if (event.type === 'run.finalized') {
    next.metadata.status = 'completed'
    next.metadata.stage = 'completed'
    next.final_report = {
      available: true,
      path: payload.final_report_path || 'final/research_deep_dive_report.md',
      markdown: payload.final_report_md || '',
    }
  }
  if (event.type === 'run.error') {
    next.metadata.status = 'error'
    next.metadata.stage = payload.stage || 'error'
    next.metadata.error = payload.error || 'Research run failed'
  }
  if (event.type === 'investigator.synthesized') {
    const investigator = upsertInvestigator(next, payload.investigator_id, {
      id: payload.investigator_id,
      section_title: payload.investigator_id,
      subagent_ids: [],
    })
    investigator.status = 'completed'
    investigator.synthesis_md = payload.synthesis_md || investigator.synthesis_md
    investigator.summary = payload.summary || investigator.summary
  }
  if (event.type === 'subagent.artifact.updated') {
    const subagent = upsertSubagent(next, payload.subagent_id, {
      id: payload.subagent_id,
      investigator_id: payload.investigator_id || '',
      artifacts: {},
      tool_events: [],
      budget: {},
    })
    subagent.artifacts = subagent.artifacts || {}
    subagent.artifact_meta = subagent.artifact_meta || {}
    subagent.artifacts[payload.artifact] = payload.content || ''
    subagent.artifact_meta[payload.artifact] = { exists: true, char_count: payload.char_count || 0 }
    markRunning(subagent)
    linkSubagent(next, subagent.investigator_id || payload.investigator_id, subagent.id)
  }
  if (event.type?.startsWith('subagent.tool')) {
    const subagent = upsertSubagent(next, payload.subagent_id, {
      id: payload.subagent_id,
      investigator_id: payload.investigator_id || '',
      artifacts: {},
      tool_events: [],
      budget: {},
    })
    markRunning(subagent)
    subagent.tool_events = [...(subagent.tool_events || []), compactToolEvent(event, payload)].slice(-1200)
    linkSubagent(next, subagent.investigator_id || payload.investigator_id, subagent.id)
  }
  if (event.type === 'subagent.budget') {
    const subagent = upsertSubagent(next, payload.subagent_id, {
      id: payload.subagent_id,
      artifacts: {},
      tool_events: [],
      budget: {},
    })
    subagent.budget = { ...(subagent.budget || {}), ...snakeBudget(payload) }
  }
  if (event.type === 'subagent.completed') {
    const subagent = upsertSubagent(next, payload.subagent_id, {
      id: payload.subagent_id,
      status: payload.error ? 'error' : 'completed',
      artifacts: {},
      tool_events: [],
      budget: {},
    })
    subagent.status = payload.error ? 'error' : 'completed'
    subagent.summary = payload.summary || subagent.summary
    subagent.error = payload.error || subagent.error
    subagent.workspace_path = payload.workspace_path || subagent.workspace_path
    if (payload.budget) subagent.budget = { ...(subagent.budget || {}), ...snakeBudget(payload.budget) }
  }
  if (event.type === 'cross_investigator.completed') {
    for (const [key, content] of Object.entries(payload.artifacts || {})) {
      next.shared[key] = { path: `shared/${key}.md`, content }
    }
  }
  if (event.type === 'critique.completed') {
    const existing = next.critiques.find((item) => item.critic_id === payload.critic_id)
    if (existing) {
      existing.status = 'completed'
      existing.markdown = payload.critique_md || existing.markdown
    } else {
      next.critiques.push({ critic_id: payload.critic_id, lens: payload.lens, status: 'completed', markdown: payload.critique_md || '' })
    }
  }
  return withCounts(next)
}

export default function ResearchDeepDive() {
  const { runId } = useParams()
  const [state, dispatch] = useReducer(reducer, initialState)
  const refreshTimer = useRef(null)

  const loadSnapshot = useCallback(async () => {
    try {
      const snapshot = await api.research.snapshot(runId)
      dispatch({ type: 'SNAPSHOT', snapshot })
    } catch (err) {
      dispatch({ type: 'CONNECTION_ERROR', error: err.message || 'Failed to load research run' })
    }
  }, [runId])

  const scheduleSnapshotRefresh = useCallback((event) => {
    const type = event?.type
    const shouldCatchUp = !event || [
      'subagent.completed',
      'investigator.synthesized',
      'cross_investigator.completed',
      'critique.completed',
      'run.finalized',
      'run.error',
    ].includes(type)
    if (!shouldCatchUp) return
    if (refreshTimer.current) window.clearTimeout(refreshTimer.current)
    refreshTimer.current = window.setTimeout(() => {
      loadSnapshot()
    }, type === 'run.finalized' || type === 'run.error' ? 250 : 700)
  }, [loadSnapshot])

  useEffect(() => {
    loadSnapshot()
  }, [loadSnapshot])

  useEffect(() => () => {
    if (refreshTimer.current) window.clearTimeout(refreshTimer.current)
  }, [])

  useResearchStream(runId, dispatch, scheduleSnapshotRefresh)

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
          <Pill label={`${counts.completed_subagents || 0}/${counts.subagents || 0} researchers`} />
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
        <div className="hidden h-full min-h-0 w-[430px] shrink-0 overflow-hidden lg:block">
          <InspectorDrawer
            snapshot={state.snapshot}
            selected={state.selected}
            onSelect={(selected) => dispatch({ type: 'SELECT', selected })}
          />
        </div>
      </div>

      <div className="block h-[42vh] min-h-[260px] overflow-hidden border-t border-white/10 lg:hidden">
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
  const budget = {}
  assignIfPresent(budget, 'research_used', value.research_used ?? value.researchUsed)
  assignIfPresent(budget, 'research_max', value.research_max ?? value.researchMax)
  assignIfPresent(budget, 'workspace_used', value.workspace_used ?? value.workspaceUsed)
  assignIfPresent(budget, 'workspace_max', value.workspace_max ?? value.workspaceMax)
  assignIfPresent(budget, 'llm_steps', value.llm_steps ?? value.llmSteps)
  return budget
}

function assignIfPresent(target, key, value) {
  if (value !== undefined && value !== null) target[key] = value
}

function emptySnapshot(runId) {
  return {
    metadata: { run_id: runId || 'research run', status: 'connecting', stage: 'connecting' },
    investigators: [],
    subagents: [],
    shared: {},
    critiques: [],
    final_report: { available: false, path: 'final/research_deep_dive_report.md', markdown: '' },
    counts: {},
  }
}

function upsertInvestigator(snapshot, id, defaults = {}) {
  if (!id) return defaults
  let item = snapshot.investigators.find((investigator) => investigator.id === id)
  if (!item) {
    item = { status: 'planned', subagent_ids: [], ...defaults, id }
    snapshot.investigators.push(item)
  } else {
    Object.assign(item, usefulDefaults(defaults))
  }
  item.subagent_ids = item.subagent_ids || []
  return item
}

function upsertSubagent(snapshot, id, defaults = {}) {
  if (!id) return defaults
  let item = snapshot.subagents.find((subagent) => subagent.id === id)
  if (!item) {
    item = { status: 'planned', artifacts: {}, artifact_meta: {}, tool_events: [], budget: {}, ...defaults, id }
    snapshot.subagents.push(item)
  } else {
    Object.assign(item, usefulDefaults(defaults))
    item.artifacts = item.artifacts || {}
    item.artifact_meta = item.artifact_meta || {}
    item.tool_events = item.tool_events || []
    item.budget = item.budget || {}
  }
  return item
}

function usefulDefaults(defaults) {
  return Object.fromEntries(
    Object.entries(defaults).filter(([, value]) => {
      if (value === undefined || value === null || value === '') return false
      if (Array.isArray(value) && value.length === 0) return false
      if (typeof value === 'object' && Object.keys(value).length === 0) return false
      return true
    })
  )
}

function linkSubagent(snapshot, investigatorId, subagentId) {
  if (!investigatorId || !subagentId) return
  const investigator = upsertInvestigator(snapshot, investigatorId, {
    id: investigatorId,
    section_title: investigatorId,
    subagent_ids: [],
  })
  investigator.subagent_ids = unique([...(investigator.subagent_ids || []), subagentId])
}

function markRunning(item) {
  if (!['completed', 'error'].includes(item.status)) item.status = 'running'
}

function unique(values) {
  return [...new Set(values.filter(Boolean))]
}

function compactToolEvent(event, payload) {
  const entry = payload.trace_entry || {}
  return {
    ...entry,
    type: entry.type || event.type,
    ts: entry.ts || event.ts,
    step: entry.step ?? payload.step,
    tool_name: entry.tool_name || payload.tool_name,
    arguments: entry.arguments || payload.arguments || {},
    action: entry.action || payload.action || {},
    result_preview: entry.result_preview || payload.result_preview || '',
    reason: entry.reason || payload.reason || '',
    error: entry.error || payload.error || '',
    error_type: entry.error_type || payload.error_type || '',
    research_tool_calls_used: entry.research_tool_calls_used ?? payload.research_tool_calls_used,
    workspace_tool_calls_used: entry.workspace_tool_calls_used ?? payload.workspace_tool_calls_used,
  }
}

function withCounts(snapshot) {
  snapshot.counts = {
    investigators: snapshot.investigators?.length || 0,
    subagents: snapshot.subagents?.length || 0,
    completed_subagents: (snapshot.subagents || []).filter((item) => item.status === 'completed').length,
    syntheses: (snapshot.investigators || []).filter((item) => item.synthesis_md).length,
    critiques: (snapshot.critiques || []).filter((item) => item.status === 'completed').length,
    tool_events: (snapshot.subagents || []).reduce((sum, item) => sum + (item.tool_events?.length || 0), 0),
  }
  return snapshot
}
