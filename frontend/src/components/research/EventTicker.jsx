import { useState } from 'react'

function eventLine(event) {
  const payload = event.payload || {}
  if (event.type === 'run.snapshot') return 'Loaded latest workspace snapshot'
  if (event.type === 'run.started') return 'Run started'
  if (event.type === 'investigator.planned') return `Planned investigator: ${payload.section_title || payload.investigator_id || 'section'}`
  if (event.type === 'subagent.planned') return `Planned researcher: ${payload.taste?.label || shortId(payload.subagent_id)}`
  if (event.type === 'subagent.started') return `Researcher started: ${shortId(payload.subagent_id)}`
  if (event.type === 'subagent.completed') return `Researcher finished: ${shortId(payload.subagent_id)}`
  if (event.type === 'subagent.budget') {
    return `${shortId(payload.subagent_id)} used ${payload.research_used ?? 0}/${payload.research_max ?? '-'} API calls`
  }
  if (event.type === 'subagent.tool.requested') {
    return `${shortId(payload.subagent_id)} called ${formatTool(payload.tool_name)}`
  }
  if (event.type === 'subagent.tool.result') {
    return `${shortId(payload.subagent_id)} received ${formatTool(payload.tool_name)} results`
  }
  if (event.type === 'subagent.tool.error') {
    return `${shortId(payload.subagent_id)} hit a tool error`
  }
  if (event.type === 'subagent.tool.rejected') {
    return `${shortId(payload.subagent_id)} corrected an invalid action`
  }
  if (event.type === 'subagent.artifact.updated') {
    return `${shortId(payload.subagent_id)} updated ${formatTool(payload.artifact || 'artifact')}`
  }
  if (event.type === 'investigator.synthesized') return `Investigator synthesis ready: ${shortId(payload.investigator_id)}`
  if (event.type === 'cross_investigator.completed') return 'Shared synthesis ready'
  if (event.type === 'critique.completed') return `Critique ready: ${formatTool(payload.critic_id || payload.lens || 'critic')}`
  if (event.type === 'stage.entered') return `Started ${stageLabel(payload.stage)}`
  if (event.type === 'stage.completed') return `Finished ${stageLabel(payload.stage)}`
  if (event.type === 'run.finalized') return 'Final report ready'
  if (event.type === 'run.error') return 'Run failed'
  return formatTool(event.type || 'event')
}

export default function EventTicker({ events = [], onSelect }) {
  const [open, setOpen] = useState(true)
  const visibleEvents = events.filter((event) => event.type !== 'run.snapshot')
  const recent = visibleEvents.slice(-40).reverse()

  return (
    <div className="border-t border-white/10 bg-[#0D1017]">
      <button
        type="button"
        onClick={() => setOpen(!open)}
        className="flex w-full items-center gap-3 px-4 py-2 text-left text-[11px] uppercase tracking-wider text-white/50 hover:text-white"
      >
        <span className="h-1.5 w-1.5 rounded-full bg-[#67E8F9]" />
        {visibleEvents.length} live activity updates
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

function shortId(value) {
  if (!value) return 'Researcher'
  return String(value).replace(/^.*?(investigator_\d+_[^_]+_)?subagent_/, 'researcher ').replaceAll('_', ' ')
}

function formatTool(value) {
  return String(value || 'tool').replaceAll('_', ' ')
}

function stageLabel(stage) {
  const labels = {
    bootstrap: 'workspace setup',
    investigator_planning: 'investigator planning',
    subagent_research: 'researcher search',
    investigator_synthesis: 'investigator synthesis',
    cross_investigator_deep_dive: 'shared synthesis',
    critique: 'critique',
    finalization: 'final report',
  }
  return labels[stage] || formatTool(stage || 'stage')
}
