

import { useState, useEffect, useRef } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { api } from '../api/client';
import Chip from '../components/Chip';
import SectionLabel from '../components/SectionLabel';
import TestabilityChip from '../components/TestabilityChip';
import ReproChip from '../components/ReproChip';
import FeedRow from '../components/FeedRow';
import { Prism as SyntaxHighlighter } from 'react-syntax-highlighter';
import { vscDarkPlus } from 'react-syntax-highlighter/dist/esm/styles/prism';


const C = {
  bg:      '#0A0C10',
  surface: 'rgba(19, 23, 32, 0.65)',
  sunken:  'rgba(13, 16, 23, 0.45)',
  border:  'rgba(255,255,255,0.08)',
  text:    '#F3F4F6',
  muted:   '#9CA3AF',
  indigo:  '#6366F1',
  cyan:    '#22D3EE',
  purple:  '#A855F7',
};

function mono(size = 11, weight = 400) {
  return { fontFamily: 'JetBrains Mono, monospace', fontSize: size, fontWeight: weight };
}
function grotesk(size = 13, weight = 400) {
  return { fontFamily: 'Space Grotesk, sans-serif', fontSize: size, fontWeight: weight };
}


// --- Local: ClaimRow, SuccessCriterion, ScaffoldFileChip, ReportPanel ---
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
            <span style={{ ...mono(8, 700), color: '#22C55E', background: 'rgba(34,197,94,0.10)', border: '1px solid rgba(34,197,94,0.25)', padding: '1px 5px', borderRadius: 2, letterSpacing: '0.04em' }}>✓ SCAFFOLD</span>
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

function ExtractingClaimsLoader() {
  return (
    <div className="animate-pulse" style={{ padding: '16px 12px', display: 'flex', flexDirection: 'column', gap: 16 }}>
      <div style={{ ...mono(11, 600), color: C.cyan, display: 'flex', alignItems: 'center', gap: 8 }}>
        <div className="animate-spin" style={{ display: 'flex', alignItems: 'center', justifyContent: 'center' }}>⟳</div>
        EXTRACTING CLAIMS...
      </div>
      {[1, 2, 3, 4, 5].map(i => (
        <div key={i} style={{ padding: '8px 12px', borderLeft: `2px solid rgba(255,255,255,0.05)`, display: 'flex', flexDirection: 'column', gap: 8 }}>
          <div style={{ display: 'flex', gap: 6 }}>
            <div style={{ width: 60, height: 16, borderRadius: 8, background: 'rgba(255,255,255,0.05)' }} />
            <div style={{ width: 40, height: 16, borderRadius: 8, background: 'rgba(255,255,255,0.05)' }} />
          </div>
          <div style={{ width: 50, height: 10, background: 'rgba(255,255,255,0.03)', borderRadius: 2 }} />
          <div style={{ width: '90%', height: 12, background: 'rgba(255,255,255,0.05)', borderRadius: 2 }} />
          <div style={{ width: '60%', height: 12, background: 'rgba(255,255,255,0.05)', borderRadius: 2 }} />
        </div>
      ))}
    </div>
  )
}

function GeneratingScaffoldLoader() {
  return (
    <div className="animate-pulse" style={{ display: 'flex', flexDirection: 'column', gap: 12, marginTop: 20 }}>
      <div style={{ ...mono(11, 600), color: C.purple, display: 'flex', alignItems: 'center', gap: 8 }}>
        <div className="animate-spin" style={{ display: 'flex', alignItems: 'center', justifyContent: 'center' }}>⟳</div>
        GENERATING SCAFFOLD FILES...
      </div>
      <div style={{ padding: 16, border: `1px dashed rgba(168, 85, 247, 0.3)`, borderRadius: 6, background: 'rgba(168, 85, 247, 0.05)' }}>
        <div style={{ height: 14, background: 'rgba(255,255,255,0.1)', borderRadius: 3, width: '30%', marginBottom: 12 }}></div>
        <div style={{ height: 10, background: 'rgba(255,255,255,0.05)', borderRadius: 3, width: '80%', marginBottom: 8 }}></div>
        <div style={{ height: 10, background: 'rgba(255,255,255,0.05)', borderRadius: 3, width: '60%', marginBottom: 8 }}></div>
        <div style={{ height: 10, background: 'rgba(255,255,255,0.05)', borderRadius: 3, width: '70%' }}></div>
      </div>
    </div>
  )
}

