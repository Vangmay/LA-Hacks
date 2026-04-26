import { useState } from 'react'

function eventLine(event) {
  const payload = event.payload || {}
  if (event.type?.startsWith('subagent.tool')) {
    return `${payload.subagent_id || 'subagent'} -> ${payload.tool_name || 'tool'}`
  }
  if (event.type === 'subagent.artifact.updated') {
    return `${payload.subagent_id || 'subagent'} wrote ${payload.artifact || 'artifact'}`
  }
  if (event.type === 'stage.entered') return `Stage entered: ${payload.stage}`
  if (event.type === 'stage.completed') return `Stage completed: ${payload.stage}`
  if (event.type === 'run.finalized') return 'Final report ready'
  return event.type || 'event'
}

export default function EventTicker({ events = [], onSelect }) {
  const [open, setOpen] = useState(true)
  const recent = events.slice(-40).reverse()

  return (
    <div className="border-t border-white/10 bg-[#0D1017]">
      <button
        type="button"
        onClick={() => setOpen(!open)}
        className="flex w-full items-center gap-3 px-4 py-2 text-left text-[11px] uppercase tracking-wider text-white/50 hover:text-white"
      >
        <span className="h-1.5 w-1.5 rounded-full bg-[#67E8F9]" />
        {events.length} live events
        <span className="ml-auto">{open ? 'Collapse' : 'Expand'}</span>
      </button>
      {open && (
        <div className="flex max-h-24 gap-2 overflow-x-auto px-4 pb-3">
          {recent.length === 0 && <div className="text-xs text-white/35">Waiting for research events...</div>}
          {recent.map((event) => (
            <button
              key={event.event_id}
              type="button"
              onClick={() => onSelect?.(event)}
              className="shrink-0 rounded border border-white/10 bg-white/[0.03] px-3 py-2 text-left text-xs text-white/70 hover:border-[#67E8F9]/40 hover:text-white"
            >
              <div className="font-mono text-[10px] text-white/35">
                {event.ts ? new Date(event.ts).toLocaleTimeString() : ''}
              </div>
              <div className="max-w-[320px] truncate">{eventLine(event)}</div>
            </button>
          ))}
        </div>
      )}
    </div>
  )
}
