import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { api } from '../api/client'

export default function Home() {
  const navigate = useNavigate()
  const [arxivUrl, setArxivUrl] = useState('')
  const [mode, setMode] = useState('review')
  const [level, setLevel] = useState('undergraduate')
  const [submitting, setSubmitting] = useState(false)
  const [error, setError] = useState('')

  async function handleSubmit(e) {
    e?.preventDefault()
    const url = arxivUrl.trim()
    if (!url || submitting) return
    setSubmitting(true)
    setError('')
    try {
      if (mode === 'reader') {
        const res = await api.reader.submit(url, level)
        const sessionId = res?.session_id || res?.sessionId
        if (!sessionId) throw new Error(res?.detail || 'No session_id returned')
        navigate(`/read/${sessionId}`)
        return
      }

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
          <button onClick={() => setMode('review')} className={`${mode === 'review' ? 'text-[#5B5BD6] opacity-100' : 'opacity-70'} hover:opacity-100 hover:text-[#5B5BD6] transition-colors`}>Review</button>
          <button onClick={() => setMode('reader')} className={`${mode === 'reader' ? 'text-[#5B5BD6] opacity-100' : 'opacity-70'} hover:opacity-100 hover:text-[#5B5BD6] transition-colors`}>Reader</button>
          <button className="opacity-70 hover:opacity-100 hover:text-[#5B5BD6] transition-colors">PoC</button>
          <button className="opacity-70 hover:opacity-100 hover:text-[#5B5BD6] transition-colors">Research</button>
        </div>
      </header>

      <main className="flex-1 flex flex-col items-center justify-center p-6">
        <div className="w-full max-w-xl bg-[#131720] border border-white/10 rounded-lg p-8">
          <div className="mb-8">
            <h1 className="text-2xl font-semibold mb-2">{mode === 'reader' ? 'Start Learner Mode' : 'Start Review'}</h1>
            <p className="text-[#6B7280] text-sm">
              {mode === 'reader'
                ? 'Enter an arXiv URL or ID to build a concept graph, then click atoms for explanations, exercises, and a scoped tutor.'
                : 'Enter an arXiv URL or ID to ingest the e-print source, assemble the TeX, and generate a rigorous claim-level audit.'}
            </p>
          </div>
          
          <form onSubmit={handleSubmit} className="flex flex-col gap-4">
            <div className="grid grid-cols-2 gap-3">
              <button
                type="button"
                onClick={() => setMode('review')}
                className={`rounded border px-4 py-3 text-left transition-colors ${mode === 'review' ? 'border-[#5B5BD6] bg-[#5B5BD6]/15' : 'border-white/10 bg-[#0D1017] hover:border-white/20'}`}
              >
                <div className="text-sm font-semibold">Review</div>
                <div className="text-xs text-[#6B7280] mt-1">Adversarial verification DAG</div>
              </button>
              <button
                type="button"
                onClick={() => setMode('reader')}
                className={`rounded border px-4 py-3 text-left transition-colors ${mode === 'reader' ? 'border-[#00AFA3] bg-[#00AFA3]/15' : 'border-white/10 bg-[#0D1017] hover:border-white/20'}`}
              >
                <div className="text-sm font-semibold">Learner</div>
                <div className="text-xs text-[#6B7280] mt-1">Explanations, exercises, tutor</div>
              </button>
            </div>

            {mode === 'reader' && (
              <div className="flex flex-col gap-2">
                <label htmlFor="level" className="text-xs uppercase tracking-wider text-[#6B7280] font-semibold">
                  Comprehension level
                </label>
                <select
                  id="level"
                  value={level}
                  onChange={(e) => setLevel(e.target.value)}
                  className="px-4 py-2.5 rounded bg-[#0D1017] text-[#E4E7F0] text-sm border border-white/10 focus:border-[#00AFA3] focus:outline-none focus:ring-1 focus:ring-[#00AFA3] transition-colors"
                >
                  <option value="layperson">Layperson</option>
                  <option value="undergraduate">Undergraduate</option>
                  <option value="graduate">Graduate</option>
                  <option value="expert">Expert</option>
                </select>
              </div>
            )}

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
                  {submitting ? 'Ingesting...' : mode === 'reader' ? 'Begin Learner' : 'Begin Review'}
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
              {mode === 'reader' ? 'Learner Pipeline' : 'Verification Pipeline'}
            </h3>
            <ul className="text-xs text-[#6B7280] space-y-2 font-mono">
              {(mode === 'reader'
                ? ['Source Ingestion & TeX Assembly', 'Research Atom Extraction', 'Dependency Graph', 'Lazy Explanations, Exercises & Tutor']
                : ['Source Ingestion & TeX Assembly', 'Research Atom Extraction', 'Symbolic & Numeric Probes', 'Adversarial Debate & Verdict Cascade']
              ).map(item => (
                <li key={item} className="flex gap-2 items-center">
                  <span className={`w-1.5 h-1.5 rounded-full ${mode === 'reader' ? 'bg-[#00AFA3]' : 'bg-[#3B82F6]'} opacity-70`}></span>
                  {item}
                </li>
              ))}
            </ul>
          </div>
        </div>
      </main>
    </div>
  )
}