function GeneratingScaffoldOverlay({ count }) {
  return (
    <div
      style={{
        position: 'absolute',
        top: 16,
        right: 16,
        zIndex: 50,
        pointerEvents: 'none',
      }}
    >
      <div
        style={{
          width: 320,
          padding: '14px 16px',
          borderRadius: 8,
          border: `1px solid rgba(168, 85, 247, 0.35)`,
          background: 'linear-gradient(180deg, rgba(30, 27, 75, 0.92) 0%, rgba(19, 23, 32, 0.94) 100%)',
          backdropFilter: 'blur(10px)',
          WebkitBackdropFilter: 'blur(10px)',
          boxShadow: '0 16px 40px rgba(0,0,0,0.45), 0 0 0 1px rgba(168,85,247,0.12)',
          display: 'flex',
          flexDirection: 'column',
          gap: 10,
          pointerEvents: 'auto',
        }}
      >
        <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
          <div
            className="animate-spin"
            style={{
              width: 18,
              height: 18,
              borderRadius: '50%',
              border: `2px solid rgba(168, 85, 247, 0.25)`,
              borderTopColor: C.purple,
            }}
          />
          <span style={{ ...mono(12, 700), color: C.purple, letterSpacing: '0.08em' }}>
            GENERATING SCAFFOLDS
          </span>
        </div>
        <div style={{ ...grotesk(13), color: C.text, lineHeight: 1.5 }}>
          {count > 0
            ? <>Building test harnesses for <strong style={{ color: C.purple }}>{count}</strong> claim{count === 1 ? '' : 's'}.</>
            : <>Building test harnesses for the selected claims.</>}
        </div>
        <div style={{ ...mono(10), color: C.muted, lineHeight: 1.5 }}>
          Drafting <code style={{ color: C.cyan }}>implementation.py</code> + <code style={{ color: C.cyan }}>test_harness.py</code> per claim. Usually 30–90s.
        </div>
        <div
          style={{
            position: 'relative',
            height: 4,
            borderRadius: 2,
            background: 'rgba(255,255,255,0.06)',
            overflow: 'hidden',
          }}
        >
          <div
            style={{
              position: 'absolute',
              top: 0,
              bottom: 0,
              width: '40%',
              borderRadius: 2,
              background: `linear-gradient(90deg, transparent, ${C.purple}, transparent)`,
              animation: 'poc-progress-slide 1.6s ease-in-out infinite',
            }}
          />
        </div>
        <style>{`
          @keyframes poc-progress-slide {
            0%   { transform: translateX(-100%); }
            100% { transform: translateX(350%); }
          }
        `}</style>
      </div>
    </div>
  )
}

