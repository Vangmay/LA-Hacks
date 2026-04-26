import FormalizationEventTicker from './FormalizationEventTicker'
import FormalizationGraph from './FormalizationGraph'
import FormalizationInspector from './FormalizationInspector'
import StatusBadge from './StatusBadge'

export default function FormalizationDashboard({ state, onSelect, onClose, leanUrl }) {
  const meta = state.runtime || {}

  function handleTickerSelect(event) {
    const atomId = event.atom_id || event.payload?.atom_id
    if (atomId) onSelect?.({ kind: 'atom', id: atomId })
    else onSelect?.({ kind: 'run', id: state.runId || 'run' })
  }

  return (
    <div className="fixed inset-4 z-50 flex min-h-0 flex-col overflow-hidden rounded-md border border-white/10 bg-[#0A0C10] text-[#E4E7F0] shadow-2xl">
      <header className="z-10 flex items-center gap-4 border-b border-white/10 bg-[#131720] px-5 py-3">
        <button
          type="button"
          onClick={onClose}
          className="rounded border border-white/10 bg-white/[0.03] px-3 py-1.5 text-xs text-white/65 hover:text-white"
        >
          Close
        </button>
        <div className="min-w-0 flex-1">
          <div className="truncate font-mono text-xs text-white/45">{state.runId || 'No run started'}</div>
          <div className="truncate text-sm font-semibold">Lean formalization and AXLE verification</div>
        </div>
        <div className="hidden items-center gap-2 text-xs text-white/55 md:flex">
          <StatusBadge value={state.status} />
          <Pill label={`${state.counts?.completed_atoms || 0}/${state.counts?.atoms || 0} atoms`} />
          <Pill label={`${state.counts?.running_atoms || 0} active`} tone="cyan" />
          <Pill label={`${state.counts?.tool_calls || 0} tool calls`} />
          <Pill label={`${meta.parallelism || '-'} workers`} />
          {leanUrl && (
            <a
              href={leanUrl}
              target="_blank"
              rel="noreferrer"
              className="rounded border border-[#67E8F9]/30 bg-[#67E8F9]/10 px-2.5 py-1 text-[#67E8F9] hover:bg-[#67E8F9]/15"
            >
              Lean
            </a>
          )}
        </div>
      </header>

      {state.error && <div className="border-b border-red-500/20 bg-red-500/10 px-5 py-2 text-sm text-red-200">{state.error}</div>}

      <div className="flex min-h-0 flex-1">
        <main className="min-w-0 flex-1 bg-[#0A0C10]">
          <FormalizationGraph state={state} selected={state.selected} onSelect={onSelect} />
        </main>
        <div className="hidden h-full min-h-0 w-[460px] shrink-0 overflow-hidden lg:block">
          <FormalizationInspector state={state} selected={state.selected} onSelect={onSelect} />
        </div>
      </div>

      <div className="block h-[42vh] min-h-[280px] overflow-hidden border-t border-white/10 lg:hidden">
        <FormalizationInspector state={state} selected={state.selected} onSelect={onSelect} />
      </div>

      <FormalizationEventTicker events={state.events} onSelect={handleTickerSelect} />
    </div>
  )
}

function Pill({ label, tone = 'slate' }) {
  const colors = {
    cyan: 'border-[#67E8F9]/30 bg-[#67E8F9]/10 text-[#67E8F9]',
    slate: 'border-white/10 bg-white/[0.03] text-white/55',
  }
  return <span className={`rounded border px-2.5 py-1 ${colors[tone]}`}>{label}</span>
}
