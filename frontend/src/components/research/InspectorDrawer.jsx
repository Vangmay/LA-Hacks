import { useEffect, useMemo, useState } from 'react'
import { createPortal } from 'react-dom'
import ResearchMarkdown from './ResearchMarkdown'

const ARTIFACT_TABS = ['findings', 'papers', 'proposal_seeds', 'memory', 'queries', 'handoff']
const ARTIFACT_LABELS = {
  findings: 'Findings',
  papers: 'Papers',
  proposal_seeds: 'Proposal seeds',
  memory: 'Memory',
  queries: 'Queries',
  handoff: 'Handoff',
}

export default function InspectorDrawer({ snapshot, selected, onSelect }) {
  const [tab, setTab] = useState('overview')
  const [modal, setModal] = useState(null)
  const target = useMemo(() => resolveSelection(snapshot, selected), [snapshot, selected])

  if (!target) {
    return (
      <aside className="flex h-full min-h-0 flex-col overflow-hidden border-l border-white/10 bg-[#131720]">
        <div className="min-h-0 flex-1 overflow-y-auto">
          <RunOverview snapshot={snapshot} onSelect={onSelect} onOpenMarkdown={setModal} />
        </div>
        <MarkdownModal modal={modal} onClose={() => setModal(null)} />
      </aside>
    )
  }

  return (
    <aside className="flex h-full min-h-0 flex-col overflow-hidden border-l border-white/10 bg-[#131720]">
      <div className="shrink-0 border-b border-white/10 bg-[#131720]/95 px-4 py-3 backdrop-blur">
        <div className="font-mono text-[10px] uppercase tracking-wider text-white/40">{displayKind(target.kind)}</div>
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
      <div className="min-h-0 flex-1 overflow-y-auto p-4">
        <SelectionContent
          target={target}
          tab={tab}
          snapshot={snapshot}
          onSelect={onSelect}
          onOpenMarkdown={setModal}
        />
      </div>
      <MarkdownModal modal={modal} onClose={() => setModal(null)} />
    </aside>
  )
}

function RunOverview({ snapshot, onSelect, onOpenMarkdown }) {
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
        <Stat label="Researchers" value={`${counts.completed_subagents || 0}/${counts.subagents || 0}`} />
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
            <div className="mt-1 text-xs text-white/45">{investigator.subagent_ids?.length || 0} researchers - {investigator.status}</div>
          </button>
        ))}
      </div>
      {snapshot?.final_report?.available && (
        <MarkdownOpenPanel
          className="mt-5"
          title="Final report"
          subtitle={snapshot.final_report.path}
          content={snapshot.final_report.markdown}
          meta={snapshot.final_report.artifact_meta}
          onOpen={onOpenMarkdown}
        />
      )}
    </div>
  )
}

