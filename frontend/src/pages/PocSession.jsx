

import { useState, useEffect, useRef } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { api } from '../api/client';
import Chip from '../components/Chip';
import SectionLabel from '../components/SectionLabel';
import TestabilityChip from '../components/TestabilityChip';
import ReproChip from '../components/ReproChip';
import FeedRow from '../components/FeedRow';


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


// --- Local: ClaimRow, SuccessCriterion, ScaffoldFileChip, ReportPanel ---
function ClaimRow({ claim, selected, reproStatus, onClick }) {
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
      }}
    >
      <div style={{ display: 'flex', alignItems: 'center', gap: 5, flexWrap: 'wrap', marginBottom: 4 }}>
        <TestabilityChip testability={claim.testability} />
        <ReproChip status={reproStatus} />
      </div>
      <div style={{ ...mono(10), color: C.muted, marginBottom: 3 }}>{claim.claim_id}</div>
      <div style={{ ...grotesk(12), color: C.text, lineHeight: 1.45, overflow: 'hidden', display: '-webkit-box', WebkitLineClamp: 2, WebkitBoxOrient: 'vertical' }}>{claim.text}</div>
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

function ScaffoldFileChip({ name }) {
  return (
    <span style={{
      fontFamily: 'JetBrains Mono, monospace', fontSize: 10,
      color: C.cyan,
      background: 'rgba(0,234,255,0.08)',
      border: '1px solid rgba(0,234,255,0.20)',
      padding: '2px 8px',
      borderRadius: 3,
    }}>
      {name}
    </span>
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

  const [claimsData, setClaimsData]     = useState(null)
  const [selectedId, setSelectedId]     = useState(null)
  const [spec, setSpec]                 = useState(null)
  const [specLoading, setSpecLoading]   = useState(false)
  const [feed, setFeed]                 = useState([])
  const [jobStatus, setJobStatus]       = useState('processing')
  const [zipReady, setZipReady]         = useState(false)
  const [uploading, setUploading]       = useState(false)
  const [analysisStatus, setAnalysisStatus] = useState(null)
  const [report, setReport]             = useState(null)
  const [reproStatuses, setReproStatuses] = useState({})

  const feedRef     = useRef(null)
  const fileInputRef = useRef(null)

  // Load + poll claims
  useEffect(() => {
    const load = () =>
      api.poc.claims(sessionId)
        .then(setClaimsData)
        .catch(() => {})
    load()
    const t = setInterval(load, 3000)
    return () => clearInterval(t)
  }, [sessionId])

  // SSE stream
  useEffect(() => {
    const es = api.poc.stream(sessionId)

    const refresh = () =>
      api.poc.claims(sessionId).then(setClaimsData).catch(() => {})

    es.addEventListener('atom_created', (e) => {
      setFeed(f => [...f, { event_type: 'atom_created', payload: JSON.parse(e.data) }])
      refresh()
    })
    es.addEventListener('check_complete', (e) => {
      setFeed(f => [...f, { event_type: 'check_complete', payload: JSON.parse(e.data) }])
      refresh()
    })
    es.addEventListener('report_ready', (e) => {
      setFeed(f => [...f, { event_type: 'report_ready', payload: JSON.parse(e.data) }])
      setZipReady(true)
      setJobStatus('complete')
    })
    es.onerror = () => setJobStatus(s => s === 'processing' ? 'complete' : s)

    return () => es.close()
  }, [sessionId])

  // Auto-scroll feed
  useEffect(() => {
    if (feedRef.current) feedRef.current.scrollTop = feedRef.current.scrollHeight
  }, [feed])

  // Load spec when testable claim selected
  useEffect(() => {
    if (!selectedId) { setSpec(null); return }
    const claim = claimsData?.claims?.find(c => c.claim_id === selectedId)
    if (claim?.testability !== 'testable') { setSpec(null); return }
    setSpecLoading(true)
    api.poc.spec(sessionId, selectedId)
      .then(s => { setSpec(s); setSpecLoading(false) })
      .catch(() => { setSpec(null); setSpecLoading(false) })
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
    <div style={{ background: C.bg, minHeight: '100vh', display: 'flex', flexDirection: 'column', ...grotesk(), color: C.text, overflow: 'hidden' }}>
      {/* Header */}
      <div style={{ background: C.surface, borderBottom: `1px solid ${C.border}`, padding: '8px 16px', display: 'flex', alignItems: 'center', gap: 12, flexShrink: 0, height: 44 }}>
        <button onClick={() => navigate('/')} style={{ ...mono(11), background: 'none', border: `1px solid ${C.border}`, color: C.muted, cursor: 'pointer', padding: '3px 8px', borderRadius: 3 }}>← HOME</button>
        <div style={{ width: 1, height: 16, background: C.border }} />
        <span style={{ ...mono(11), color: C.muted }}>POC /</span>
        <span style={{ ...mono(11, 600), color: C.text }}>{sessionId}</span>
        <div style={{ flex: 1 }} />
        {claimsData && (<span style={{ ...mono(10), color: C.muted }}>{claimsData.testable} testable · {claimsData.theoretical} theoretical</span>)}
        <div style={{ ...mono(10, 700), padding: '3px 8px', borderRadius: 3, background: statusChipStyle.bg, border: `1px solid ${statusChipStyle.border}`, color: statusChipStyle.color }}>{statusChipStyle.label}</div>
      </div>
      {/* Body: three columns */}
      <div style={{ flex: 1, display: 'flex', overflow: 'hidden', minHeight: 0 }}>
        {/* Claims list */}
        <div style={{ width: 280, flexShrink: 0, background: C.sunken, borderRight: `1px solid ${C.border}`, display: 'flex', flexDirection: 'column', overflow: 'hidden' }}>
          <div style={{ padding: '7px 12px', borderBottom: `1px solid ${C.border}`, ...mono(9, 700), color: C.muted, letterSpacing: '0.1em', textTransform: 'uppercase', flexShrink: 0 }}>CLAIMS {claimsData ? `(${claimsData.total})` : ''}</div>
          <div style={{ flex: 1, overflowY: 'auto' }}>
            {!claimsData ? (
              <div style={{ padding: 16, ...mono(11), color: C.muted }}>Loading…</div>
            ) : claimsData.claims.length === 0 ? (
              <div style={{ padding: 16, ...mono(11), color: C.muted }}>{jobStatus === 'processing' ? '⟳ Extracting claims…' : 'No claims found.'}</div>
            ) : (
              claimsData.claims.map(claim => (
                <ClaimRow
                  key={claim.claim_id}
                  claim={claim}
                  selected={selectedId === claim.claim_id}
                  reproStatus={reproStatuses[claim.claim_id]}
                  onClick={() => setSelectedId(selectedId === claim.claim_id ? null : claim.claim_id)}
                />
              ))
            )}
          </div>
        </div>
        {/* Claim detail */}
        <div style={{ width: 380, flexShrink: 0, background: C.surface, borderRight: `1px solid ${C.border}`, overflowY: 'auto', padding: 20, minWidth: 0, transition: 'box-shadow 0.2s' }}>
          {!selectedClaim ? (<div style={{ height: '100%', display: 'flex', alignItems: 'center', justifyContent: 'center', flexDirection: 'column', gap: 8 }}><span style={{ ...mono(12), color: C.muted }}>Select a claim from the left panel</span>{jobStatus === 'processing' && (<span style={{ ...mono(11), color: C.indigo }}>⟳ Pipeline running…</span>)}</div>) : (<><div style={{ marginBottom: 16 }}><div style={{ display: 'flex', alignItems: 'center', gap: 7, flexWrap: 'wrap', marginBottom: 8 }}><TestabilityChip testability={selectedClaim.testability} />{selectedClaim.claim_type && (<Chip>{selectedClaim.claim_type}</Chip>)}<ReproChip status={reproStatuses[selectedClaim.claim_id]} /></div><div style={{ ...mono(10), color: C.muted, marginBottom: 8 }}>{selectedClaim.claim_id}</div><p style={{ ...grotesk(14), color: C.text, lineHeight: 1.65, margin: 0 }}>{selectedClaim.text}</p></div>{selectedClaim.testability === 'theoretical' && (<div style={{ padding: '10px 12px', background: 'rgba(107,114,128,0.07)', border: `1px solid ${C.border}`, borderRadius: 4, ...grotesk(12), color: C.muted, lineHeight: 1.5 }}>This claim is theoretical — no executable scaffold can be generated.{selectedClaim.spec_summary?.reason && (<div style={{ ...mono(10), marginTop: 6 }}>reason: {selectedClaim.spec_summary.reason}</div>)}</div>)}{selectedClaim.testability === 'testable' && (specLoading ? (<div style={{ ...mono(11), color: C.muted }}>⟳ Loading spec…</div>) : !spec ? (<div style={{ ...mono(11), color: C.muted }}>{jobStatus === 'processing' ? '⟳ Scaffold generating…' : 'No spec available.'}</div>) : (<><section style={{ marginBottom: 20 }}>{spec.success_criteria?.length > 0 && (<><SectionLabel>Success Criteria</SectionLabel>{spec.success_criteria.map((c, i) => (<SuccessCriterion key={i} c={c} />))}</>)}{spec.environment && Object.keys(spec.environment).length > 0 && (<><SectionLabel>Environment</SectionLabel><div style={{ background: C.sunken, border: `1px solid ${C.border}`, borderRadius: 4, padding: '8px 10px' }}>{Object.entries(spec.environment).map(([k, v]) => (<div key={k} style={{ display: 'flex', gap: 12, marginBottom: 4 }}><span style={{ ...mono(11), color: C.muted, minWidth: 100 }}>{k}</span><span style={{ ...mono(11), color: C.text }}>{String(v)}</span></div>))}</div></>)}{spec.scaffold_files && Object.keys(spec.scaffold_files).length > 0 && (<><SectionLabel>Scaffold Files</SectionLabel><div style={{ display: 'flex', gap: 6, flexWrap: 'wrap', marginBottom: 10 }}>{Object.keys(spec.scaffold_files).map(name => (<ScaffoldFileChip key={name} name={name} />))}</div>{spec.scaffold_files['README.md'] && (<><div style={{ ...mono(10), color: C.muted, marginBottom: 4 }}>README.md</div><pre style={{ background: C.sunken, border: `1px solid ${C.border}`, borderRadius: 4, padding: '10px 12px', ...mono(11), color: C.text, whiteSpace: 'pre-wrap', maxHeight: 220, overflowY: 'auto', margin: 0 }}>{spec.scaffold_files['README.md']}</pre></>)}</>)}{report && (<ReportPanel report={{ summary: report.summary, results: (report.results || []).filter(r => r.claim_id === selectedClaim.claim_id) }} />)}</section></>))}</>)}
        </div>
        {/* Activity feed */}
        <div style={{ width: 280, flexShrink: 0, background: C.sunken, borderLeft: `1px solid ${C.border}`, display: 'flex', flexDirection: 'column', overflow: 'hidden' }}>
          <div style={{ padding: '7px 12px', borderBottom: `1px solid ${C.border}`, ...mono(9, 700), color: C.muted, letterSpacing: '0.1em', textTransform: 'uppercase', flexShrink: 0 }}>ACTIVITY FEED</div>
          <div ref={feedRef} style={{ flex: 1, overflowY: 'auto' }}>{feed.length === 0 ? (<div style={{ padding: 12, ...mono(10), color: C.muted }}>Waiting for events…</div>) : (feed.map((ev, i) => <FeedRow key={i} event={ev} />))}</div>
        </div>
      </div>
      {/* Bottom action bar */}
      <div style={{ background: C.surface, borderTop: `1px solid ${C.border}`, padding: '9px 16px', display: 'flex', alignItems: 'center', gap: 10, flexShrink: 0 }}>
        <button onClick={() => window.open(`/api/poc/${sessionId}/scaffold.zip`, '_blank')} disabled={!zipReady} style={{ ...mono(11, 700), letterSpacing: '0.05em', padding: '5px 14px', borderRadius: 3, border: `1px solid ${zipReady ? C.indigo : C.border}`, background: zipReady ? 'rgba(91,91,214,0.15)' : 'rgba(255,255,255,0.03)', color: zipReady ? C.indigo : C.muted, cursor: zipReady ? 'pointer' : 'not-allowed' }}>↓ SCAFFOLD.ZIP</button>
        <div style={{ width: 1, height: 16, background: C.border }} />
        <input ref={fileInputRef} type="file" accept=".json" onChange={handleUpload} style={{ display: 'none' }} />
        <button onClick={() => fileInputRef.current?.click()} disabled={!zipReady || uploading} style={{ ...mono(11, 700), letterSpacing: '0.05em', padding: '5px 14px', borderRadius: 3, border: `1px solid ${zipReady && !uploading ? C.cyan : C.border}`, background: zipReady && !uploading ? 'rgba(0,234,255,0.08)' : 'rgba(255,255,255,0.03)', color: zipReady && !uploading ? C.cyan : C.muted, cursor: zipReady && !uploading ? 'pointer' : 'not-allowed' }}>{uploading ? '⟳ UPLOADING…' : '↑ UPLOAD RESULTS.JSON'}</button>
        {analysisStatus === 'analyzing' && (<span style={{ ...mono(11), color: C.indigo }}>⟳ Analyzing results…</span>)}
        {analysisStatus === 'complete' && report && (<span style={{ ...mono(11), color: '#22C55E' }}>✓ Analysis complete — {report.results?.length ?? 0} results</span>)}
        <div style={{ flex: 1 }} />
        <span style={{ ...mono(10), color: C.muted }}>{!zipReady ? 'Generating scaffolds…' : analysisStatus !== 'complete' ? 'Download scaffold → run pytest → upload poc_results.json' : 'Reproducibility analysis complete'}</span>
      </div>
    </div>
  );
}
