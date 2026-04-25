import { useState } from 'react'
import { Prism as SyntaxHighlighter } from 'react-syntax-highlighter'
import { vscDarkPlus } from 'react-syntax-highlighter/dist/esm/styles/prism'

const SCAFFOLD_FILES = ['implementation.py', 'test_harness.py', 'results_logger.py', 'README.md']

const STATUS_BANNER = {
  REPRODUCED: { bg: '#14532d', border: '#15803D', text: '#86efac', icon: '✓', msg: 'Reproduced — within tolerance' },
  PARTIAL:    { bg: '#78350f', border: '#B45309', text: '#fcd34d', icon: '⚠', msg: 'Partial — close but outside tolerance' },
  FAILED:     { bg: '#7f1d1d', border: '#DC2626', text: '#fca5a5', icon: '✗', msg: 'Failed to reproduce' },
}

const LIKELIHOOD_COLOR = {
  high:   'bg-red-900/40 text-red-300',
  medium: 'bg-amber-900/40 text-amber-300',
  low:    'bg-blue-900/40 text-blue-300',
}

function copyToClipboard(text) {
  navigator.clipboard?.writeText(text)
}

function SpecTab({ spec }) {
  if (!spec) return <div className="p-4 text-[#4b5563] text-xs">Loading spec...</div>
  return (
    <div className="p-3 overflow-y-auto text-xs text-[#94a3b8]">
      <div className="mb-3">
        <div className="text-[10px] text-[#4b5563] tracking-widest mb-1">CLAIM TEXT</div>
        <pre className="bg-[#1a1f2a] rounded p-2 text-[#e2e8f0] whitespace-pre-wrap font-mono text-[11px] leading-relaxed">
          {spec.claim_id}
        </pre>
      </div>

      {spec.success_criteria?.length > 0 && (
        <div className="mb-3">
          <div className="text-[10px] text-[#4b5563] tracking-widest mb-1">SUCCESS CRITERIA</div>
          <table className="w-full text-[10px]">
            <thead>
              <tr className="text-[#4b5563] border-b border-[#2a2e3f]">
                <th className="text-left py-1 pr-2">Metric</th>
                <th className="text-left py-1 pr-2">Paper Value</th>
                <th className="text-left py-1 pr-2">Threshold</th>
                <th className="text-left py-1 pr-2">Tolerance</th>
                <th className="text-left py-1">Comparison</th>
              </tr>
            </thead>
            <tbody>
              {spec.success_criteria.map((c, i) => (
                <tr key={i} className="border-b border-[#1e2433] text-[#94a3b8]">
                  <td className="py-1 pr-2 font-mono text-[#a3e635]">{c.metric_name}</td>
                  <td className="py-1 pr-2">{c.paper_reported_value}</td>
                  <td className="py-1 pr-2">{c.numeric_threshold ?? '—'}</td>
                  <td className="py-1 pr-2">{c.tolerance ?? '—'}</td>
                  <td className="py-1">{c.comparison}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {spec.failure_criteria?.length > 0 && (
        <details className="mb-3">
          <summary className="text-[10px] text-[#4b5563] tracking-widest cursor-pointer mb-1">FAILURE CRITERIA ▶</summary>
          <div className="pl-2 mt-1">
            {spec.failure_criteria.map((c, i) => (
              <div key={i} className="text-[10px] text-[#64748b] py-0.5">• {JSON.stringify(c)}</div>
            ))}
          </div>
        </details>
      )}
    </div>
  )
}

function CodeTab({ spec }) {
  const [selectedFile, setSelectedFile] = useState(SCAFFOLD_FILES[0])
  if (!spec?.scaffold_files) return <div className="p-4 text-[#4b5563] text-xs">No scaffold files yet</div>

  const files = SCAFFOLD_FILES.filter(f => spec.scaffold_files[f])
  const code = spec.scaffold_files[selectedFile] || ''
  const lang = selectedFile.endsWith('.md') ? 'markdown' : 'python'

  return (
    <div className="flex flex-col h-full">
      <div className="flex gap-1 px-2 pt-2 flex-wrap border-b border-[#2a2e3f] pb-1">
        {files.map(f => (
          <button
            key={f}
            onClick={() => setSelectedFile(f)}
            className={`text-[10px] px-2 py-1 rounded font-mono transition-all ${
              selectedFile === f
                ? 'bg-[#a3e635]/20 text-[#a3e635] border border-[#a3e635]/40'
                : 'text-[#4b5563] hover:text-[#94a3b8]'
            }`}
          >
            {f}
          </button>
        ))}
      </div>
      <div className="relative flex-1 overflow-auto">
        <button
          className="absolute top-2 right-2 z-10 text-[10px] text-[#4b5563] hover:text-[#94a3b8] bg-[#1a1f2a] border border-[#2a2e3f] px-2 py-0.5 rounded"
          onClick={() => copyToClipboard(code)}
        >
          Copy
        </button>
        <SyntaxHighlighter
          language={lang}
          style={vscDarkPlus}
          customStyle={{ margin: 0, background: '#0d1117', fontSize: '11px', minHeight: '100%' }}
          showLineNumbers
        >
          {code}
        </SyntaxHighlighter>
      </div>
    </div>
  )
}

function ResultsTab({ claimId, report }) {
  if (!report?.results) {
    return (
      <div className="p-4 text-center">
        <div className="text-[#4b5563] text-xs">No results yet.</div>
        <div className="text-[#374151] text-[10px] mt-1">Upload results to see reproduction status.</div>
      </div>
    )
  }

  const claimResults = report.results.filter(r => r.claim_id === claimId)
  if (!claimResults.length) {
    return <div className="p-4 text-[#4b5563] text-xs">No results for this claim.</div>
  }

  const rankOf = { REPRODUCED: 0, PARTIAL: 1, FAILED: 2 }
  const worstStatus = claimResults.reduce((worst, r) =>
    (rankOf[r.status] ?? 0) > (rankOf[worst] ?? 0) ? r.status : worst,
    claimResults[0].status
  )
  const banner = STATUS_BANNER[worstStatus]

  const gapAnalyses = (report.gap_analyses || []).filter(g => g.claim_id === claimId)
  const whatToTry = report.what_to_try_next || []

  return (
    <div className="p-3 overflow-y-auto text-xs">
      {banner && (
        <div className="rounded-lg px-3 py-2 mb-3 border" style={{ background: banner.bg, borderColor: banner.border }}>
          <span style={{ color: banner.text }} className="font-bold text-sm">
            {banner.icon} {banner.msg}
          </span>
        </div>
      )}

      {/* Metric table */}
      <div className="mb-3">
        <div className="text-[10px] text-[#4b5563] tracking-widest mb-1">METRICS</div>
        <table className="w-full text-[10px]">
          <thead>
            <tr className="text-[#4b5563] border-b border-[#2a2e3f]">
              <th className="text-left py-1 pr-2">Metric</th>
              <th className="text-left py-1 pr-2">Paper</th>
              <th className="text-left py-1 pr-2">Achieved</th>
              <th className="text-left py-1 pr-2">Delta</th>
              <th className="text-left py-1">Status</th>
            </tr>
          </thead>
          <tbody>
            {claimResults.map((r, i) => (
              <tr key={i} className="border-b border-[#1e2433] text-[#94a3b8]">
                <td className="py-1 pr-2 font-mono text-[#a3e635]">{r.metric_name}</td>
                <td className="py-1 pr-2">—</td>
                <td className="py-1 pr-2">{r.achieved_value?.toFixed?.(3) ?? r.achieved_value}</td>
                <td className="py-1 pr-2" style={{ color: (r.delta ?? 0) >= 0 ? '#86efac' : '#fca5a5' }}>
                  {r.delta != null ? (r.delta >= 0 ? '+' : '') + r.delta.toFixed(3) : '—'}
                </td>
                <td className="py-1">
                  <span className={`px-1.5 py-0.5 rounded text-[9px] font-bold ${
                    r.status === 'REPRODUCED' ? 'bg-green-900/40 text-green-300' :
                    r.status === 'PARTIAL' ? 'bg-amber-900/40 text-amber-300' :
                    'bg-red-900/40 text-red-300'
                  }`}>{r.status}</span>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {/* Gap analysis */}
      {gapAnalyses.length > 0 && (
        <div className="mb-3">
          <div className="text-[10px] text-[#4b5563] tracking-widest mb-1">GAP ANALYSIS</div>
          {gapAnalyses.map((g, i) => (
            <div key={i} className="bg-[#1a1f2a] rounded p-2 mb-1.5">
              <div className="flex items-start justify-between gap-2 mb-1">
                <span className="text-[#cbd5e1] leading-snug">{g.explanation}</span>
                <span className={`text-[9px] font-bold px-1.5 py-0.5 rounded flex-shrink-0 ${LIKELIHOOD_COLOR[g.likelihood] || LIKELIHOOD_COLOR.low}`}>
                  {g.likelihood}
                </span>
              </div>
              {g.suggested_fix && (
                <div className="text-[10px] text-[#4b5563]">Fix: {g.suggested_fix}</div>
              )}
            </div>
          ))}
        </div>
      )}

      {/* What to try next */}
      {whatToTry.length > 0 && (
        <div>
          <div className="text-[10px] text-[#4b5563] tracking-widest mb-1">WHAT TO TRY NEXT</div>
          <ol className="list-decimal list-inside space-y-1 text-[#94a3b8]">
            {whatToTry.map((step, i) => (
              <li key={i} className="leading-snug">{step}</li>
            ))}
          </ol>
        </div>
      )}
    </div>
  )
}

export default function SpecPanel({ claimId, claims, specData, report, onClose }) {
  const [tab, setTab] = useState('spec')
  const claimInfo = (claims?.claims || []).find(c => c.claim_id === claimId)

  return (
    <div className="flex flex-col h-full" style={{ background: '#14181f' }}>
      {/* Header */}
      <div className="px-3 py-2.5 border-b border-[#2a2e3f] flex items-start justify-between gap-2">
        <div>
          <div className="text-[10px] text-[#a3e635] tracking-widest font-bold">CLAIM SPEC</div>
          <div className="text-xs font-mono text-[#94a3b8] mt-0.5 truncate">{claimId}</div>
          {claimInfo?.text && (
            <div className="text-[10px] text-[#4b5563] mt-0.5 line-clamp-2 leading-snug">{claimInfo.text}</div>
          )}
        </div>
        <button onClick={onClose} className="text-[#4b5563] hover:text-[#94a3b8] text-lg leading-none flex-shrink-0 mt-0.5">×</button>
      </div>

      {/* Tabs */}
      <div className="flex border-b border-[#2a2e3f]">
        {['spec', 'code', 'results'].map(t => (
          <button
            key={t}
            onClick={() => setTab(t)}
            className={`flex-1 py-2 text-[10px] tracking-widest font-bold uppercase transition-all ${
              tab === t
                ? 'text-[#a3e635] border-b-2 border-[#a3e635]'
                : 'text-[#4b5563] hover:text-[#94a3b8]'
            }`}
          >
            {t}
          </button>
        ))}
      </div>

      {/* Tab content */}
      <div className="flex-1 overflow-hidden">
        {tab === 'spec'    && <SpecTab spec={specData} />}
        {tab === 'code'    && <CodeTab spec={specData} />}
        {tab === 'results' && <ResultsTab claimId={claimId} report={report} />}
      </div>
    </div>
  )
}