function SelectionContent({ target, tab, snapshot, onSelect, onOpenMarkdown }) {
  if (target.kind === 'subagent') {
    if (tab === 'persona') return <PersonaCard taste={target.item.taste} />
    if (tab === 'tools') return <ToolTimeline events={target.item.tool_events || []} />
    if (ARTIFACT_TABS.includes(tab)) {
      return (
        <MarkdownOpenPanel
          title={ARTIFACT_LABELS[tab] || tab}
          subtitle={target.item.id}
          content={target.item.artifacts?.[tab]}
          meta={target.item.artifact_meta?.[tab]}
          onOpen={onOpenMarkdown}
        />
      )
    }
    return <SubagentOverview item={target.item} />
  }

  if (target.kind === 'investigator' || target.kind === 'synthesis') {
    return (
      <div className="space-y-4">
        <OverviewRows rows={[['Status', target.item.status], ['Workspace', target.item.workspace_path], ['Researchers', target.item.subagent_ids?.length || 0]]} />
        <div className="space-y-2">
          {(target.item.subagent_ids || []).map((id) => (
            <button key={id} type="button" onClick={() => onSelect?.({ kind: 'subagent', id })} className="w-full rounded border border-white/10 bg-[#0D1017] px-3 py-2 text-left text-xs hover:border-[#67E8F9]/40">
              {id}
            </button>
          ))}
        </div>
        <MarkdownOpenPanel
          title="Investigator synthesis"
          subtitle={target.item.section_title || target.item.id}
          content={target.item.synthesis_md}
          meta={target.item.artifact_meta}
          onOpen={onOpenMarkdown}
        />
      </div>
    )
  }

  if (target.kind === 'critique') {
    return (
      <MarkdownOpenPanel
        title={target.title}
        subtitle={target.item.lens}
        content={target.item.markdown}
        meta={target.item.artifact_meta}
        onOpen={onOpenMarkdown}
      />
    )
  }
  if (target.kind === 'final') {
    return (
      <MarkdownOpenPanel
        title="Final report"
        subtitle={snapshot?.final_report?.path}
        content={snapshot?.final_report?.markdown}
        meta={snapshot?.final_report?.artifact_meta}
        onOpen={onOpenMarkdown}
      />
    )
  }
  if (target.kind === 'shared') {
    return (
      <MarkdownOpenPanel
        title={target.title}
        subtitle={target.item.path}
        content={target.item.content}
        meta={target.item.artifact_meta}
        onOpen={onOpenMarkdown}
      />
    )
  }
  return (
    <MarkdownOpenPanel
      title={target.title}
      content={target.markdown}
      onOpen={onOpenMarkdown}
    />
  )
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
          ['API calls', `${item.budget?.research_used || 0}/${item.budget?.research_max || item.max_tool_calls || 0}`],
          ['Workspace writes', item.budget?.workspace_used ?? 0],
          ['LLM steps', item.budget?.llm_steps ?? 0],
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
    if (filter === 'errors') return ['tool_error', 'rejected_action', 'subagent.tool.error', 'subagent.tool.rejected'].includes(event.type)
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
              <span className={badgeColor(event.type)}>{toolEventLabel(event.type)}</span>
              <span className="ml-2 text-white/75">{formatToolName(event.tool_name || event.action?.action || 'action')}</span>
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
          <div className="min-w-0 break-words text-white/70">{value ?? '-'}</div>
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

function MarkdownOpenPanel({ title, subtitle, content, meta, onOpen, className = '' }) {
  const text = String(content || '').trim()
  const hasContent = Boolean(text)
  const charCount = meta?.char_count || text.length
  return (
    <div className={`rounded border border-white/10 bg-[#0D1017] p-3 ${className}`}>
      <div className="flex items-start gap-3">
        <div className="min-w-0 flex-1">
          <div className="text-sm font-semibold text-[#E4E7F0]">{title}</div>
          {subtitle && <div className="mt-1 truncate font-mono text-[11px] text-white/35">{subtitle}</div>}
          <div className="mt-2 text-xs text-white/40">
            {hasContent ? `${charCount.toLocaleString()} chars` : 'No markdown written yet.'}
          </div>
        </div>
        <button
          type="button"
          disabled={!hasContent}
          onClick={() => onOpen?.({ title, subtitle, content: text })}
          className="shrink-0 rounded border border-[#67E8F9]/40 bg-[#67E8F9]/10 px-3 py-1.5 text-xs font-semibold text-[#67E8F9] transition-colors hover:bg-[#67E8F9]/15 disabled:cursor-not-allowed disabled:border-white/10 disabled:bg-white/[0.03] disabled:text-white/30"
        >
          Open
        </button>
      </div>
      {hasContent && (
        <div className="mt-3 max-h-28 overflow-hidden rounded border border-white/5 bg-black/15 p-3 text-xs leading-relaxed text-white/55">
          {excerpt(text)}
        </div>
      )}
    </div>
  )
}

function MarkdownModal({ modal, onClose }) {
  useEffect(() => {
    if (!modal) return undefined
    const handleKeyDown = (event) => {
      if (event.key === 'Escape') onClose()
    }
    window.addEventListener('keydown', handleKeyDown)
    return () => window.removeEventListener('keydown', handleKeyDown)
  }, [modal, onClose])

  if (!modal || typeof document === 'undefined') return null

  return createPortal(
    <div
      className="fixed inset-0 z-50 flex items-center justify-center bg-black/75 p-4"
      onMouseDown={(event) => {
        if (event.target === event.currentTarget) onClose()
      }}
    >
      <div className="flex max-h-[88vh] w-full max-w-5xl flex-col overflow-hidden rounded-md border border-white/10 bg-[#131720] shadow-2xl">
        <div className="flex shrink-0 items-start gap-3 border-b border-white/10 px-5 py-4">
          <div className="min-w-0 flex-1">
            <div className="text-base font-semibold text-[#E4E7F0]">{modal.title}</div>
            {modal.subtitle && <div className="mt-1 truncate font-mono text-xs text-white/40">{modal.subtitle}</div>}
          </div>
          <button
            type="button"
            onClick={onClose}
            aria-label="Close markdown preview"
            className="flex h-8 w-8 shrink-0 items-center justify-center rounded border border-white/10 bg-white/[0.03] text-lg leading-none text-white/60 hover:border-[#67E8F9]/40 hover:text-white"
          >
            x
          </button>
        </div>
        <div className="min-h-0 flex-1 overflow-y-auto p-5">
          <ResearchMarkdown>{modal.content}</ResearchMarkdown>
        </div>
      </div>
    </div>,
    document.body
  )
}

function excerpt(text) {
  const compact = text.replace(/\s+/g, ' ').trim()
  return compact.length > 280 ? `${compact.slice(0, 280)}...` : compact
}

function toolEventLabel(type) {
  const labels = {
    llm_action: 'Tool call',
    tool_result: 'Result',
    tool_error: 'Error',
    rejected_action: 'Corrected',
    'subagent.tool.requested': 'Tool call',
    'subagent.tool.result': 'Result',
    'subagent.tool.error': 'Error',
    'subagent.tool.rejected': 'Corrected',
  }
  return labels[type] || 'Update'
}

function formatToolName(value) {
  return String(value || 'action').replaceAll('_', ' ')
}

function displayKind(kind) {
  if (kind === 'subagent') return 'researcher'
  if (kind === 'shared') return 'shared synthesis'
  return String(kind || '').replaceAll('_', ' ')
}

function badgeColor(type) {
  if (type === 'tool_error' || type === 'subagent.tool.error') return 'rounded bg-red-500/15 px-1.5 py-0.5 text-red-300'
  if (type === 'rejected_action' || type === 'subagent.tool.rejected') return 'rounded bg-amber-500/15 px-1.5 py-0.5 text-amber-300'
  if (type === 'tool_result' || type === 'subagent.tool.result') return 'rounded bg-green-500/15 px-1.5 py-0.5 text-green-300'
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
