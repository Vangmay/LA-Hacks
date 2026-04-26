import { useEffect, useMemo, useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { api } from '../../api/client'
import { ResearchIcon } from '../../assets/ModeIcons'

const DEFAULT_SECTIONS = 'Core method\nExperiments\nRelated work and novelty'

export default function ResearchLanding() {
  const navigate = useNavigate()
  const [runs, setRuns] = useState([])
  const [loadingRuns, setLoadingRuns] = useState(true)
  const [arxivUrl, setArxivUrl] = useState('https://arxiv.org/abs/1706.03762')
  const [objective, setObjective] = useState('novelty_ideation')
  const [mode, setMode] = useState('live')
  const [sections, setSections] = useState(DEFAULT_SECTIONS)
  const [maxInvestigators, setMaxInvestigators] = useState(3)
  const [subagents, setSubagents] = useState(3)
  const [toolCalls, setToolCalls] = useState(12)
  const [error, setError] = useState('')
  const [submitting, setSubmitting] = useState(false)
  const [query, setQuery] = useState('')

  useEffect(() => {
    let cancelled = false
    async function loadRuns() {
      try {
        const res = await api.research.runs()
        if (!cancelled) setRuns(res.runs || [])
      } catch (err) {
        if (!cancelled) setError(err.message || 'Failed to load research runs')
      } finally {
        if (!cancelled) setLoadingRuns(false)
      }
    }
    loadRuns()
    return () => {
      cancelled = true
    }
  }, [])

  const filteredRuns = useMemo(() => {
    const needle = query.trim().toLowerCase()
    if (!needle) return runs
    return runs.filter((run) => JSON.stringify(run).toLowerCase().includes(needle))
  }, [runs, query])

  async function handleStart(e) {
    e.preventDefault()
    if (!arxivUrl.trim() || submitting) return
    setSubmitting(true)
    setError('')
    try {
      const res = await api.research.start({
        arxiv_url: arxivUrl.trim(),
        research_objective: objective,
        mode,
        section_titles: sections.split('\n').map((item) => item.trim()).filter(Boolean),
        max_investigators: Number(maxInvestigators),
        subagents_per_investigator: Number(subagents),
        subagent_tool_calls: Number(toolCalls),
      })
      if (!res.run_id) throw new Error(res.detail || 'No run_id returned')
      navigate(`/research/${res.run_id}`)
    } catch (err) {
      setError(err.message || 'Failed to start research run')
      setSubmitting(false)
    }
  }

  return (
    <div className="min-h-screen bg-[#0A0C10] text-[#E4E7F0]">
      <header className="flex items-center gap-4 border-b border-white/10 bg-[#131720] px-6 py-4">
        <Link to="/" className="text-sm text-[#67E8F9] hover:underline">Home</Link>
        <div className="flex items-center gap-3">
          <div className="scale-75"><ResearchIcon /></div>
          <div>
            <div className="text-lg font-semibold">Research Deep Dive</div>
            <div className="font-mono text-xs text-white/40">{runs.length} saved workspaces</div>
          </div>
        </div>
      </header>

      {error && <div className="border-b border-red-500/20 bg-red-500/10 px-6 py-2 text-sm text-red-200">{error}</div>}

      <main className="grid min-h-[calc(100vh-81px)] grid-cols-1 lg:grid-cols-[minmax(360px,520px)_1fr]">
        <section className="border-r border-white/10 bg-[#0D1017] p-5">
          <div className="mb-4 flex items-center justify-between gap-3">
            <h1 className="text-sm font-semibold uppercase tracking-wider text-white/60">Open Run</h1>
            <input
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              placeholder="Filter"
              className="w-40 rounded border border-white/10 bg-[#0A0C10] px-3 py-1.5 text-xs outline-none focus:border-[#67E8F9]/50"
            />
          </div>
          <div className="space-y-2">
            {loadingRuns && <div className="text-sm text-white/40">Loading saved runs...</div>}
            {!loadingRuns && filteredRuns.length === 0 && <div className="text-sm text-white/40">No matching runs.</div>}
            {filteredRuns.map((run) => (
              <button
                key={run.run_id}
                type="button"
                onClick={() => navigate(`/research/${run.run_id}`)}
                className="w-full rounded-md border border-white/10 bg-[#131720] p-3 text-left transition-colors hover:border-[#67E8F9]/40 hover:bg-[#17202c]"
              >
                <div className="flex items-start gap-3">
                  <span className={`mt-1 h-2 w-2 rounded-full ${run.final_report_available ? 'bg-green-400' : 'bg-[#67E8F9]'}`} />
                  <div className="min-w-0 flex-1">
                    <div className="truncate font-mono text-xs text-[#E4E7F0]">{run.run_id}</div>
                    <div className="mt-1 truncate text-xs text-white/45">{run.arxiv_url || run.paper_id || run.created_utc || run.mtime}</div>
                    <div className="mt-2 flex flex-wrap gap-1.5 text-[10px] text-white/45">
                      <span className="rounded bg-white/5 px-2 py-1">{run.status}</span>
                      <span className="rounded bg-white/5 px-2 py-1">{run.subagent_count} agents</span>
                      <span className="rounded bg-white/5 px-2 py-1">{run.tool_event_count} tool events</span>
                      {run.final_report_available && <span className="rounded bg-green-400/10 px-2 py-1 text-green-300">report</span>}
                    </div>
                  </div>
                </div>
              </button>
            ))}
          </div>
        </section>

        <section className="p-5">
          <form onSubmit={handleStart} className="mx-auto max-w-3xl rounded-md border border-white/10 bg-[#131720] p-5">
            <div className="mb-5">
              <div className="text-sm font-semibold uppercase tracking-wider text-white/60">Start Live Run</div>
            </div>

            <div className="space-y-4">
              <Field label="arXiv source">
                <input
                  value={arxivUrl}
                  onChange={(e) => setArxivUrl(e.target.value)}
                  className="w-full rounded border border-white/10 bg-[#0D1017] px-3 py-2 text-sm outline-none focus:border-[#67E8F9]/50"
                />
              </Field>
              <div className="grid gap-4 md:grid-cols-2">
                <Field label="Objective">
                  <select value={objective} onChange={(e) => setObjective(e.target.value)} className="w-full rounded border border-white/10 bg-[#0D1017] px-3 py-2 text-sm outline-none focus:border-[#67E8F9]/50">
                    <option value="novelty_ideation">Novelty ideation</option>
                    <option value="literature_review">Literature review</option>
                  </select>
                </Field>
                <Field label="Execution">
                  <select value={mode} onChange={(e) => setMode(e.target.value)} className="w-full rounded border border-white/10 bg-[#0D1017] px-3 py-2 text-sm outline-none focus:border-[#67E8F9]/50">
                    <option value="live">Live</option>
                    <option value="dry_run">Dry run</option>
                  </select>
                </Field>
              </div>
              <Field label="Sections">
                <textarea
                  value={sections}
                  onChange={(e) => setSections(e.target.value)}
                  rows={4}
                  className="w-full resize-none rounded border border-white/10 bg-[#0D1017] px-3 py-2 text-sm outline-none focus:border-[#67E8F9]/50"
                />
              </Field>
              <div className="grid gap-4 md:grid-cols-3">
                <NumberField label="Investigators" value={maxInvestigators} onChange={setMaxInvestigators} min={1} max={6} />
                <NumberField label="Subagents each" value={subagents} onChange={setSubagents} min={1} max={6} />
                <NumberField label="Tool calls" value={toolCalls} onChange={setToolCalls} min={1} max={48} />
              </div>
              <button
                type="submit"
                disabled={submitting || !arxivUrl.trim()}
                className="w-full rounded bg-[#5B5BD6] px-4 py-2.5 text-sm font-semibold text-white transition-colors hover:bg-[#4a4ac2] disabled:cursor-not-allowed disabled:opacity-50"
              >
                {submitting ? 'Starting...' : 'Start Research Run'}
              </button>
            </div>
          </form>
        </section>
      </main>
    </div>
  )
}

function Field({ label, children }) {
  return (
    <label className="block">
      <div className="mb-2 text-xs font-semibold uppercase tracking-wider text-white/45">{label}</div>
      {children}
    </label>
  )
}

function NumberField({ label, value, onChange, min, max }) {
  return (
    <Field label={label}>
      <input
        type="number"
        value={value}
        min={min}
        max={max}
        onChange={(e) => onChange(e.target.value)}
        className="w-full rounded border border-white/10 bg-[#0D1017] px-3 py-2 text-sm outline-none focus:border-[#67E8F9]/50"
      />
    </Field>
  )
}
