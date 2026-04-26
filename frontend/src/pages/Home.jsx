import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { api } from '../api/client'

const MODES = {
  review: {
    label: 'Review',
    title: 'Start Review',
    description: 'Ingest a paper, extract source-grounded atoms, build a dependency DAG, and run adversarial verification.',
    card: 'Adversarial verification DAG',
    cta: 'Begin Review',
    accent: '#5B5BD6',
    pipeline: ['Source Ingestion & TeX Assembly', 'Research Atom Extraction', 'Symbolic & Numeric Probes', 'Adversarial Debate & Verdict Cascade'],
  },
  reader: {
    label: 'Learner',
    title: 'Start Learner Mode',
    description: 'Build an educational graph, then click atoms for explanations, exercises, prerequisites, and a scoped tutor.',
    card: 'Explanations, exercises, tutor',
    cta: 'Begin Learner',
    accent: '#00AFA3',
    pipeline: ['Source Ingestion & TeX Assembly', 'Research Atom Extraction', 'Dependency Graph', 'Lazy Explanations, Exercises & Tutor'],
  },
  poc: {
    label: 'PoC',
    title: 'Start PoC Mode',
    description: 'Generate proof-of-concept scaffolds for key claims, with test harnesses and reproducibility analysis.',
    card: 'Proof-of-concept scaffold',
    cta: 'Begin PoC',
    accent: '#5B5BD6',
    pipeline: ['Source Ingestion & TeX Assembly', 'Claim Extraction', 'PoC Scaffold Generation', 'Test Harness & Repro Analysis'],
  },
  research: {
    label: 'Research',
    title: 'Start Research Mode',
    description: 'Run a monitored research deep dive with investigator agents, literature search, critique, synthesis, and novelty proposals.',
    card: 'Literature deep dive',
    cta: 'Open Research Launcher',
    accent: '#67E8F9',
    pipeline: ['Research Objective Setup', 'Investigator Planning', 'Literature Search Agents', 'Critique, Synthesis & Final Report'],
  },
}

