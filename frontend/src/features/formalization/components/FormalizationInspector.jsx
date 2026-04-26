import { useMemo, useState } from 'react'
import AxleToolBadge from './AxleToolBadge'
import LeanCodeBlock from './LeanCodeBlock'
import StatusBadge from './StatusBadge'

const ATOM_TABS = ['overview', 'tools', 'lean', 'thoughts', 'context']

export default function FormalizationInspector({ state, selected, onSelect }) {
  const [tab, setTab] = useState('overview')
  const target = useMemo(() => resolveTarget(state, selected), [state, selected])

  return (
    <aside className="flex h-full min-h-0 flex-col overflow-hidden border-l border-white/10 bg-[#131720]">
      <div className="shrink-0 border-b border-white/10 bg-[#131720]/95 px-4 py-3 backdrop-blur">
        <div className="font-mono text-[10px] uppercase tracking-wider text-white/40">{target.kind}</div>
        <div className="mt-1 line-clamp-2 text-sm font-semibold text-[#E4E7F0]">{target.title}</div>
        {target.kind === 'atom' && (
          <div className="mt-2 flex flex-wrap gap-2">
            {ATOM_TABS.map((item) => (
              <button
                key={item}
                type="button"
                onClick={() => setTab(item)}
                className={`rounded border px-2.5 py-1 text-xs capitalize transition-colors ${tab === item ? 'border-[#67E8F9]/50 bg-[#67E8F9]/10 text-[#67E8F9]' : 'border-white/10 bg-white/[0.03] text-white/55 hover:text-white'}`}
              >
                {item}
              </button>
            ))}
          </div>
        )}
      </div>
      <div className="min-h-0 flex-1 overflow-y-auto p-4">
        {target.kind === 'run' ? (
          <RunOverview state={state} onSelect={onSelect} />
        ) : (
          <AtomContent atom={target.atom} tab={tab} />
        )}
      </div>
    </aside>
  )
}

function RunOverview({ state, onSelect }) {
  const runtime = state.runtime || {}
  return (
    <div className="space-y-4">
      <div className="grid grid-cols-2 gap-2 text-xs">
        <Stat label="Status" value={state.status || 'idle'} />
        <Stat label="Connection" value={state.connection || 'idle'} />
        <Stat label="Atoms" value={`${state.counts?.completed_atoms || 0}/${state.counts?.atoms || 0}`} />
        <Stat label="Active" value={state.counts?.running_atoms || 0} />
        <Stat label="Tool calls" value={state.counts?.tool_calls || 0} />
        <Stat label="Artifacts" value={state.counts?.artifacts || 0} />
      </div>
      <OverviewRows
        rows={[
          ['Model', runtime.model_name],
          ['Provider', runtime.model_provider],
          ['Reasoning', runtime.reasoning_effort],
          ['Atom workers', runtime.parallelism],
          ['AXLE concurrency', runtime.axle_max_concurrency],
          ['Lean environment', runtime.lean_environment],
          ['Max AXLE calls', runtime.max_axle_calls_per_atom],
          ['Max iterations', runtime.max_iterations_per_atom],
        ]}
      />
      <div className="space-y-2">
        {(state.atomOrder || []).map((atomId) => {
          const atom = state.atoms[atomId] || { atom_id: atomId }
          return (
            <button
              key={atomId}
              type="button"
              onClick={() => onSelect?.({ kind: 'atom', id: atomId })}
              className="w-full rounded border border-white/10 bg-[#0D1017] px-3 py-2 text-left hover:border-[#67E8F9]/40"
            >
              <div className="flex items-center gap-2">
                <div className="min-w-0 flex-1 truncate text-xs font-medium">{atom.text || atomId}</div>
                <StatusBadge value={atom.label || atom.status} />
              </div>
              <div className="mt-1 text-[11px] text-white/40">
                {(atom.tool_calls?.length || 0)} tool calls - {(atom.artifacts?.length || 0)} artifacts
              </div>
            </button>
          )
        })}
      </div>
    </div>
  )
}

