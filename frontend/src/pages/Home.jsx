import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { api } from '../api/client'

export default function Home() {
  const navigate = useNavigate()
  const [arxivUrl, setArxivUrl] = useState('')
  const [submitting, setSubmitting] = useState(false)
  const [error, setError] = useState('')

  async function handleSubmit(e) {
    e?.preventDefault()
    const url = arxivUrl.trim()
    if (!url || submitting) return
    setSubmitting(true)
    setError('')
    try {
      const res = await api.review.submit(url)
      const jobId = res?.job_id || res?.jobId
      if (!jobId) throw new Error(res?.detail || 'No job_id returned')
      navigate(`/review/${jobId}`)
    } catch (err) {
      setError(err.message || 'Submit failed')
      setSubmitting(false)
    }
  }

  return (
    <div className="min-h-screen w-full bg-[#0A0C10] text-[#E4E7F0] flex flex-col relative font-sans">
      <header className="w-full flex items-center px-8 py-4 border-b border-white/10 bg-[#131720]">
        <div className="text-xl font-bold tracking-wide">
          PaperCourt
        </div>
        <div className="ml-auto flex gap-6 text-sm">
          <button className="opacity-70 hover:opacity-100 hover:text-[#5B5BD6] transition-colors">Review</button>
          <button className="opacity-70 hover:opacity-100 hover:text-[#5B5BD6] transition-colors">Reader</button>
          <button className="opacity-70 hover:opacity-100 hover:text-[#5B5BD6] transition-colors">PoC</button>
          <button className="opacity-70 hover:opacity-100 hover:text-[#5B5BD6] transition-colors">Research</button>
        </div>
      </header>

      <main className="flex-1 flex flex-col items-center justify-center p-6">
        <div className="w-full max-w-xl bg-[#131720] border border-white/10 rounded-lg p-8">
          <div className="mb-8">
            <h1 className="text-2xl font-semibold mb-2">Start Review</h1>
            <p className="text-[#6B7280] text-sm">
              Enter an arXiv URL or ID to ingest the e-print source, assemble the TeX, and generate a rigorous claim-level audit.
            </p>
          </div>
          
          <form onSubmit={handleSubmit} className="flex flex-col gap-4">
            <div className="flex flex-col gap-2">
              <label htmlFor="arxivUrl" className="text-xs uppercase tracking-wider text-[#6B7280] font-semibold">
                arXiv Source
              </label>
              <div className="flex gap-3">
                <input
                  id="arxivUrl"
                  type="text"
                  value={arxivUrl}
                  onChange={(e) => setArxivUrl(e.target.value)}
                  placeholder="e.g., https://arxiv.org/abs/1706.03762"
                  disabled={submitting}
                  className="flex-1 px-4 py-2.5 rounded bg-[#0D1017] text-[#E4E7F0] text-sm border border-white/10 focus:border-[#5B5BD6] focus:outline-none focus:ring-1 focus:ring-[#5B5BD6] transition-colors placeholder:text-[#6B7280]"
                />
                <button
                  type="submit"
                  disabled={submitting || !arxivUrl.trim()}
                  className="px-6 py-2.5 rounded bg-[#5B5BD6] text-white font-medium text-sm disabled:opacity-50 disabled:cursor-not-allowed hover:bg-[#4a4ac2] transition-colors whitespace-nowrap"
                >
                  {submitting ? 'Ingesting...' : 'Begin Review'}
                </button>
              </div>
            </div>
            {error && (
              <div className="text-red-400 text-xs p-3 rounded bg-red-400/10 border border-red-400/20">
                {error}
              </div>
            )}
          </form>

          <div className="mt-8 pt-6 border-t border-white/5">
            <h3 className="text-xs uppercase tracking-wider text-[#6B7280] font-semibold mb-3">
              Verification Pipeline
            </h3>
            <ul className="text-xs text-[#6B7280] space-y-2 font-mono">
              <li className="flex gap-2 items-center">
                <span className="w-1.5 h-1.5 rounded-full bg-[#3B82F6] opacity-70"></span>
                Source Ingestion & TeX Assembly
              </li>
              <li className="flex gap-2 items-center">
                <span className="w-1.5 h-1.5 rounded-full bg-[#3B82F6] opacity-70"></span>
                Research Atom Extraction
              </li>
              <li className="flex gap-2 items-center">
                <span className="w-1.5 h-1.5 rounded-full bg-[#3B82F6] opacity-70"></span>
                Symbolic & Numeric Probes
              </li>
              <li className="flex gap-2 items-center">
                <span className="w-1.5 h-1.5 rounded-full bg-[#3B82F6] opacity-70"></span>
                Adversarial Debate & Verdict Cascade
              </li>
            </ul>
          </div>
        </div>
      </main>
    </div>
  )
}
