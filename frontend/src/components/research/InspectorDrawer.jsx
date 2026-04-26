import { useMemo, useState } from 'react'
import ResearchMarkdown from './ResearchMarkdown'

const ARTIFACT_TABS = ['findings', 'papers', 'proposal_seeds', 'memory', 'queries', 'handoff']

export default function InspectorDrawer({ snapshot, selected, onSelect }) {
  const [tab, setTab] = useState('overview')
  const target = useMemo(() => resolveSelection(snapshot, selected), [snapshot, selected])

  if (!target) {
    return (
      <aside className="min-h-0 overflow-y-auto border-l border-white/10 bg-[#131720]">
        <RunOverview snapshot={snapshot} onSelect={onSelect} />
      </aside>
    )
  }

  return (
    <aside className="min-h-0 overflow-y-auto border-l border-white/10 bg-[#131720]">
      <div className="sticky top-0 z-10 border-b border-white/10 bg-[#131720]/95 px-4 py-3 backdrop-blur">
        <div className="font-mono text-[10px] uppercase tracking-wider text-white/40">{target.kind}</div>
        <div className="mt-1 line-clamp-2 text-sm font-semibold text-[#E4E7F0]">{target.title}</div>
        <div className="mt-2 flex flex-wrap gap-2">
          {tabsFor(target).map((item) => (
            <button
              key={item}
              type="button"
              onClick={() => setTab(item)}
              className={`rounded border px-2.5 py-1 text-xs capitalize transition-colors ${tab === item ? 'border-[#67E8F9]/50 bg-[#67E8F9]/10 text-[#67E8F9]' : 'border-white/10 bg-white/[0.03] text-white/55 hover:text-white'}`}
            >
              {item.replaceAll('_', ' ')}
            </button>
          ))}
        </div>
      </div>
      <div className="p-4">
        <SelectionContent target={target} tab={tab} snapshot={snapshot} onSelect={onSelect} />
      </div>
    </aside>
  )
}

function RunOverview({ snapshot, onSelect }) {
  const meta = snapshot?.metadata || {}
  const counts = snapshot?.counts || {}
  return (
    <div className="p-4">
      <div className="font-mono text-[10px] uppercase tracking-wider text-white/40">Run overview</div>
      <h2 className="mt-2 text-lg font-semibold">{meta.run_id || 'Research run'}</h2>
      <div className="mt-4 grid grid-cols-2 gap-2 text-xs">
        <Stat label="Status" value={meta.status || 'loading'} />
        <Stat label="Objective" value={meta.research_objective || 'unknown'} />
        <Stat label="Investigators" value={counts.investigators || 0} />
        <Stat label="Subagents" value={`${counts.completed_subagents || 0}/${counts.subagents || 0}`} />
        <Stat label="Tool events" value={counts.tool_events || 0} />
        <Stat label="Critiques" value={counts.critiques || 0} />
      </div>
      <div className="mt-5 space-y-2">
        {(snapshot?.investigators || []).map((investigator) => (
          <button
            key={investigator.id}
            type="button"
            onClick={() => onSelect?.({ kind: 'investigator', id: investigator.id })}
            className="w-full rounded border border-white/10 bg-[#0D1017] px-3 py-2 text-left hover:border-[#67E8F9]/40"
          >
            <div className="text-sm font-medium">{investigator.section_title}</div>
            <div className="mt-1 text-xs text-white/45">{investigator.subagent_ids?.length || 0} subagents · {investigator.status}</div>
          </button>
        ))}
      </div>
      {snapshot?.final_report?.available && (
        <div className="mt-5 rounded border border-white/10 bg-[#0D1017] p-3">
          <div className="mb-2 text-xs uppercase tracking-wider text-white/40">Final report</div>
          <ResearchMarkdown>{snapshot.final_report.markdown}</ResearchMarkdown>
        </div>
      )}
    </div>
  )
}