export default function PocSession() {
  const { sessionId } = useParams()
  const navigate = useNavigate()

  const [claimsData, setClaimsData]     = useState(null)
  const [selectedId, setSelectedId]     = useState(null)
  const [selectedFile, setSelectedFile] = useState('README.md')
  const [spec, setSpec]                 = useState(null)
  const [specLoading, setSpecLoading]   = useState(false)
  const [feed, setFeed]                 = useState([])
  const [jobStatus, setJobStatus]       = useState('processing')
  const [zipReady, setZipReady]         = useState(false)
  const [uploading, setUploading]       = useState(false)
  const [analysisStatus, setAnalysisStatus] = useState(null)
  const [report, setReport]             = useState(null)
  const [reproStatuses, setReproStatuses] = useState({})
  const [checkedIds, setCheckedIds]     = useState(() => new Set())
  const [scaffoldStatus, setScaffoldStatus] = useState('awaiting_selection')
  const [scaffoldError, setScaffoldError]   = useState(null)
  const [sessions, setSessions]             = useState([])
  const [paperTitle, setPaperTitle]         = useState('')
  const [sessionError, setSessionError]     = useState(null)

  const feedRef     = useRef(null)
  const fileInputRef = useRef(null)
  const prevSelectedId = useRef(null)

  // Load + poll claims
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

  // Load available sessions
  useEffect(() => {
    api.poc.sessions().then(res => setSessions(res.sessions || [])).catch(() => {})
  }, [sessionId])

  // SSE stream
  useEffect(() => {
    const es = api.poc.stream(sessionId)

    const refresh = () =>
      api.poc.claims(sessionId).then(setClaimsData).catch(() => {})

    es.addEventListener('atom_created', (e) => {
      const payload = JSON.parse(e.data)
      const shortId = payload.claim_id ? payload.claim_id.split('-')[0] : 'unknown'
      setFeed(f => [...f, { 
        level: 'info', 
        message: `Extracted ${payload.testability} claim: ${shortId}` 
      }])
      refresh()
    })
    es.addEventListener('check_complete', (e) => {
      const payload = JSON.parse(e.data)
      const shortId = payload.claim_id ? payload.claim_id.split('-')[0] : 'unknown'
      setFeed(f => [...f, { 
        level: payload.status === 'error' ? 'error' : 'success', 
        message: `Scaffold ${payload.status || 'generated'}: ${shortId}` 
      }])
      refresh()
    })
    es.addEventListener('report_ready', (e) => {
      setFeed(f => [...f, { 
        level: 'success', 
        message: `Reproducibility report generated.` 
      }])
      setZipReady(true)
      setScaffoldStatus('ready')
      setJobStatus('complete')
    })
    es.onerror = () => setJobStatus(s => s === 'processing' ? 'ready' : s)

    return () => es.close()
  }, [sessionId])

  // Auto-scroll feed
  useEffect(() => {
    if (feedRef.current) feedRef.current.scrollTop = feedRef.current.scrollHeight
  }, [feed])

  // Load spec when testable claim selected
  useEffect(() => {
    if (!selectedId) { 
      setSpec(null); 
      prevSelectedId.current = null;
      return; 
    }
    const claim = claimsData?.claims?.find(c => c.claim_id === selectedId)
    if (claim && claim.testability !== 'testable') { 
      setSpec(null); 
      return; 
    }
    
    if (selectedId !== prevSelectedId.current) {
      prevSelectedId.current = selectedId
      setSpecLoading(true)
      api.poc.spec(sessionId, selectedId)
        .then(s => {
          setSpec(s)
          setSpecLoading(false)
          const files = s?.scaffold_files ? Object.keys(s.scaffold_files) : []
          setSelectedFile(files.includes('README.md') ? 'README.md' : (files[0] || 'README.md'))
        })
        .catch(() => { setSpec(null); setSpecLoading(false) })
    }
  }, [selectedId, sessionId, claimsData])

  // Poll for analysis report once results uploaded
  useEffect(() => {
    if (analysisStatus !== 'analyzing') return
    const t = setInterval(async () => {
      try {
        const data = await api.poc.report(sessionId)
        setReport(data)
        setAnalysisStatus('complete')
        const statuses = {}
        for (const r of data.results || []) statuses[r.claim_id] = r.status
        setReproStatuses(statuses)
        clearInterval(t)
      } catch {}
    }, 2000)
    return () => clearInterval(t)
  }, [analysisStatus, sessionId])

  // Poll scaffold status so the download button activates as soon as Phase 2 finishes
  useEffect(() => {
    let cancelled = false
    const tick = async () => {
      try {
        const s = await api.poc.scaffoldStatus(sessionId)
        if (cancelled) return
        const next = s.scaffold_status || 'phase_1'
        setScaffoldStatus(next)
        setScaffoldError(s.scaffold_error || null)
        setZipReady(!!s.zip_ready)
        // Phase 1 done → flip the header chip out of "processing" so the
        // generate button is reachable.
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

  // ── Status chip helper ──────────────────────────────────────────────────────
  const statusChipStyle = (() => {
    if (jobStatus === 'complete')
      return { bg: '#14532D', border: '#22C55E', color: '#22C55E', label: '✓ COMPLETE' }
    if (jobStatus === 'error')
      return { bg: '#450A0A', border: '#EF4444', color: '#EF4444', label: '✗ ERROR' }
    return { bg: 'rgba(91,91,214,0.15)', border: C.indigo, color: C.indigo, label: '⟳ PROCESSING' }
  })()

  return (
    <div style={{ background: 'radial-gradient(circle at top left, #1e1b4b 0%, #0A0C10 50%)', minHeight: '100vh', display: 'flex', flexDirection: 'column', ...grotesk(), color: C.text, overflow: 'hidden' }}>
      {/* Header */}
      <div style={{ background: C.surface, backdropFilter: 'blur(12px)', borderBottom: `1px solid ${C.border}`, padding: '8px 16px', display: 'flex', alignItems: 'center', gap: 12, flexShrink: 0, height: 44, zIndex: 10 }}>
        <button onClick={() => navigate('/')} style={{ ...mono(11), background: 'none', border: `1px solid ${C.border}`, color: C.muted, cursor: 'pointer', padding: '3px 8px', borderRadius: 3 }}>← HOME</button>
        <div style={{ width: 1, height: 16, background: C.border }} />
        <span style={{ ...mono(11), color: C.muted }}>POC /</span>
        <select 
          value={sessionId} 
          onChange={(e) => navigate(`/poc/${e.target.value}`)}
          style={{ ...mono(11, 600), color: C.cyan, background: 'rgba(0,234,255,0.08)', border: `1px solid rgba(0,234,255,0.2)`, borderRadius: 4, padding: '2px 6px', cursor: 'pointer', outline: 'none' }}
        >
          {sessions.length === 0 ? (
            <option value={sessionId}>{sessionId.split('-')[0]}</option>
          ) : (
            sessions.map(s => {
              let label = s.title || (s.arxiv_id !== 'unknown' ? s.arxiv_id : s.session_id.split('-')[0]);
              if (label.length > 50) label = label.substring(0, 47) + '...';
              if (s.status === 'error') label += ' (error)';
              return (
                <option key={s.session_id} value={s.session_id} style={{ background: '#131720', color: C.text }}>
                  {label}
                </option>
              );
            })
          )}
        </select>
        {paperTitle && (
          <span
            title={paperTitle}
            style={{ ...grotesk(14, 700), color: C.text, marginLeft: 6, maxWidth: 480, whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}
          >
            {paperTitle}
          </span>
        )}
        <div style={{ flex: 1 }} />
        {claimsData && (<span style={{ ...mono(10), color: C.muted }}>{claimsData.testable} testable · {claimsData.theoretical} theoretical</span>)}
        <div style={{ ...mono(10, 700), padding: '3px 8px', borderRadius: 3, background: statusChipStyle.bg, border: `1px solid ${statusChipStyle.border}`, color: statusChipStyle.color }}>{statusChipStyle.label}</div>
      </div>
      {/* Body: three columns */}
      <div style={{ flex: 1, display: 'flex', overflow: 'hidden', minHeight: 0, position: 'relative' }}>
        {scaffoldStatus === 'generating' && (
          <GeneratingScaffoldOverlay count={checkedIds.size} />
        )}
        {/* Claims list */}
        <div style={{ width: 280, flexShrink: 0, background: C.sunken, backdropFilter: 'blur(12px)', borderRight: `1px solid ${C.border}`, display: 'flex', flexDirection: 'column', overflow: 'hidden', zIndex: 5 }}>
          <div style={{ padding: '7px 12px', borderBottom: `1px solid ${C.border}`, ...mono(9, 700), color: C.muted, letterSpacing: '0.1em', textTransform: 'uppercase', flexShrink: 0, display: 'flex', alignItems: 'center', justifyContent: 'space-between', gap: 8 }}>
            <span>CLAIMS {claimsData ? `(${claimsData.total})` : ''}</span>
            {claimsData && claimsData.claims?.length > 0 && (() => {
              const testableIds = claimsData.claims.filter(c => c.testability === 'testable').map(c => c.claim_id)
              if (testableIds.length === 0) return null
              const allSelected = testableIds.every(id => checkedIds.has(id))
              const disabled = scaffoldStatus === 'generating'
              return (
                <button
                  onClick={() => {
                    if (disabled) return
                    setCheckedIds(prev => {
                      if (allSelected) {
                        const next = new Set(prev)
                        for (const id of testableIds) next.delete(id)
                        return next
                      }
                      const next = new Set(prev)
                      for (const id of testableIds) next.add(id)
                      return next
                    })
                  }}
                  disabled={disabled}
                  style={{ ...mono(9, 700), color: disabled ? C.muted : C.cyan, background: 'none', border: 'none', cursor: disabled ? 'not-allowed' : 'pointer', padding: '2px 6px', borderRadius: 3, textTransform: 'none', letterSpacing: 0 }}
                  title={allSelected ? 'Unselect all testable claims' : 'Select all testable claims'}
                >
                  {allSelected ? 'Unselect All' : 'Select All'}
                </button>
              )
            })()}
          </div>
          <div style={{ flex: 1, overflowY: 'auto' }}>
            {sessionError ? (
              <div style={{ padding: 16, ...mono(11), color: '#EF4444', lineHeight: 1.5 }}>{sessionError}</div>
            ) : !claimsData ? (
              <ExtractingClaimsLoader />
            ) : claimsData.claims.length === 0 ? (
              jobStatus === 'processing' ? <ExtractingClaimsLoader /> : <div style={{ padding: 16, ...mono(11), color: C.muted }}>No claims found.</div>
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
        <div style={{ flex: 1, minWidth: 380, background: C.surface, backdropFilter: 'blur(12px)', borderRight: `1px solid ${C.border}`, overflowY: 'auto', padding: 20, transition: 'all 0.2s', zIndex: 5 }}>
          {!selectedClaim ? (<div style={{ height: '100%', display: 'flex', alignItems: 'center', justifyContent: 'center', flexDirection: 'column', gap: 8 }}><span style={{ ...mono(12), color: C.muted }}>Select a claim from the left panel</span>{jobStatus === 'processing' && (<span style={{ ...mono(11), color: C.indigo }}>⟳ Pipeline running…</span>)}</div>) : (<><div style={{ marginBottom: 16 }}><div style={{ display: 'flex', alignItems: 'center', gap: 7, flexWrap: 'wrap', marginBottom: 8 }}><TestabilityChip testability={selectedClaim.testability} />{selectedClaim.claim_type && (<Chip>{selectedClaim.claim_type}</Chip>)}<ReproChip status={reproStatuses[selectedClaim.claim_id]} /></div><div style={{ ...mono(10), color: C.muted, marginBottom: 8 }}>{selectedClaim.claim_id}</div><p style={{ ...grotesk(14), color: C.text, lineHeight: 1.65, margin: 0 }}>{selectedClaim.text}</p></div>{selectedClaim.testability === 'theoretical' && (<div style={{ padding: '10px 12px', background: 'rgba(107,114,128,0.07)', border: `1px solid ${C.border}`, borderRadius: 4, ...grotesk(12), color: C.muted, lineHeight: 1.5 }}>This claim is theoretical — no executable scaffold can be generated.{selectedClaim.spec_summary?.reason && (<div style={{ ...mono(10), marginTop: 6 }}>reason: {selectedClaim.spec_summary.reason}</div>)}</div>)}{selectedClaim.testability === 'testable' && (specLoading ? (<div style={{ ...mono(11), color: C.muted }}>⟳ Loading spec…</div>) : !spec ? (
  scaffoldStatus === 'generating' && checkedIds.has(selectedClaim.claim_id) ? (
    <GeneratingScaffoldLoader />
  ) : (
    <div style={{ ...mono(11), color: C.muted, marginTop: 10 }}>
      {jobStatus === 'processing' ? '⟳ Extracting claim details…' : 'No scaffold generated for this claim.'}
    </div>
  )
) : (<><section style={{ marginBottom: 20 }}>{spec.success_criteria?.length > 0 && (<><SectionLabel>Success Criteria</SectionLabel>{spec.success_criteria.map((c, i) => (<SuccessCriterion key={i} c={c} />))}</>)}{spec.environment && Object.keys(spec.environment).length > 0 && (<><SectionLabel>Environment</SectionLabel><div style={{ background: C.sunken, border: `1px solid ${C.border}`, borderRadius: 4, padding: '8px 10px' }}>{Object.entries(spec.environment).map(([k, v]) => (<div key={k} style={{ display: 'flex', gap: 12, marginBottom: 4 }}><span style={{ ...mono(11), color: C.muted, minWidth: 100 }}>{k}</span><span style={{ ...mono(11), color: C.text }}>{String(v)}</span></div>))}</div></>)}{spec.scaffold_files && Object.keys(spec.scaffold_files).length > 0 && (<><SectionLabel>Scaffold Files</SectionLabel><div style={{ display: 'flex', gap: 6, flexWrap: 'wrap', marginBottom: 10 }}>{Object.keys(spec.scaffold_files).map(name => (<button key={name} onClick={() => setSelectedFile(name)} style={{ fontFamily: 'JetBrains Mono, monospace', fontSize: 10, color: selectedFile === name ? C.cyan : C.muted, background: selectedFile === name ? 'rgba(0,234,255,0.08)' : 'transparent', border: `1px solid ${selectedFile === name ? 'rgba(0,234,255,0.20)' : C.border}`, padding: '2px 8px', borderRadius: 3, cursor: 'pointer', transition: 'all 0.15s' }}>{name}</button>))}</div>{spec.scaffold_files[selectedFile] && (<div style={{ background: C.sunken, border: `1px solid ${C.border}`, borderRadius: 4, overflow: 'hidden', boxShadow: 'inset 0 2px 4px rgba(0,0,0,0.1)' }}><SyntaxHighlighter language={selectedFile.endsWith('.py') ? 'python' : selectedFile.endsWith('.md') ? 'markdown' : 'text'} style={vscDarkPlus} customStyle={{ margin: 0, padding: '12px 14px', fontSize: 11, background: 'transparent', maxHeight: 400 }} wrapLongLines={false}>{spec.scaffold_files[selectedFile]}</SyntaxHighlighter></div>)}</>)}{report && (<ReportPanel report={{ summary: report.summary, results: (report.results || []).filter(r => r.claim_id === selectedClaim.claim_id) }} />)}</section></>))}</>)}
        </div>
        {/* Activity feed */}
        <div style={{ width: 280, flexShrink: 0, background: C.sunken, backdropFilter: 'blur(12px)', borderLeft: `1px solid ${C.border}`, display: 'flex', flexDirection: 'column', overflow: 'hidden', zIndex: 5 }}>
          <div style={{ padding: '7px 12px', borderBottom: `1px solid ${C.border}`, ...mono(9, 700), color: C.muted, letterSpacing: '0.1em', textTransform: 'uppercase', flexShrink: 0 }}>ACTIVITY FEED</div>
          <div ref={feedRef} style={{ flex: 1, overflowY: 'auto' }}>{feed.length === 0 ? (<div style={{ padding: 12, ...mono(10), color: C.muted }}>Waiting for events…</div>) : (feed.map((ev, i) => <FeedRow key={i} event={ev} />))}</div>
        </div>
      </div>
      {/* Bottom action bar */}
      <div style={{ background: C.surface, backdropFilter: 'blur(12px)', borderTop: `1px solid ${C.border}`, padding: '9px 16px', display: 'flex', alignItems: 'center', gap: 10, flexShrink: 0, zIndex: 10 }}>
        {(() => {
          const canGenerate =
            checkedIds.size > 0 &&
            scaffoldStatus !== 'generating' &&
            scaffoldStatus !== 'phase_1'
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
        <button onClick={() => window.open(`/api/poc/${sessionId}/scaffold.zip`, '_blank')} disabled={!zipReady} style={{ ...mono(11, 700), letterSpacing: '0.05em', padding: '5px 14px', borderRadius: 3, border: `1px solid ${zipReady ? C.indigo : C.border}`, background: zipReady ? 'rgba(91,91,214,0.15)' : 'rgba(255,255,255,0.03)', color: zipReady ? C.indigo : C.muted, cursor: zipReady ? 'pointer' : 'not-allowed' }}>↓ SCAFFOLD.ZIP</button>
        <div style={{ width: 1, height: 16, background: C.border }} />
        <input ref={fileInputRef} type="file" accept=".json" onChange={handleUpload} style={{ display: 'none' }} />
        <button onClick={() => fileInputRef.current?.click()} disabled={!zipReady || uploading} style={{ ...mono(11, 700), letterSpacing: '0.05em', padding: '5px 14px', borderRadius: 3, border: `1px solid ${zipReady && !uploading ? C.cyan : C.border}`, background: zipReady && !uploading ? 'rgba(0,234,255,0.08)' : 'rgba(255,255,255,0.03)', color: zipReady && !uploading ? C.cyan : C.muted, cursor: zipReady && !uploading ? 'pointer' : 'not-allowed' }}>{uploading ? '⟳ UPLOADING…' : '↑ UPLOAD RESULTS.JSON'}</button>
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
