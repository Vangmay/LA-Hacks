
import { useState, useEffect, useRef } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { api } from '../api/client';
import Chip from '../components/Chip';
import SectionLabel from '../components/SectionLabel';
import TestabilityChip from '../components/TestabilityChip';
import ReproChip from '../components/ReproChip';

const C = {
  bg:      '#0A0C10',
  surface: '#131720',
  sunken:  '#0D1017',
  border:  'rgba(255,255,255,0.08)',
  text:    '#E4E7F0',
  muted:   '#6B7280',
  indigo:  '#5B5BD6',
  cyan:    '#00eaff',
  purple:  '#b388ff',
};

function mono(size = 11, weight = 400) {
  return { fontFamily: 'JetBrains Mono, monospace', fontSize: size, fontWeight: weight };
}
function grotesk(size = 13, weight = 400) {
  return { fontFamily: 'Space Grotesk, sans-serif', fontSize: size, fontWeight: weight };
}

function ClaimRow({ claim, selected, reproStatus, onClick, checkable, checked, onCheckChange }) {
  const stop = (e) => e.stopPropagation()
  return (
    <div
      onClick={onClick}
      style={{
        padding: '8px 12px',
        borderBottom: `1px solid ${C.border}`,
        borderLeft: `2px solid ${selected ? C.indigo : 'transparent'}`,
        background: selected ? 'rgba(91,91,214,0.10)' : 'transparent',
        cursor: 'pointer',
        transition: 'background 0.15s',
        display: 'flex',
        gap: 8,
      }}
    >
      {checkable ? (
        <input
          type="checkbox"
          checked={!!checked}
          onClick={stop}
          onChange={(e) => onCheckChange?.(e.target.checked)}
          style={{ marginTop: 2, accentColor: C.indigo, cursor: 'pointer' }}
        />
      ) : (
        <span style={{ width: 13, flexShrink: 0 }} />
      )}
      <div style={{ flex: 1, minWidth: 0 }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 5, flexWrap: 'wrap', marginBottom: 4 }}>
          <TestabilityChip testability={claim.testability} />
          {claim.has_scaffold && (
            <span style={{ ...mono(8), color: '#22C55E', background: 'rgba(34,197,94,0.10)', border: '1px solid rgba(34,197,94,0.25)', padding: '1px 5px', borderRadius: 2 }}>✓ scaffold</span>
          )}
          <ReproChip status={reproStatus} />
        </div>
        <div style={{ ...mono(10), color: C.muted, marginBottom: 3 }}>{claim.claim_id}</div>
        <div style={{ ...grotesk(12), color: C.text, lineHeight: 1.45, overflow: 'hidden', display: '-webkit-box', WebkitLineClamp: 2, WebkitBoxOrient: 'vertical' }}>{claim.text}</div>
      </div>
    </div>
  );
}

