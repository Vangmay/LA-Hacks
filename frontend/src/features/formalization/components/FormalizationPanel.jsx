import { useEffect, useReducer, useState } from 'react'
import { formalizationApi } from '../api'
import { formalizationReducer, initialFormalizationState } from '../reducer'
import { useFormalizationStream } from '../hooks/useFormalizationStream'
import FormalizationDashboard from './FormalizationDashboard'
import StatusBadge from './StatusBadge'
import SummaryStrip from './SummaryStrip'

export default function FormalizationPanel({ jobId, atom }) {
  const [state, dispatch] = useReducer(formalizationReducer, initialFormalizationState)
  const [isStarting, setIsStarting] = useState(false)
  const [isRefreshing, setIsRefreshing] = useState(false)
  const [expanded, setExpanded] = useState(false)
  useFormalizationStream(state.runId, dispatch)

  useEffect(() => {
    if (!state.runId || !['complete', 'error'].includes(state.status)) return
    refreshRun()
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [state.runId, state.status])

  const selectedReviewAtomId = atom?.id || atom?.atom_id
  const busy = isStarting || ['queued', 'running', 'building_context', 'llm_thinking', 'axle_running'].includes(state.status)

  async function startSelected() {
    if (!selectedReviewAtomId) return
    await start(() => formalizationApi.startAtom(jobId, selectedReviewAtomId))
  }

  async function startAll() {
    await start(() => formalizationApi.start(jobId))
  }

  async function start(fn) {
    setIsStarting(true)
    try {
      const response = await fn()
      dispatch({ type: 'START_RESPONSE', payload: response })
      setExpanded(true)
    } catch (err) {
      dispatch({ type: 'ERROR', error: err.message || 'Failed to start formalization' })
    } finally {
      setIsStarting(false)
    }
  }

  async function refreshRun() {
    if (!state.runId) return
    setIsRefreshing(true)
    try {
      const snapshot = await formalizationApi.run(state.runId)
      dispatch({ type: 'RUN_SNAPSHOT', payload: snapshot })
    } catch (err) {
      dispatch({ type: 'ERROR', error: err.message || 'Failed to refresh formalization run' })
    } finally {
      setIsRefreshing(false)
    }
  }

  function handleDashboardSelect(selected) {
    if (selected?.kind === 'atom') {
      dispatch({ type: 'SELECT_ATOM', atomId: selected.id })
    } else {
      dispatch({ type: 'SELECT', selected })
    }
  }

  return (
    <section className="rounded border border-white/10 bg-[#0D1017] p-3">
      <div className="mb-3 flex items-center gap-2">
        <div>
          <div className="text-[10px] uppercase tracking-wider text-white/45">Formalize</div>
          <div className="text-sm font-medium text-white/85">AXLE Verification</div>
        </div>
        <span className="ml-auto"><StatusBadge value={state.status} /></span>
      </div>

      <div className="mb-3 flex flex-wrap gap-2">
        <button
          onClick={startSelected}
          disabled={!selectedReviewAtomId || busy}
          className="rounded border border-cyan-400/30 bg-cyan-500/10 px-3 py-1.5 text-xs text-cyan-100 hover:bg-cyan-500/20 disabled:cursor-not-allowed disabled:opacity-40"
        >
          Run selected
        </button>
        <button
          onClick={startAll}
          disabled={busy}
          className="rounded border border-white/10 bg-white/5 px-3 py-1.5 text-xs text-white/75 hover:bg-white/10 disabled:cursor-not-allowed disabled:opacity-40"
        >
          Run reviewable
        </button>
        {state.runId && (
          <button
            onClick={refreshRun}
            disabled={isRefreshing}
            className="rounded border border-white/10 bg-white/5 px-3 py-1.5 text-xs text-white/55 hover:bg-white/10 disabled:opacity-40"
          >
            Refresh
          </button>
        )}
        {state.runId && (
          <button
            onClick={() => setExpanded(true)}
            className="rounded border border-[#67E8F9]/30 bg-[#67E8F9]/10 px-3 py-1.5 text-xs text-[#67E8F9] hover:bg-[#67E8F9]/15"
          >
            Live dashboard
          </button>
        )}
      </div>

      {state.error && (
        <div className="mb-3 rounded border border-red-400/20 bg-red-500/10 p-2 text-xs text-red-200">
          {state.error}
        </div>
      )}

      {state.runId && (
        <div className="mb-3 space-y-3">
          <div className="truncate font-mono text-[10px] text-white/35">run {state.runId}</div>
          <div className="grid grid-cols-2 gap-2 text-[11px]">
            <MiniStat label="Atoms" value={`${state.counts?.completed_atoms || 0}/${state.counts?.atoms || 0}`} />
            <MiniStat label="Active" value={state.counts?.running_atoms || 0} />
            <MiniStat label="Tool calls" value={state.counts?.tool_calls || 0} />
            <MiniStat label="Workers" value={state.runtime?.parallelism || '-'} />
          </div>
          <SummaryStrip summary={state.summary} />
          <div className="rounded border border-white/10 bg-black/10 p-2 text-[11px] leading-relaxed text-white/55">
            {(state.runtime?.model_name || 'formalization model')} - Lean {state.runtime?.lean_environment || 'environment'} - AXLE concurrency {state.runtime?.axle_max_concurrency || '-'}
          </div>
        </div>
      )}

      {state.runId && (
        <div className="mt-3 flex flex-wrap gap-2">
          <a
            href={formalizationApi.leanUrl(state.runId)}
            target="_blank"
            rel="noreferrer"
            className="inline-flex rounded border border-white/10 bg-white/5 px-3 py-1.5 text-xs text-white/65 hover:bg-white/10"
          >
            Open merged Lean
          </a>
        </div>
      )}

      {expanded && (
        <FormalizationDashboard
          state={state}
          leanUrl={state.runId ? formalizationApi.leanUrl(state.runId) : ''}
          onClose={() => setExpanded(false)}
          onSelect={handleDashboardSelect}
        />
      )}
    </section>
  )
}

function MiniStat({ label, value }) {
  return (
    <div className="rounded border border-white/10 bg-black/10 p-2">
      <div className="text-[9px] uppercase tracking-wider text-white/35">{label}</div>
      <div className="mt-1 font-mono text-white/75">{value}</div>
    </div>
  )
}
