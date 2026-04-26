import { useMemo, useState } from 'react'
import LeanCodeBlock from './LeanCodeBlock'
import StatusBadge from './StatusBadge'

export default function AtomDetail({ atom }) {
  const [tab, setTab] = useState('artifact')
  const latestArtifact = useMemo(() => {
    const artifacts = atom?.artifacts || []
    return artifacts[artifacts.length - 1] || null
  }, [atom])

  if (!atom) {
    return <div className="text-xs text-white/45">Select a formalized atom for details.</div>
  }

  return (
    <div className="space-y-3">
      <div className="flex items-center gap-2">
        <span className="truncate font-mono text-[11px] text-white/55">{atom.atom_id}</span>
        <span className="ml-auto"><StatusBadge value={atom.label || atom.status} /></span>
      </div>
      {atom.rationale && <div className="rounded border border-white/10 bg-black/15 p-2 text-xs text-white/70">{atom.rationale}</div>}
      <div className="flex gap-1">
        {['artifact', 'tools', 'transcript'].map(item => (
          <button
            key={item}
            onClick={() => setTab(item)}
            className={`rounded border px-2 py-1 text-[10px] uppercase ${tab === item ? 'border-blue-400/40 bg-blue-500/15 text-blue-100' : 'border-white/10 bg-white/5 text-white/55'}`}
          >
            {item}
          </button>
        ))}
      </div>
      {tab === 'artifact' && <LeanCodeBlock code={latestArtifact?.lean_code} />}
      {tab === 'tools' && (
        <div className="max-h-48 space-y-1 overflow-auto rounded border border-white/10 bg-black/10 p-2">
          {(atom.tool_calls || []).map(call => (
            <div key={call.call_id} className="rounded bg-white/[0.03] p-2 text-[11px] text-white/60">
              <div className="flex gap-2">
                <span className="font-mono">{call.tool_name}</span>
                <span className="ml-auto">{call.status}</span>
              </div>
              {call.result_summary?.first_errors?.[0] && (
                <div className="mt-1 line-clamp-3 text-red-200/75">{call.result_summary.first_errors[0]}</div>
              )}
            </div>
          ))}
        </div>
      )}
      {tab === 'transcript' && (
        <pre className="max-h-48 overflow-auto rounded border border-white/10 bg-black/10 p-2 text-[10px] text-white/55">
          {JSON.stringify(atom.llm_messages || [], null, 2)}
        </pre>
      )}
    </div>
  )
}
