import { useEffect, useState } from 'react'
import ReactMarkdown from 'react-markdown'
import remarkGfm from 'remark-gfm'
import { api } from '../../api/client'

export default function ReproducibilityReportView({ sessionId, report, onClose }) {
  const [markdown, setMarkdown] = useState(report?.markdown_report || '')
  const [loading, setLoading] = useState(!report?.markdown_report)

  useEffect(() => {
    if (!report?.markdown_report && sessionId) {
      setLoading(true)
      api.poc.reportMarkdown(sessionId)
        .then(md => { setMarkdown(md); setLoading(false) })
        .catch(() => setLoading(false))
    }
  }, [sessionId, report])

  function downloadMarkdown() {
    const blob = new Blob([markdown], { type: 'text/markdown' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `reproducibility_report_${sessionId}.md`
    a.click()
    URL.revokeObjectURL(url)
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center" style={{ background: 'rgba(0,0,0,0.8)' }}>
      <div className="relative rounded-xl border border-[#2a2e3f] w-[700px] max-h-[85vh] flex flex-col" style={{ background: '#14181f' }}>
        {/* Header */}
        <div className="flex items-center justify-between px-5 py-3 border-b border-[#2a2e3f]">
          <div>
            <div className="text-xs text-[#a3e635] tracking-widest font-bold">REPRODUCIBILITY REPORT</div>
            {report && (
              <div className="text-[10px] text-[#94a3b8] mt-0.5">
                Rate: <span style={{ color: report.reproduction_rate >= 0.8 ? '#86efac' : report.reproduction_rate >= 0.4 ? '#fcd34d' : '#fca5a5' }}>
                  {(report.reproduction_rate * 100).toFixed(0)}%
                </span>
                {' · '}
                {report.reproduced ?? 0} reproduced · {report.partial ?? 0} partial · {report.failed ?? 0} failed
              </div>
            )}
          </div>
          <div className="flex items-center gap-2">
            <button
              onClick={downloadMarkdown}
              disabled={!markdown}
              className="text-[10px] px-3 py-1.5 rounded border border-[#2a2e3f] text-[#94a3b8] hover:text-[#a3e635] hover:border-[#a3e635]/40 transition-all"
            >
              Export .md
            </button>
            <button onClick={onClose} className="text-[#4b5563] hover:text-white text-xl leading-none">×</button>
          </div>
        </div>

        <div className="flex-1 overflow-y-auto p-5">
          {loading ? (
            <div className="flex items-center justify-center py-12">
              <div className="w-6 h-6 border-2 border-[#a3e635] border-t-transparent rounded-full animate-spin" />
            </div>
          ) : markdown ? (
            <div className="prose prose-invert prose-sm max-w-none" style={{ color: '#cbd5e1' }}>
              <ReactMarkdown
                remarkPlugins={[remarkGfm]}
                components={{
                  h1: ({ children }) => <h1 className="text-xl font-bold text-[#a3e635] mb-3">{children}</h1>,
                  h2: ({ children }) => <h2 className="text-base font-bold text-[#86efac] mt-4 mb-2">{children}</h2>,
                  h3: ({ children }) => <h3 className="text-sm font-bold text-[#94a3b8] mt-3 mb-1">{children}</h3>,
                  p: ({ children }) => <p className="text-[#94a3b8] text-sm leading-relaxed mb-2">{children}</p>,
                  code: ({ inline, children }) => inline
                    ? <code className="bg-[#1a1f2a] px-1 py-0.5 rounded text-[#a3e635] text-[11px] font-mono">{children}</code>
                    : <pre className="bg-[#0d1117] rounded p-3 text-[11px] font-mono text-[#94a3b8] overflow-x-auto mb-2"><code>{children}</code></pre>,
                  table: ({ children }) => <table className="w-full text-[11px] border-collapse mb-3">{children}</table>,
                  th: ({ children }) => <th className="text-left py-1 px-2 border-b border-[#2a2e3f] text-[#4b5563]">{children}</th>,
                  td: ({ children }) => <td className="py-1 px-2 border-b border-[#1e2433] text-[#94a3b8]">{children}</td>,
                  li: ({ children }) => <li className="text-[#94a3b8] text-sm leading-snug">{children}</li>,
                }}
              >
                {markdown}
              </ReactMarkdown>
            </div>
          ) : (
            <div className="text-center text-[#4b5563] py-12 text-sm">Report not available yet.</div>
          )}
        </div>
      </div>
    </div>
  )
}
