import { useState } from 'react'

export default function FormalizationEventTicker({ events = [], onSelect }) {
  const [open, setOpen] = useState(true)
  const visibleEvents = events.filter((event) => event.event_type !== 'run_snapshot')
  const recent = visibleEvents.slice(-50).reverse()

  return (
    <div className="border-t border-white/10 bg-[#0D1017]">
      <button
        type="button"
        onClick={() => setOpen(!open)}
        className="flex w-full items-center gap-3 px-4 py-2 text-left text-[11px] uppercase tracking-wider text-white/50 hover:text-white"
      >
        <span className="h-1.5 w-1.5 rounded-full bg-[#67E8F9]" />
        {visibleEvents.length} live formalization updates
        <span className="ml-auto">{open ? 'Collapse' : 'Expand'}</span>
      </button>
      {open && (
        <div className="flex max-h-24 gap-2 overflow-x-auto px-4 pb-3">
          {recent.length === 0 && <div className="text-xs text-white/35">Waiting for Lean/AXLE events...</div>}
          {recent.map((event, index) => (
            <button
              key={event.event_id || `${event.event_type}-${index}`}
              type="button"
              onClick={() => onSelect?.(event)}
              className="shrink-0 rounded border border-white/10 bg-white/[0.03] px-3 py-2 text-left text-xs text-white/70 hover:border-[#67E8F9]/40 hover:text-white"
            >
              <div className="font-mono text-[10px] text-white/35">
                {event.timestamp ? new Date(event.timestamp).toLocaleTimeString() : ''}
              </div>
              <div className="max-w-[340px] truncate">{eventLine(event)}</div>
            </button>
          ))}
        </div>
      )}
    </div>
  )
}

function eventLine(event) {
  const payload = event.payload || {}
  const atom = shortAtom(event.atom_id || payload.atom_id)
  if (event.event_type === 'run_started') return `Run started with ${payload.selected_atom_ids?.length || 0} atoms`
  if (event.event_type === 'atom_queued') return `${atom} queued`
  if (event.event_type === 'atom_context_built') return `${atom} context built`
  if (event.event_type === 'llm_thought') return `${atom} model streamed reasoning`
  if (event.event_type === 'tool_call_started') return `${atom} called ${formatTool(payload.tool_name)}`
  if (event.event_type === 'tool_call_complete') return `${atom} finished ${formatTool(payload.tool_name)}`
  if (event.event_type === 'axle_check_result') return `${atom} AXLE check ${payload.okay ? 'passed' : 'reported errors'}`
  if (event.event_type === 'axle_verify_result') return `${atom} proof verification ${payload.okay ? 'passed' : 'needs repair'}`
  if (event.event_type === 'artifact_recorded') return `${atom} recorded ${formatTool(payload.kind)} artifact`
  if (event.event_type === 'artifact_updated') return `${atom} updated Lean artifact status`
  if (event.event_type === 'atom_verdict') return `${atom} verdict: ${formatTool(payload.label)}`
  if (event.event_type === 'atom_error') return `${atom} failed`
  if (event.event_type === 'run_complete') return 'Formalization run complete'
  if (event.event_type === 'run_error') return 'Formalization run failed'
  return formatTool(event.event_type || 'event')
}

function shortAtom(value) {
  if (!value) return 'Atom'
  return String(value).replace(/^atom_?/, 'atom ')
}

function formatTool(value) {
  return String(value || '').replaceAll('_', ' ')
}