function AtomContent({ atom, tab }) {
  if (!atom) {
    return <div className="text-sm text-white/45">Select an atom to inspect.</div>
  }
  if (tab === 'tools') return <ToolTimeline calls={atom.tool_calls || []} />
  if (tab === 'lean') return <ArtifactPanel atom={atom} />
  if (tab === 'thoughts') return <ThoughtPanel thoughts={atom.thoughts || []} />
  if (tab === 'context') return <ContextPanel atom={atom} />
  return <AtomOverview atom={atom} />
}

function AtomOverview({ atom }) {
  const latestTool = [...(atom.tool_calls || [])].reverse().find(Boolean)
  return (
    <div className="space-y-4">
      <div className="flex items-center gap-2">
        <div className="min-w-0 flex-1 truncate font-mono text-[11px] text-white/45">{atom.atom_id}</div>
        <StatusBadge value={atom.label || atom.status} />
      </div>
      {atom.text && <div className="rounded border border-white/10 bg-[#0D1017] p-3 text-sm leading-relaxed text-white/75">{atom.text}</div>}
      {atom.rationale && <div className="rounded border border-emerald-400/20 bg-emerald-500/10 p-3 text-sm leading-relaxed text-emerald-100">{atom.rationale}</div>}
      {atom.error && <div className="rounded border border-red-400/20 bg-red-500/10 p-3 text-sm text-red-200">{atom.error}</div>}
      <div className="grid grid-cols-2 gap-2 text-xs">
        <Stat label="Type" value={atom.atom_type || '-'} />
        <Stat label="Importance" value={atom.importance || '-'} />
        <Stat label="Tool calls" value={atom.tool_calls?.length || 0} />
        <Stat label="Artifacts" value={atom.artifacts?.length || 0} />
        <Stat label="Confidence" value={atom.confidence ?? '-'} />
        <Stat label="Queue" value={atom.queue_index ? `${atom.queue_index}/${atom.queue_total || '?'}` : '-'} />
      </div>
      {latestTool && (
        <div className="rounded border border-white/10 bg-[#0D1017] p-3">
          <div className="mb-2 text-[10px] uppercase tracking-wider text-white/35">Latest tool</div>
          <ToolCallSummary call={latestTool} />
        </div>
      )}
    </div>
  )
}

function ToolTimeline({ calls }) {
  const [filter, setFilter] = useState('all')
  const filtered = calls.filter((call) => {
    if (filter === 'all') return true
    if (filter === 'errors') return call.status === 'error' || call.error
    if (filter === 'axle') return String(call.tool_name || '').startsWith('axle_')
    if (filter === 'meta') return !String(call.tool_name || '').startsWith('axle_')
    return true
  })
  return (
    <div>
      <div className="mb-3 flex flex-wrap gap-2">
        {['all', 'axle', 'meta', 'errors'].map((item) => (
          <button key={item} type="button" onClick={() => setFilter(item)} className={`rounded border px-2 py-1 text-xs ${filter === item ? 'border-[#67E8F9]/50 text-[#67E8F9]' : 'border-white/10 text-white/55'}`}>
            {item}
          </button>
        ))}
      </div>
      <div className="space-y-2">
        {filtered.length === 0 && <div className="text-sm text-white/40">No tool calls yet.</div>}
        {filtered.map((call, index) => (
          <details key={call.call_id || index} className="rounded border border-white/10 bg-[#0D1017] p-3">
            <summary className="cursor-pointer text-xs">
              <span className="mr-2 font-mono text-white/35">{index + 1}</span>
              <StatusBadge value={call.status} />
              <span className="ml-2"><AxleToolBadge tool={call.tool_name} /></span>
              {call.duration_ms !== null && call.duration_ms !== undefined && <span className="ml-2 text-white/35">{call.duration_ms}ms</span>}
            </summary>
            <pre className="mt-3 max-h-64 overflow-auto rounded bg-black/25 p-3 text-[11px] text-white/70">
              {JSON.stringify({ arguments: call.arguments, result_summary: call.result_summary, error: call.error }, null, 2)}
            </pre>
          </details>
        ))}
      </div>
    </div>
  )
}