export default function Home() {
  const navigate = useNavigate()
  const [arxivUrl, setArxivUrl] = useState('')
  const [mode, setMode] = useState('review')
  const [level, setLevel] = useState('undergraduate')
  const [submitting, setSubmitting] = useState(false)
  const [error, setError] = useState('')
  const active = MODES[mode]

  function scrollToSection(sectionId) {
    const target = document.getElementById(sectionId)
    if (!target) return

    const start = window.scrollY
    const end = target.getBoundingClientRect().top + window.scrollY
    const distance = end - start
    const duration = 750
    const startedAt = performance.now()

    function step(now) {
      const progress = Math.min((now - startedAt) / duration, 1)
      const eased = 1 - Math.pow(1 - progress, 3)
      window.scrollTo(0, start + distance * eased)
      if (progress < 1) requestAnimationFrame(step)
    }

    requestAnimationFrame(step)
  }

  function scrollToOverview() {
    scrollToSection('overview')
  }

  function selectModeAndScroll(key) {
    setMode(key)
    scrollToSection('try-it-out')
  }

  async function handleSubmit(e) {
    e?.preventDefault()
    if (mode === 'research') {
      navigate('/research')
      return
    }

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
      if (mode === 'poc') {
        const res = await api.poc.submit(url)
        const sessionId = res?.session_id || res?.sessionId
        if (!sessionId) throw new Error(res?.detail || 'No session_id returned')
        navigate(`/poc/${sessionId}`)
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
    <div className="min-h-screen w-full overflow-hidden scroll-smooth bg-[#080B10] text-[#E4E7F0] font-sans">
      <div className="pointer-events-none fixed inset-0 opacity-80">
        <div className="absolute left-[-12%] top-[-18%] h-[420px] w-[420px] rounded-full bg-[#5B5BD6]/25 blur-3xl" />
        <div className="absolute bottom-[-18%] right-[-10%] h-[460px] w-[460px] rounded-full bg-[#00AFA3]/20 blur-3xl" />
        <div className="absolute inset-0 bg-[radial-gradient(circle_at_top,rgba(255,255,255,0.06),transparent_34%),linear-gradient(135deg,rgba(255,255,255,0.06)_1px,transparent_1px)] bg-[length:auto,38px_38px]" />
      </div>

      <main className="relative z-10">
        <section className="mx-auto flex min-h-screen max-w-6xl flex-col items-center justify-center px-6 py-16 text-center">
          <h1 className="text-7xl font-bold leading-none tracking-[-0.08em] text-white sm:text-9xl">
            Veritas
          </h1>
          <p className="mt-6 max-w-xl text-base leading-7 text-[#AAB4C2] sm:text-lg">
            Transform research papers into educational graphs for review, learning, prototyping, and discovery.
          </p>
          <button
            type="button"
            onClick={scrollToOverview}
            className="mt-10 rounded bg-[#67E8F9] px-7 py-3 text-sm font-semibold text-[#081113] shadow-[0_0_30px_rgba(103,232,249,0.22)] transition hover:bg-[#22D3EE]"
          >
            Try it out
          </button>
        </section>

        <section id="overview" className="mx-auto flex min-h-screen max-w-6xl flex-col justify-center px-6 py-20">
          <div className="max-w-4xl">
            <div className="mb-5 inline-flex rounded-full border border-white/10 bg-white/5 px-3 py-1 text-xs font-semibold uppercase tracking-[0.22em] text-[#67E8F9]">
              Scientific papers, made interrogable
            </div>
            <h2 className="max-w-4xl text-5xl font-bold leading-[0.98] tracking-[-0.05em] text-white sm:text-7xl">
              Turn papers into educational graphs.
            </h2>
            <p className="mt-6 max-w-2xl text-lg leading-8 text-[#AAB4C2]">
              Review claims, learn ideas, build proof-of-concept scaffolds, or launch a monitored research deep dive from the same arXiv source.
            </p>
          </div>

          <div className="mt-14 grid gap-4 md:grid-cols-4">
            {Object.entries(MODES).map(([key, item]) => (
              <button
                key={key}
                onClick={() => selectModeAndScroll(key)}
                className={`rounded-xl border p-4 text-left transition ${mode === key ? 'border-[#67E8F9]/70 bg-[#67E8F9]/10' : 'border-white/10 bg-white/[0.04] hover:border-white/25'}`}
              >
                <div className="text-sm font-semibold text-white">{item.label}</div>
                <div className="mt-2 text-xs leading-5 text-[#8E98A8]">{item.card}</div>
              </button>
            ))}
          </div>
        </section>

        <section id="try-it-out" className="mx-auto flex min-h-screen max-w-6xl flex-col justify-center px-6 py-20">
          <div className="rounded-2xl border border-white/10 bg-[#111722]/90 p-8 shadow-2xl shadow-black/20 backdrop-blur">
            <div className="mb-8">
              <h2 className="text-3xl font-semibold tracking-tight">{active.title}</h2>
              <p className="mt-3 text-sm leading-6 text-[#8E98A8]">{active.description}</p>
            </div>

            <form onSubmit={handleSubmit} className="flex flex-col gap-4">
              <div className="grid grid-cols-2 gap-3 sm:grid-cols-4">
                {Object.entries(MODES).map(([key, item]) => (
                  <button
                    key={key}
                    type="button"
                    onClick={() => setMode(key)}
                    className={`rounded border px-4 py-3 text-left transition-colors ${mode === key ? 'border-[#67E8F9] bg-[#67E8F9]/15' : 'border-white/10 bg-[#0D1017] hover:border-white/20'}`}
                  >
                    <div className="text-sm font-semibold">{item.label}</div>
                    <div className="mt-1 text-xs text-[#6B7280]">{item.card}</div>
                  </button>
                ))}
              </div>

              {mode === 'reader' && (
                <div className="flex flex-col gap-2">
                  <label htmlFor="level" className="text-xs font-semibold uppercase tracking-wider text-[#6B7280]">
                    Comprehension level
                  </label>
                  <select
                    id="level"
                    value={level}
                    onChange={(e) => setLevel(e.target.value)}
                    className="rounded border border-white/10 bg-[#0D1017] px-4 py-2.5 text-sm text-[#E4E7F0] outline-none transition-colors focus:border-[#00AFA3] focus:ring-1 focus:ring-[#00AFA3]"
                  >
                    <option value="layperson">Layperson</option>
                    <option value="undergraduate">Undergraduate</option>
                    <option value="graduate">Graduate</option>
                    <option value="expert">Expert</option>
                  </select>
                </div>
              )}

              {mode === 'research' ? (
                <button
                  type="submit"
                  className="rounded bg-[#67E8F9] px-6 py-2.5 text-sm font-semibold text-[#081113] transition-colors hover:bg-[#22D3EE]"
                >
                  {active.cta}
                </button>
              ) : (
                <div className="flex flex-col gap-2">
                  <label htmlFor="arxivUrl" className="text-xs font-semibold uppercase tracking-wider text-[#6B7280]">
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
                      className="flex-1 rounded border border-white/10 bg-[#0D1017] px-4 py-2.5 text-sm text-[#E4E7F0] outline-none transition-colors placeholder:text-[#6B7280] focus:border-[#67E8F9] focus:ring-1 focus:ring-[#67E8F9]"
                    />
                  <button
                    type="submit"
                    disabled={submitting || !arxivUrl.trim()}
                    className="whitespace-nowrap rounded bg-[#5B5BD6] px-6 py-2.5 text-sm font-semibold text-white transition-colors hover:bg-[#4a4ac2] disabled:cursor-not-allowed disabled:opacity-50"
                  >
                    {submitting ? 'Ingesting...' : active.cta}
                  </button>
                  </div>
                </div>
              )}

              {error && (
                <div className="rounded border border-red-400/20 bg-red-400/10 p-3 text-xs text-red-400">
                  {error}
                </div>
              )}
            </form>
          </div>
        </section>

        <footer className="mx-auto max-w-6xl px-6 pb-8 text-center text-xs text-[#6B7280]">
          © 2026 Veritas. All rights reserved.
        </footer>
      </main>
    </div>
  )
}