function SelectionContent({ target, tab, snapshot, onSelect }) {
  if (target.kind === 'subagent') {
    if (tab === 'persona') return <PersonaCard taste={target.item.taste} />
    if (tab === 'tools') return <ToolTimeline events={target.item.tool_events || []} />
    if (ARTIFACT_TABS.includes(tab)) return <ResearchMarkdown>{target.item.artifacts?.[tab]}</ResearchMarkdown>
    return <SubagentOverview item={target.item} />
  }

  if (target.kind === 'investigator' || target.kind === 'synthesis') {
    return (
      <div className="space-y-4">
        <OverviewRows rows={[['Status', target.item.status], ['Workspace', target.item.workspace_path], ['Subagents', target.item.subagent_ids?.length || 0]]} />
        <div className="space-y-2">
          {(target.item.subagent_ids || []).map((id) => (
            <button key={id} type="button" onClick={() => onSelect?.({ kind: 'subagent', id })} className="w-full rounded border border-white/10 bg-[#0D1017] px-3 py-2 text-left text-xs hover:border-[#67E8F9]/40">
              {id}
            </button>
          ))}
        </div>
        <ResearchMarkdown>{target.item.synthesis_md}</ResearchMarkdown>
      </div>
    )
  }

  if (target.kind === 'critique') return <ResearchMarkdown>{target.item.markdown}</ResearchMarkdown>
  if (target.kind === 'final') return <ResearchMarkdown>{snapshot?.final_report?.markdown}</ResearchMarkdown>
  if (target.kind === 'shared') return <ResearchMarkdown>{target.item.content}</ResearchMarkdown>
  return <ResearchMarkdown>{target.markdown}</ResearchMarkdown>
}

function SubagentOverview({ item }) {
  return (
    <div className="space-y-4">
      <OverviewRows
        rows={[
          ['Status', item.status],
          ['Investigator', item.investigator_id],
          ['Section', item.section_title],
          ['Persona', item.taste?.label || item.id],
          ['Archetype', item.taste?.archetype_label || ''],
          ['Workspace', item.workspace_path],
          ['Budget', `${item.budget?.research_used || 0}/${item.budget?.research_max || item.max_tool_calls || 0} research`],
        ]}
      />
      {item.summary && (
        <div className="rounded border border-white/10 bg-[#0D1017] p-3 text-sm leading-relaxed text-white/70">
          {item.summary}
        </div>
      )}
    </div>
  )
}

function PersonaCard({ taste = {} }) {
  const sections = [
    ['Worldview', taste.worldview],
    ['Best for', taste.best_for],
    ['Search biases', taste.search_biases],
    ['Typical queries', taste.typical_queries],
    ['Evidence preferences', taste.evidence_preferences],
    ['Proposal style', taste.proposal_style],
    ['Failure modes', taste.failure_modes_to_watch],
    ['Must not do', taste.must_not_do],
    ['Counterbalance', taste.required_counterbalance],
  ]
  return (
    <div className="space-y-3">
      <div className="rounded border border-[#b388ff]/30 bg-[#b388ff]/10 p-3">
        <div className="text-sm font-semibold">{taste.label || 'Persona'}</div>
        <div className="mt-1 text-xs text-white/50">{taste.archetype_label}</div>
        <div className="mt-2 flex flex-wrap gap-1">
          {(taste.diversity_roles || []).map((role) => (
            <span key={role} className="rounded bg-white/10 px-2 py-1 text-[10px] text-white/60">{role}</span>
          ))}
        </div>
      </div>
      {sections.map(([label, value]) => (
        <details key={label} open className="rounded border border-white/10 bg-[#0D1017] p-3">
          <summary className="cursor-pointer text-xs font-semibold uppercase tracking-wider text-white/50">{label}</summary>
          <div className="mt-2 text-sm leading-relaxed text-white/70">
            {Array.isArray(value) ? (
              <div className="flex flex-wrap gap-1.5">{value.map((item) => <span key={item} className="rounded bg-white/5 px-2 py-1 text-xs">{item}</span>)}</div>
            ) : (
              value || 'None recorded.'
            )}
          </div>
        </details>
      ))}
    </div>
  )
}

