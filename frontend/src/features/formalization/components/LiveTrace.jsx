import { FORMALIZATION_EVENTS } from '../types'
import ToolCallRow from './ToolCallRow'

export default function LiveTrace({ events, selectedAtomId }) {
  const filtered = selectedAtomId ? events.filter(e => !e.atom_id || e.atom_id === selectedAtomId) : events
  if (!filtered.length) {
    return <div className="text-xs text-white/45">Trace events appear here while AXLE runs.</div>
  }
  return (
    <div className="max-h-56 space-y-2 overflow-auto rounded border border-white/10 bg-black/10 p-2">
      {filtered.map(event => (
        <TraceRow key={event.event_id} event={event} />
      ))}
    </div>
  )
}

function TraceRow({ event }) {
  const timestamp = event.timestamp ? new Date(event.timestamp).toLocaleTimeString() : ''
  if ([FORMALIZATION_EVENTS.TOOL_CALL_STARTED, FORMALIZATION_EVENTS.TOOL_CALL_COMPLETE].includes(event.event_type)) {
    return <ToolCallRow event={event} />
  }
  if (event.event_type === FORMALIZATION_EVENTS.LLM_THOUGHT) {
    return (
      <div className="rounded border border-white/5 bg-white/[0.03] px-2 py-1 text-[11px] italic text-white/60">
        <span className="mr-2 font-mono not-italic text-white/35">{timestamp}</span>
        {event.payload?.delta}
      </div>
    )
  }
  return (
    <div className="rounded border border-white/5 bg-white/[0.03] px-2 py-1 text-[11px] text-white/60">
      <span className="mr-2 font-mono text-white/35">{timestamp}</span>
      <span className="font-mono">{event.event_type}</span>
      {event.atom_id && <span className="ml-2 text-white/35">{event.atom_id}</span>}
    </div>
  )
}