function SuccessCriterion({ c }) {
  return (
    <div style={{
      padding: '8px 10px',
      background: C.sunken,
      border: `1px solid ${C.border}`,
      borderRadius: 4,
      marginBottom: 6,
    }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', gap: 8 }}>
        <div style={{ fontFamily: 'Space Grotesk, sans-serif', fontSize: 12, color: C.text, flex: 1, lineHeight: 1.4 }}>
          {c.metric_name || c.description || '—'}
        </div>
        <div style={{ fontFamily: 'JetBrains Mono, monospace', fontSize: 11, color: C.indigo, flexShrink: 0, fontWeight: 700 }}>
          {c.comparison} {c.threshold}
        </div>
      </div>
      {c.paper_reported_value !== undefined && (
        <div style={{ fontFamily: 'JetBrains Mono, monospace', fontSize: 10, color: C.muted, marginTop: 4 }}>
          paper reports: {c.paper_reported_value}
          {c.tolerance ? ` ± ${c.tolerance}` : ''}
        </div>
      )}
    </div>
  )
}

function ScaffoldFileRow({ name, selected, onClick }) {
  const ext = name.includes('.') ? name.split('.').pop() : ''
  const baseName = name.includes('.') ? name.slice(0, name.lastIndexOf('.')) : name
  const extColor = { py: C.cyan, md: C.purple, txt: C.muted }[ext] || C.muted
  return (
    <div
      onClick={onClick}
      style={{
        padding: '7px 10px',
        cursor: 'pointer',
        background: selected ? 'rgba(0,234,255,0.07)' : 'transparent',
        borderLeft: `2px solid ${selected ? C.cyan : 'transparent'}`,
        display: 'flex', alignItems: 'center', gap: 7,
        transition: 'background 0.12s',
      }}
    >
      <span style={{
        ...mono(9),
        color: extColor,
        minWidth: 26,
        textAlign: 'center',
        background: 'rgba(255,255,255,0.06)',
        padding: '1px 4px',
        borderRadius: 2,
        flexShrink: 0,
      }}>{ext || '?'}</span>
      <span style={{ ...mono(10), color: selected ? C.text : C.muted, whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>{baseName}</span>
    </div>
  )
}

function ReportPanel({ report }) {
  if (!report) return null
  return (
    <div style={{
      marginTop: 20,
      padding: '12px 14px',
      background: C.sunken,
      border: `1px solid ${C.border}`,
      borderRadius: 4,
    }}>
      <SectionLabel>Reproducibility Report</SectionLabel>
      {report.summary && (
        <p style={{ fontFamily: 'Space Grotesk, sans-serif', fontSize: 13, color: C.text, lineHeight: 1.6, margin: '0 0 12px' }}>
          {report.summary}
        </p>
      )}
      {(report.results || []).map((r, i) => (
        <div key={i} style={{
          display: 'flex',
          alignItems: 'flex-start',
          gap: 10,
          padding: '6px 0',
          borderTop: i > 0 ? `1px solid ${C.border}` : 'none',
        }}>
          <ReproChip status={r.status} />
          <div style={{ minWidth: 0 }}>
            <div style={{ fontFamily: 'JetBrains Mono, monospace', fontSize: 10, color: C.muted }}>{r.claim_id}</div>
            {r.notes && (
              <div style={{ fontFamily: 'Space Grotesk, sans-serif', fontSize: 12, color: C.text, marginTop: 3, lineHeight: 1.4 }}>
                {r.notes}
              </div>
            )}
          </div>
        </div>
      ))}
    </div>
  )
}

export default function PocSession() {
  const { sessionId } = useParams()
  const navigate = useNavigate()

  const [claimsData, setClaimsData]         = useState(null)
  const [selectedId, setSelectedId]         = useState(null)
  const [spec, setSpec]                     = useState(null)
  const [specLoading, setSpecLoading]       = useState(false)
  const [jobStatus, setJobStatus]           = useState('processing')
  const [zipReady, setZipReady]             = useState(false)
  const [uploading, setUploading]           = useState(false)
  const [analysisStatus, setAnalysisStatus] = useState(null)
  const [report, setReport]                 = useState(null)
  const [reproStatuses, setReproStatuses]   = useState({})
  const [checkedIds, setCheckedIds]         = useState(() => new Set())
  const [scaffoldStatus, setScaffoldStatus] = useState('awaiting_selection')
  const [scaffoldError, setScaffoldError]   = useState(null)
  const [paperTitle, setPaperTitle]         = useState('')
  const [codeTab, setCodeTab]               = useState('')
  const [sessionError, setSessionError]     = useState(null)

  const fileInputRef = useRef(null)

  // Load + poll claims and paper title
  useEffect(() => {
    const load = async () => {
      try {
        const data = await api.poc.claims(sessionId)
        setSessionError(null)
        setClaimsData(data)
        if (data && data.paper_title) setPaperTitle(data.paper_title)
      } catch (err) {
        const msg = err?.message || ''
        if (msg.includes('404') || msg.toLowerCase().includes('not found')) {
          setSessionError('Session not found — the server may have restarted. Submit the paper again.')
        }
      }
    }
    load()
    const t = setInterval(load, 3000)
    return () => clearInterval(t)
  }, [sessionId])

  // SSE stream — used for real-time claim refresh and phase completion signals
  useEffect(() => {
    const es = api.poc.stream(sessionId)
    const refresh = () =>
      api.poc.claims(sessionId).then(setClaimsData).catch(() => {})

    es.addEventListener('atom_created', () => refresh())
    es.addEventListener('check_complete', () => refresh())
    es.addEventListener('report_ready', () => {
      setZipReady(true)
      setScaffoldStatus('ready')
      setJobStatus('complete')
    })
    es.onerror = () => setJobStatus(s => s === 'processing' ? 'ready' : s)

    return () => es.close()
  }, [sessionId])

  // Load spec when testable claim selected; auto-select first scaffold file
  useEffect(() => {
    if (!selectedId) { setSpec(null); setCodeTab(''); return }
    const claim = claimsData?.claims?.find(c => c.claim_id === selectedId)
    if (claim?.testability !== 'testable') { setSpec(null); setCodeTab(''); return }
    setSpecLoading(true)
    api.poc.spec(sessionId, selectedId)
      .then(s => {
        setSpec(s)
        const files = s.scaffold_files ? Object.keys(s.scaffold_files) : []
        setCodeTab(files[0] || '')
        setSpecLoading(false)
      })
      .catch(() => { setSpec(null); setCodeTab(''); setSpecLoading(false) })
  }, [selectedId, sessionId, claimsData])

  // Poll for analysis report once results uploaded
  useEffect(() => {
    if (analysisStatus !== 'analyzing') return
    const t = setInterval(async () => {
      try {
        const data = await api.poc.report(sessionId)
        if (!Array.isArray(data.results)) return
        setReport(data)
        setAnalysisStatus('complete')
        const statuses = {}
        for (const r of data.results) statuses[r.claim_id] = r.status
        setReproStatuses(statuses)
        clearInterval(t)
      } catch {}
    }, 2000)
    return () => clearInterval(t)
  }, [analysisStatus, sessionId])

  // Poll scaffold status
  useEffect(() => {
    let cancelled = false
    const tick = async () => {
      try {
        const s = await api.poc.scaffoldStatus(sessionId)
        if (cancelled) return
        const next = s.scaffold_status || 'phase_1'
        setScaffoldStatus(next)
        setScaffoldError(s.scaffold_error || s.job_error || null)
        setZipReady(!!s.zip_ready)
        if (s.job_status === 'error') { setJobStatus('error'); return }
        if (next === 'awaiting_selection' || next === 'generating' || next === 'ready') {
          setJobStatus(j => j === 'processing' ? 'ready' : j)
        }
        if (next === 'ready' || next === 'error') return
      } catch {}
      if (!cancelled) setTimeout(tick, 2000)
    }
    tick()
    return () => { cancelled = true }
  }, [sessionId])

  const toggleChecked = (claimId, on) => {
    setCheckedIds(prev => {
      const next = new Set(prev)
      if (on) next.add(claimId); else next.delete(claimId)
      return next
    })
  }

  const handleGenerateScaffolds = async () => {
    const ids = Array.from(checkedIds)
    if (ids.length === 0) return
    setScaffoldStatus('generating')
    setScaffoldError(null)
    setZipReady(false)
    try {
      await api.poc.generateScaffolds(sessionId, ids)
    } catch (err) {
      console.error('Scaffold generation failed', err)
      setScaffoldStatus('error')
      setScaffoldError(String(err))
    }
  }

  const handleUpload = async (e) => {
    const file = e.target.files?.[0]
    if (!file) return
    setUploading(true)
    try {
      await api.poc.uploadResults(sessionId, file)
      setAnalysisStatus('analyzing')
    } catch (err) {
      console.error('Upload failed', err)
    }
    setUploading(false)
    e.target.value = ''
  }

  const selectedClaim = claimsData?.claims?.find(c => c.claim_id === selectedId)
  const scaffoldFiles = spec?.scaffold_files ?? {}
  const hasScaffoldFiles = Object.keys(scaffoldFiles).length > 0

  const statusChipStyle = (() => {
    if (jobStatus === 'complete')
      return { bg: '#14532D', border: '#22C55E', color: '#22C55E', label: '✓ COMPLETE' }
    if (jobStatus === 'error')
      return { bg: '#450A0A', border: '#EF4444', color: '#EF4444', label: '✗ ERROR' }
    return { bg: 'rgba(91,91,214,0.15)', border: C.indigo, color: C.indigo, label: '⟳ PROCESSING' }
  })()

  return (
    <div style={{ background: C.bg, minHeight: '100vh', display: 'flex', flexDirection: 'column', ...grotesk(), color: C.text, overflow: 'hidden' }}>
      {/* Header */}
      <div style={{ background: C.surface, borderBottom: `1px solid ${C.border}`, padding: '8px 16px', display: 'flex', alignItems: 'center', gap: 12, flexShrink: 0, height: 48 }}>
        <button onClick={() => navigate('/')} style={{ ...mono(11), background: 'none', border: `1px solid ${C.border}`, color: C.muted, cursor: 'pointer', padding: '3px 8px', borderRadius: 3 }}>← HOME</button>
        <div style={{ width: 1, height: 16, background: C.border }} />
        {paperTitle && (
          <span style={{ ...grotesk(15, 700), color: C.cyan, marginLeft: 6, maxWidth: 420, whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }} title={paperTitle}>
            {paperTitle}
          </span>
        )}
        <div style={{ flex: 1 }} />
        {claimsData && (<span style={{ ...mono(10), color: C.muted }}>{claimsData.testable} testable · {claimsData.theoretical} theoretical</span>)}
        <div style={{ ...mono(10, 700), padding: '3px 8px', borderRadius: 3, background: statusChipStyle.bg, border: `1px solid ${statusChipStyle.border}`, color: statusChipStyle.color }}>{statusChipStyle.label}</div>
      </div>

      {/* Body: claims | detail | scaffold viewer */}
      <div style={{ flex: 1, display: 'flex', overflow: 'hidden', minHeight: 0 }}>

        {/* Claims list */}
        <div style={{ width: 260, flexShrink: 0, background: C.sunken, borderRight: `1px solid ${C.border}`, display: 'flex', flexDirection: 'column', overflow: 'hidden' }}>
          <div style={{ padding: '7px 12px', borderBottom: `1px solid ${C.border}`, ...mono(9, 700), color: C.muted, letterSpacing: '0.1em', textTransform: 'uppercase', flexShrink: 0, display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
            <span>CLAIMS {claimsData ? `(${claimsData.total})` : ''}</span>
            {claimsData && claimsData.claims?.length > 0 && (
              <button
                onClick={() => {
                  const testableIds = claimsData.claims.filter(c => c.testability === 'testable').map(c => c.claim_id)
                  const allSelected = testableIds.every(id => checkedIds.has(id))
                  setCheckedIds(prev => {
                    if (allSelected) return new Set([...prev].filter(id => !testableIds.includes(id)))
                    return new Set([...prev, ...testableIds])
                  })
                }}
                style={{ ...mono(9, 700), color: C.cyan, background: 'none', border: 'none', cursor: 'pointer', padding: '2px 6px', borderRadius: 3, marginLeft: 4 }}
                title="Select all testable claims"
              >
                {(() => {
                  const testableIds = claimsData.claims.filter(c => c.testability === 'testable').map(c => c.claim_id)
                  return testableIds.every(id => checkedIds.has(id)) ? 'Unselect All' : 'Select All'
                })()}
              </button>
            )}
          </div>
          <div style={{ flex: 1, overflowY: 'auto' }}>
            {sessionError ? (
              <div style={{ padding: 16, ...mono(11), color: '#EF4444', lineHeight: 1.5 }}>{sessionError}</div>
            ) : !claimsData ? (
              <div style={{ padding: 16, ...mono(11), color: C.muted }}>Loading…</div>
            ) : !(claimsData.claims?.length) ? (
              <div style={{ padding: 16, ...mono(11), color: C.muted }}>{jobStatus === 'processing' ? '⟳ Extracting claims…' : 'No claims found.'}</div>
            ) : (
              claimsData.claims.map(claim => (
                <ClaimRow
                  key={claim.claim_id}
                  claim={claim}
                  selected={selectedId === claim.claim_id}
                  reproStatus={reproStatuses[claim.claim_id]}
                  onClick={() => setSelectedId(selectedId === claim.claim_id ? null : claim.claim_id)}
                  checkable={claim.testability === 'testable' && scaffoldStatus !== 'generating'}
                  checked={checkedIds.has(claim.claim_id)}
                  onCheckChange={(on) => toggleChecked(claim.claim_id, on)}
                />
              ))
            )}
          </div>
        </div>

        {/* Claim detail */}
        <div style={{ width: 340, flexShrink: 0, background: C.surface, borderRight: `1px solid ${C.border}`, overflowY: 'auto', padding: 22, minWidth: 0 }}>
          {!selectedClaim ? (
            <div style={{ height: '100%', display: 'flex', alignItems: 'center', justifyContent: 'center', flexDirection: 'column', gap: 8 }}>
              <span style={{ ...mono(12), color: C.muted }}>Select a claim</span>
              {jobStatus === 'processing' && (<span style={{ ...mono(11), color: C.indigo }}>⟳ Pipeline running…</span>)}
            </div>
          ) : (
            <>
              <div style={{ marginBottom: 18 }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: 7, flexWrap: 'wrap', marginBottom: 8 }}>
                  <TestabilityChip testability={selectedClaim.testability} />
                  {selectedClaim.claim_type && (<Chip>{selectedClaim.claim_type}</Chip>)}
                  <ReproChip status={reproStatuses[selectedClaim.claim_id]} />
                </div>
                <div style={{ ...mono(10), color: C.muted, marginBottom: 8 }}>{selectedClaim.claim_id}</div>
                <p style={{ ...grotesk(14), color: C.text, lineHeight: 1.65, margin: 0 }}>{selectedClaim.text}</p>
              </div>

              {selectedClaim.testability === 'theoretical' && (
                <div style={{ padding: '10px 12px', background: 'rgba(107,114,128,0.07)', border: `1px solid ${C.border}`, borderRadius: 4, ...grotesk(12), color: C.muted, lineHeight: 1.5 }}>
                  This claim is theoretical — no executable scaffold can be generated.
                  {selectedClaim.spec_summary?.reason && (<div style={{ ...mono(10), marginTop: 6 }}>reason: {selectedClaim.spec_summary.reason}</div>)}
                </div>
              )}

              {selectedClaim.testability === 'testable' && (
                specLoading ? (
                  <div style={{ ...mono(11), color: C.muted }}>⟳ Loading spec…</div>
                ) : !spec ? (
                  <div style={{ ...mono(11), color: C.muted }}>{jobStatus === 'processing' ? '⟳ Spec generating…' : 'No spec available.'}</div>
                ) : (
                  <>
                    {spec.success_criteria?.length > 0 && (
                      <section style={{ marginBottom: 18 }}>
                        <SectionLabel>Success Criteria</SectionLabel>
                        {spec.success_criteria.map((c, i) => (<SuccessCriterion key={i} c={c} />))}
                      </section>
                    )}
                    {spec.environment && Object.keys(spec.environment).length > 0 && (
                      <section style={{ marginBottom: 18 }}>
                        <SectionLabel>Environment</SectionLabel>
                        <div style={{ background: C.sunken, border: `1px solid ${C.border}`, borderRadius: 4, padding: '8px 10px' }}>
                          {Object.entries(spec.environment).map(([k, v]) => (
                            <div key={k} style={{ display: 'flex', gap: 12, marginBottom: 4 }}>
                              <span style={{ ...mono(11), color: C.muted, minWidth: 100 }}>{k}</span>
                              <span style={{ ...mono(11), color: C.text }}>{String(v)}</span>
                            </div>
                          ))}
                        </div>
                      </section>
                    )}
                    {report && (
                      <ReportPanel report={{ summary: report.summary, results: (report.results || []).filter(r => r.claim_id === selectedClaim.claim_id) }} />
                    )}
                  </>
                )
              )}
            </>
          )}
        </div>

        {/* Scaffold code viewer */}
        <div style={{ flex: 1, minWidth: 0, background: C.sunken, display: 'flex', flexDirection: 'column', overflow: 'hidden' }}>
          {/* Panel header */}
          <div style={{ padding: '7px 12px', borderBottom: `1px solid ${C.border}`, ...mono(9, 700), color: C.muted, letterSpacing: '0.1em', textTransform: 'uppercase', flexShrink: 0, display: 'flex', alignItems: 'center', gap: 8 }}>
            <span>SCAFFOLD</span>
            {selectedClaim && hasScaffoldFiles && (
              <span style={{ ...mono(9), color: C.indigo, fontWeight: 400, textTransform: 'none', letterSpacing: 0 }}>{selectedClaim.claim_id}</span>
            )}
          </div>

          {/* Panel body */}
          {!selectedClaim ? (
            <div style={{ flex: 1, display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
              <span style={{ ...mono(11), color: C.muted }}>Select a testable claim to view its scaffold</span>
            </div>
          ) : selectedClaim.testability !== 'testable' ? (
            <div style={{ flex: 1, display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
              <span style={{ ...mono(11), color: C.muted }}>Theoretical claim — no scaffold</span>
            </div>
          ) : specLoading ? (
            <div style={{ flex: 1, display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
              <span style={{ ...mono(11), color: C.muted }}>⟳ Loading…</span>
            </div>
          ) : !hasScaffoldFiles ? (
            <div style={{ flex: 1, display: 'flex', alignItems: 'center', justifyContent: 'center', flexDirection: 'column', gap: 8 }}>
              {scaffoldStatus === 'generating' ? (
                <span style={{ ...mono(11), color: C.indigo }}>⟳ Generating scaffold…</span>
              ) : scaffoldStatus === 'ready' ? (
                <span style={{ ...mono(11), color: '#EF4444' }}>Scaffold generation failed for this claim. Select it and click GENERATE SCAFFOLDS to retry.</span>
              ) : (
                <span style={{ ...mono(11), color: C.muted }}>Check this claim and click GENERATE SCAFFOLDS</span>
              )}
            </div>
          ) : (
            <div style={{ flex: 1, display: 'flex', overflow: 'hidden', minHeight: 0 }}>
              {/* File list */}
              <div style={{ width: 156, flexShrink: 0, borderRight: `1px solid ${C.border}`, overflowY: 'auto', background: 'rgba(0,0,0,0.18)' }}>
                {Object.keys(scaffoldFiles).map(name => (
                  <ScaffoldFileRow
                    key={name}
                    name={name}
                    selected={codeTab === name}
                    onClick={() => setCodeTab(name)}
                  />
                ))}
              </div>
              {/* Code pane */}
              <div style={{ flex: 1, overflow: 'auto', background: C.bg }}>
                {codeTab && scaffoldFiles[codeTab] ? (
                  <div style={{ minWidth: 'max-content' }}>
                    {scaffoldFiles[codeTab].split('\n').map((line, i) => (
                      <div
                        key={i}
                        style={{ display: 'flex', alignItems: 'stretch', minHeight: '1.6em' }}
                      >
                        <span style={{
                          ...mono(10),
                          color: C.muted,
                          minWidth: 44,
                          paddingRight: 14,
                          paddingLeft: 12,
                          textAlign: 'right',
                          userSelect: 'none',
                          borderRight: `1px solid ${C.border}`,
                          flexShrink: 0,
                          lineHeight: '1.6em',
                          background: 'rgba(0,0,0,0.25)',
                        }}>{i + 1}</span>
                        <span style={{
                          ...mono(11),
                          color: C.text,
                          paddingLeft: 14,
                          paddingRight: 20,
                          whiteSpace: 'pre',
                          lineHeight: '1.6em',
                        }}>{line}</span>
                      </div>
                    ))}
                  </div>
                ) : (
                  <div style={{ height: '100%', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                    <span style={{ ...mono(11), color: C.muted }}>Select a file</span>
                  </div>
                )}
              </div>
            </div>
          )}
        </div>
      </div>

      {/* Bottom action bar */}
      <div style={{ background: C.surface, borderTop: `1px solid ${C.border}`, padding: '11px 18px', display: 'flex', alignItems: 'center', gap: 12, flexShrink: 0 }}>
        {(() => {
          const canGenerate = checkedIds.size > 0 && scaffoldStatus !== 'generating' && scaffoldStatus !== 'phase_1'
          const generating = scaffoldStatus === 'generating'
          return (
            <button
              onClick={handleGenerateScaffolds}
              disabled={!canGenerate}
              style={{
                ...mono(11, 700),
                letterSpacing: '0.05em',
                padding: '5px 14px',
                borderRadius: 3,
                border: `1px solid ${canGenerate ? C.purple : C.border}`,
                background: canGenerate ? 'rgba(179,136,255,0.10)' : 'rgba(255,255,255,0.03)',
                color: canGenerate ? C.purple : C.muted,
                cursor: canGenerate ? 'pointer' : 'not-allowed',
              }}
            >
              {generating ? '⟳ GENERATING…' : `⚡ GENERATE SCAFFOLDS (${checkedIds.size})`}
            </button>
          )
        })()}
        <div style={{ width: 1, height: 16, background: C.border }} />
        <button
          onClick={() => window.open(`/api/poc/${sessionId}/scaffold.zip`, '_blank')}
          disabled={!zipReady}
          style={{ ...mono(11, 700), letterSpacing: '0.05em', padding: '5px 14px', borderRadius: 3, border: `1px solid ${zipReady ? C.indigo : C.border}`, background: zipReady ? 'rgba(91,91,214,0.15)' : 'rgba(255,255,255,0.03)', color: zipReady ? C.indigo : C.muted, cursor: zipReady ? 'pointer' : 'not-allowed' }}
        >↓ SCAFFOLD.ZIP</button>
        <div style={{ width: 1, height: 16, background: C.border }} />
        <input ref={fileInputRef} type="file" accept=".json" onChange={handleUpload} style={{ display: 'none' }} />
        <button
          onClick={() => fileInputRef.current?.click()}
          disabled={!zipReady || uploading}
          style={{ ...mono(11, 700), letterSpacing: '0.05em', padding: '5px 14px', borderRadius: 3, border: `1px solid ${zipReady && !uploading ? C.cyan : C.border}`, background: zipReady && !uploading ? 'rgba(0,234,255,0.08)' : 'rgba(255,255,255,0.03)', color: zipReady && !uploading ? C.cyan : C.muted, cursor: zipReady && !uploading ? 'pointer' : 'not-allowed' }}
        >{uploading ? '⟳ UPLOADING…' : '↑ UPLOAD RESULTS.JSON'}</button>
        {analysisStatus === 'analyzing' && (<span style={{ ...mono(11), color: C.indigo }}>⟳ Analyzing results…</span>)}
        {analysisStatus === 'complete' && report && (<span style={{ ...mono(11), color: '#22C55E' }}>✓ Analysis complete — {report.results?.length ?? 0} results</span>)}
        {scaffoldError && (<span style={{ ...mono(11), color: '#EF4444' }}>scaffold error: {scaffoldError}</span>)}
        <div style={{ flex: 1 }} />
        <span style={{ ...mono(10), color: C.muted }}>{
          scaffoldStatus === 'phase_1' || jobStatus === 'processing' ? 'Extracting atoms + metrics…'
            : scaffoldStatus === 'awaiting_selection' ? 'Pick claims → click GENERATE SCAFFOLDS'
            : scaffoldStatus === 'generating' ? 'Generating scaffolds…'
            : !zipReady ? 'Scaffolds queued…'
            : analysisStatus !== 'complete' ? 'Download scaffold → run pytest → upload poc_results.json'
            : 'Reproducibility analysis complete'
        }</span>
      </div>
    </div>
  );
}