function ArtifactPanel({ atom }) {
  const [artifactId, setArtifactId] = useState('')
  const artifacts = atom.artifacts || []
  const selected = artifacts.find((artifact) => artifact.artifact_id === artifactId) || artifacts[artifacts.length - 1]
  return (
    <div className="space-y-3">
      <div className="flex flex-wrap gap-2">
        {artifacts.map((artifact, index) => (
          <button
            key={artifact.artifact_id || index}
            type="button"
            onClick={() => setArtifactId(artifact.artifact_id)}
            className={`rounded border px-2 py-1 text-xs ${selected?.artifact_id === artifact.artifact_id ? 'border-[#67E8F9]/50 bg-[#67E8F9]/10 text-[#67E8F9]' : 'border-white/10 text-white/55'}`}
          >
            {artifact.kind || 'artifact'} {index + 1}
          </button>
        ))}
      </div>
      {selected ? (
        <>
          <OverviewRows
            rows={[
              ['Kind', selected.kind],
              ['Iteration', selected.iteration],
              ['AXLE check', String(selected.axle_check_okay ?? '-')],
              ['Proof verify', String(selected.axle_verify_okay ?? '-')],
              ['Path', selected.path],
            ]}
          />
          <LeanCodeBlock code={selected.lean_code} />
        </>
      ) : (
        <div className="text-sm text-white/40">No Lean artifacts recorded yet.</div>
      )}
    </div>
  )
}

function ThoughtPanel({ thoughts }) {
  return (
    <div className="space-y-2">
      {thoughts.length === 0 && <div className="text-sm text-white/40">No streamed model text yet.</div>}
      {thoughts.map((thought, index) => (
        <details key={`${thought.iteration}-${index}`} open={index === thoughts.length - 1} className="rounded border border-white/10 bg-[#0D1017] p-3">
          <summary className="cursor-pointer text-xs text-white/60">
            iteration {thought.iteration || index + 1}
            {thought.model_name && <span className="ml-2 font-mono text-white/35">{thought.model_name}</span>}
          </summary>
          <div className="mt-3 whitespace-pre-wrap text-sm leading-relaxed text-white/70">{thought.content || 'No visible content.'}</div>
        </details>
      ))}
    </div>
  )
}

function ContextPanel({ atom }) {
  const context = atom.context || {}
  return (
    <div className="space-y-3">
      <OverviewRows
        rows={[
          ['Section', atom.section_heading || context.section_heading],
          ['Equations', context.equations],
          ['Citations', context.citations],
          ['Dependencies', context.dependencies],
          ['Nearby prose chars', context.nearby_prose_chars],
          ['TeX excerpt chars', context.tex_excerpt_chars],
        ]}
      />
      {(context.formalization_hints || []).length > 0 && (
        <div className="rounded border border-[#67E8F9]/20 bg-[#67E8F9]/10 p-3">
          <div className="mb-2 text-[10px] uppercase tracking-wider text-[#67E8F9]">Formalization hints</div>
          <div className="space-y-2 text-sm leading-relaxed text-white/75">
            {context.formalization_hints.map((hint, index) => <div key={index}>{hint}</div>)}
          </div>
        </div>
      )}
    </div>
  )
}

function ToolCallSummary({ call }) {
  const okay = call.result_summary?.okay
  return (
    <div className="text-xs text-white/65">
      <div className="flex items-center gap-2">
        <AxleToolBadge tool={call.tool_name} />
        <span className="font-mono text-white/40">{call.status}</span>
        {okay !== undefined && <span className={okay ? 'text-emerald-200' : 'text-red-200'}>{okay ? 'okay' : 'needs repair'}</span>}
      </div>
      {call.result_summary?.first_errors?.[0] && <div className="mt-2 line-clamp-3 text-red-200/80">{call.result_summary.first_errors[0]}</div>}
    </div>
  )
}

function OverviewRows({ rows }) {
  return (
    <div className="divide-y divide-white/5 rounded border border-white/10 bg-[#0D1017]">
      {rows.map(([label, value]) => (
        <div key={label} className="grid grid-cols-[120px_1fr] gap-3 px-3 py-2 text-xs">
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

function resolveTarget(state, selected) {
  if (selected?.kind === 'atom' && selected.id) {
    const atom = state.atoms?.[selected.id]
    if (atom) {
      return {
        kind: 'atom',
        title: atom.text || atom.atom_id || selected.id,
        atom,
      }
    }
  }
  return {
    kind: 'run',
    title: state.runId || 'Lean formalization run',
  }
}