function ToolTimeline({ events }) {
  const [filter, setFilter] = useState('all')
  const filtered = events.filter((event) => {
    if (filter === 'all') return true
    if (filter === 'errors') return event.type === 'tool_error' || event.type === 'rejected_action'
    if (filter === 'workspace') return String(event.tool_name || '').includes('workspace')
    if (filter === 'search') return !String(event.tool_name || '').includes('workspace')
    return true
  })
  return (
    <div>
      <div className="mb-3 flex flex-wrap gap-2">
        {['all', 'search', 'workspace', 'errors'].map((item) => (
          <button key={item} type="button" onClick={() => setFilter(item)} className={`rounded border px-2 py-1 text-xs ${filter === item ? 'border-[#67E8F9]/50 text-[#67E8F9]' : 'border-white/10 text-white/55'}`}>
            {item}
          </button>
        ))}
      </div>
      <div className="space-y-2">
        {filtered.map((event, idx) => (
          <details key={`${event.ts}-${idx}`} className="rounded border border-white/10 bg-[#0D1017] p-3">
            <summary className="cursor-pointer text-xs">
              <span className="mr-2 font-mono text-white/35">{event.step || idx + 1}</span>
              <span className={badgeColor(event.type)}>{event.type}</span>
              <span className="ml-2 text-white/75">{event.tool_name || event.action?.action || 'action'}</span>
            </summary>
            <pre className="mt-3 max-h-56 overflow-auto rounded bg-black/25 p-3 text-[11px] text-white/70">
              {JSON.stringify({ arguments: event.arguments, action: event.action, result_preview: event.result_preview, reason: event.reason, error: event.error }, null, 2)}
            </pre>
          </details>
        ))}
      </div>
    </div>
  )
}

function OverviewRows({ rows }) {
  return (
    <div className="divide-y divide-white/5 rounded border border-white/10 bg-[#0D1017]">
      {rows.map(([label, value]) => (
        <div key={label} className="grid grid-cols-[110px_1fr] gap-3 px-3 py-2 text-xs">
          <div className="text-white/35">{label}</div>
          <div className="min-w-0 break-words text-white/70">{value || '-'}</div>
        </div>
      ))}
    </div>
  )
}

function Stat({ label, value }) {
  return (
    <div className="rounded border border-white/10 bg-[#0D1017] p-3">
      <div className="text-[10px] uppercase tracking-wider text-white/35">{label}</div>
      <div className="mt-1 truncate font-mono text-sm text-[#E4E7F0]">{value}</div>
    </div>
  )
}

function badgeColor(type) {
  if (type === 'tool_error') return 'rounded bg-red-500/15 px-1.5 py-0.5 text-red-300'
  if (type === 'rejected_action') return 'rounded bg-amber-500/15 px-1.5 py-0.5 text-amber-300'
  if (type === 'tool_result') return 'rounded bg-green-500/15 px-1.5 py-0.5 text-green-300'
  return 'rounded bg-cyan-500/15 px-1.5 py-0.5 text-cyan-300'
}

function tabsFor(target) {
  if (target.kind === 'subagent') return ['overview', 'persona', 'tools', ...ARTIFACT_TABS]
  return ['overview']
}

function resolveSelection(snapshot, selected) {
  if (!snapshot || !selected) return null
  if (selected.kind === 'subagent') {
    const item = (snapshot.subagents || []).find((subagent) => subagent.id === selected.id)
    return item && { kind: 'subagent', id: item.id, title: item.taste?.label || item.id, item }
  }
  if (selected.kind === 'investigator' || selected.kind === 'synthesis') {
    const item = (snapshot.investigators || []).find((investigator) => investigator.id === selected.id)
    return item && { kind: selected.kind, id: item.id, title: item.section_title || item.id, item }
  }
  if (selected.kind === 'critique') {
    const item = (snapshot.critiques || []).find((critique) => critique.critic_id === selected.id)
    return item && { kind: 'critique', id: item.critic_id, title: item.critic_id.replaceAll('_', ' '), item }
  }
  if (selected.kind === 'final') return { kind: 'final', id: 'final', title: 'Final report' }
  if (selected.kind === 'shared') {
    const item = snapshot.shared?.[selected.id]
    return item && { kind: 'shared', id: selected.id, title: selected.id.replaceAll('_', ' '), item }
  }
  return null
}
