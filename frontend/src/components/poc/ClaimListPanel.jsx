const STATUS_COLOR = {
  PENDING:    '#93c5fd',
  REPRODUCED: '#86efac',
  PARTIAL:    '#fcd34d',
  FAILED:     '#fca5a5',
}

const STATUS_BG = {
  PENDING:    'bg-blue-900/40 text-blue-300',
  REPRODUCED: 'bg-green-900/40 text-green-300',
  PARTIAL:    'bg-amber-900/40 text-amber-300',
  FAILED:     'bg-red-900/40 text-red-300',
}

export default function ClaimListPanel({ claims = {}, report, onClaimClick, onDownloadScaffold, onUploadResults, onViewReport }) {
  const claimsArr = claims.claims || []
  const testable = claimsArr.filter(c => c.testability === 'testable')

  const reproduced = report ? (report.reproduced ?? 0) : 0
  const partial    = report ? (report.partial    ?? 0) : 0
  const failed     = report ? (report.failed     ?? 0) : 0

  const claimStatusMap = {}
  if (report?.results) {
    report.results.forEach(r => {
      const prev = claimStatusMap[r.claim_id]
      const rank = { REPRODUCED: 0, PARTIAL: 1, FAILED: 2, PENDING: -1 }
      if (!prev || (rank[r.status] ?? -1) > (rank[prev] ?? -1)) {
        claimStatusMap[r.claim_id] = r.status
      }
    })
  }

  return (
    <div className="flex flex-col h-full" style={{ background: '#14181f' }}>
      {/* Header */}
      <div className="px-4 py-3 border-b border-[#2a2e3f]">
        <div className="text-xs text-[#a3e635] tracking-widest font-bold mb-1">POC CLAIMS</div>
        <div className="text-[11px] text-[#94a3b8]">
          <span className="text-white font-semibold">{claims.testable ?? 0}</span> testable
          {' · '}
          <span style={{ color: '#86efac' }}>{reproduced}</span> reproduced
          {' · '}
          <span style={{ color: '#fcd34d' }}>{partial}</span> partial
          {' · '}
          <span style={{ color: '#fca5a5' }}>{failed}</span> failed
        </div>
      </div>

      {/* Claims list */}
      <div className="flex-1 overflow-y-auto px-2 py-2">
        {testable.length === 0 && (
          <div className="text-center text-[#374151] text-xs py-8">
            {claims.total === 0 ? 'Processing claims...' : 'No testable claims found'}
          </div>
        )}
        {testable.map(claim => {
          const status = claimStatusMap[claim.claim_id] || 'PENDING'
          const criterion = claim.spec_summary?.success_criteria?.[0]
          return (
            <button
              key={claim.claim_id}
              className="w-full text-left px-3 py-2.5 mb-1.5 rounded-lg border transition-all hover:border-[#a3e635]/40"
              style={{ background: '#1a1f2a', borderColor: '#2a2e3f' }}
              onClick={() => onClaimClick(claim.claim_id)}
            >
              <div className="flex items-center justify-between gap-2 mb-1">
                <span className="text-[11px] font-mono text-[#94a3b8] truncate">{claim.claim_id}</span>
                <span className={`text-[9px] font-bold px-1.5 py-0.5 rounded tracking-wider flex-shrink-0 ${STATUS_BG[status] || STATUS_BG.PENDING}`}>
                  {status}
                </span>
              </div>
              <div className="text-xs text-[#64748b] leading-snug line-clamp-2">{claim.text}</div>
              {criterion && (
                <div className="text-[10px] text-[#4b5563] mt-1 truncate">
                  {criterion.metric_name}: {criterion.paper_reported_value}
                </div>
              )}
            </button>
          )
        })}
      </div>

      {/* CTAs */}
      <div className="px-3 py-3 border-t border-[#2a2e3f] flex flex-col gap-2">
        {report && (
          <button
            className="w-full py-2 rounded-lg text-xs font-bold tracking-widest text-[#a3e635] border border-[#a3e635]/30 hover:bg-[#a3e635]/10 transition-all"
            onClick={onViewReport}
          >
            VIEW FULL REPORT
          </button>
        )}
        <div className="flex gap-2">
          <a
            className="flex-1 py-2 rounded-lg text-xs font-bold tracking-wider text-center text-[#93c5fd] border border-[#1D4ED8]/40 hover:bg-[#1D4ED8]/10 transition-all cursor-pointer"
            onClick={onDownloadScaffold}
          >
            ↓ SCAFFOLD.ZIP
          </a>
          <button
            className="flex-1 py-2 rounded-lg text-xs font-bold tracking-wider text-[#b388ff] border border-[#b388ff]/40 hover:bg-[#b388ff]/10 transition-all"
            onClick={onUploadResults}
          >
            ↑ UPLOAD RESULTS
          </button>
        </div>
      </div>
    </div>
  )
}
