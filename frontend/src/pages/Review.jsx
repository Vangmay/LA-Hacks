import { useEffect, useMemo, useState } from 'react'
import { Link, useParams } from 'react-router-dom'
import { api } from '../api/client'

const STATUS_COLORS = {
  pending: '#6b7280',
  checking: '#00eaff',
  no_objection: '#22c55e',
  contested: '#eab308',
  likely_flawed: '#f97316',
  refuted: '#ef4444',
  cascade_risk: '#a855f7',
}

function statusColor(label) {
  return STATUS_COLORS[label] || STATUS_COLORS.pending
}

export default function Review() {
  const { jobId } = useParams()
  const [status, setStatus] = useState(null)
  const [dag, setDag] = useState(null)
  const [selectedId, setSelectedId] = useState(null)
  const [error, setError] = useState('')

  useEffect(() => {
    if (!jobId) return
    let cancelled = false
    async function load() {
      try {
        const [s, d] = await Promise.all([
          api.review.status(jobId),
          api.review.dag(jobId),
        ])
        if (cancelled) return
        setStatus(s)
        setDag(d)
      } catch (err) {
        if (!cancelled) setError(err.message || 'Failed to load job')
      }
    }
    load()
    return () => { cancelled = true }
  }, [jobId])

  const nodes = dag?.nodes || []
  const edges = dag?.edges || []
  const selected = useMemo(
    () => nodes.find((n) => n.id === selectedId) || null,
    [nodes, selectedId],
  )

  const completed = status?.completed_atoms ?? 0
  const total = status?.total_atoms ?? nodes.length

  return (
    <div className="min-h-screen w-full bg-[#0f1226] text-white flex flex-col font-sans">
      <header className="flex items-center justify-between px-6 py-3 border-b border-white/10">
        <div className="flex items-center gap-4">
          <Link to="/" className="text-[#00eaff] text-sm hover:underline">← Home</Link>
          <span className="text-sm opacity-60">Job</span>
          <span className="text-sm font-mono">{jobId}</span>
        </div>
        <div className="flex items-center gap-3 text-sm">
          <span className="opacity-60">Status:</span>
          <span className="font-semibold">{status?.status || 'loading…'}</span>
          <span className="opacity-60">·</span>
          <span>{completed}/{total} atoms</span>
        </div>
      </header>

      {error && (
        <div className="px-6 py-2 bg-red-500/10 text-red-300 text-sm">{error}</div>
      )}

      <div className="flex-1 grid grid-cols-[320px_1fr_360px] min-h-0">
        <aside className="border-r border-white/10 overflow-y-auto">
          <div className="px-4 py-3 text-xs uppercase tracking-wider opacity-60">Atoms</div>
          {nodes.length === 0 && (
            <div className="px-4 py-2 text-sm opacity-50">Waiting for atoms…</div>
          )}
          <ul>
            {nodes.map((n) => {
              const active = n.id === selectedId
              return (
                <li key={n.id}>
                  <button
                    onClick={() => setSelectedId(n.id)}
                    className={`w-full text-left px-4 py-2 border-b border-white/5 hover:bg-white/5 ${active ? 'bg-white/10' : ''}`}
                  >
                    <div className="flex items-center gap-2">
                      <span
                        className="w-2 h-2 rounded-full inline-block"
                        style={{ background: statusColor(n.status) }}
                      />
                      <span className="text-xs uppercase opacity-70">{n.atom_type}</span>
                      {n.importance && (
                        <span className="ml-auto text-[10px] opacity-50">{n.importance}</span>
                      )}
                    </div>
                    <div className="text-sm mt-1 line-clamp-2">{n.label}</div>
                    {n.section && (
                      <div className="text-[11px] opacity-50 mt-0.5 truncate">{n.section}</div>
                    )}
                  </button>
                </li>
              )
            })}
          </ul>
        </aside>

        <main className="flex items-center justify-center p-8">
          <div className="text-center max-w-md">
            <div className="text-sm uppercase tracking-wider opacity-50 mb-2">Research Graph</div>
            <div className="text-white/70">
              {nodes.length} atoms, {edges.length} edges
            </div>
            <div className="mt-6 text-xs opacity-40">DAG visualization coming next.</div>
          </div>
        </main>

        <aside className="border-l border-white/10 overflow-y-auto">
          {!selected ? (
            <div className="p-6 text-sm opacity-50">Select an atom to inspect.</div>
          ) : (
            <div className="p-4 space-y-3">
              <div className="flex items-center gap-2">
                <span
                  className="w-2.5 h-2.5 rounded-full inline-block"
                  style={{ background: statusColor(selected.status) }}
                />
                <span className="text-xs uppercase opacity-70">{selected.atom_type}</span>
                <span className="ml-auto text-xs opacity-60">{selected.status}</span>
              </div>
              <div className="text-sm">{selected.label}</div>
              {selected.section && (
                <div className="text-xs opacity-60">Section: {selected.section}</div>
              )}
              {selected.source_excerpt && (
                <div className="mt-2">
                  <div className="text-[11px] uppercase tracking-wider opacity-50 mb-1">Source excerpt</div>
                  <div className="text-xs bg-black/30 rounded p-2 whitespace-pre-wrap">{selected.source_excerpt}</div>
                </div>
              )}
              <div className="mt-4 text-[11px] opacity-40">
                Checks, challenges, and rebuttals will stream in here.
              </div>
            </div>
          )}
        </aside>
      </div>
    </div>
  )
}
