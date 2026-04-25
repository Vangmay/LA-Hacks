import { useState, useEffect, useCallback, useRef } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { api } from '../api/client'
import PoCDagCanvas from '../components/poc/PoCDagCanvas'
import ClaimListPanel from '../components/poc/ClaimListPanel'
import SpecPanel from '../components/poc/SpecPanel'
import ActivityFeed from '../components/poc/ActivityFeed'
import UploadResultsModal from '../components/poc/UploadResultsModal'
import ReproducibilityReportView from '../components/poc/ReproducibilityReportView'

function timestamp() {
  return new Date().toLocaleTimeString('en-US', { hour12: false, hour: '2-digit', minute: '2-digit', second: '2-digit' })
}

export default function PoCPage() {
  const { sessionId } = useParams()
  const navigate = useNavigate()

  const [dag, setDag] = useState({ nodes: [], edges: [] })
  const [claims, setClaims] = useState({ total: 0, testable: 0, theoretical: 0, claims: [] })
  const [report, setReport] = useState(null)
  const [selectedClaimId, setSelectedClaimId] = useState(null)
  const [specData, setSpecData] = useState(null)
  const [showOnlyTestable, setShowOnlyTestable] = useState(false)
  const [activities, setActivities] = useState([])
  const [showModal, setShowModal] = useState(false)
  const [showReport, setShowReport] = useState(false)
  const [paperTitle, setPaperTitle] = useState('')
  const [isProcessing, setIsProcessing] = useState(true)
  const streamRef = useRef(null)
  const pollRef = useRef(null)

  function addActivity(type, message, color) {
    setActivities(prev => [...prev.slice(-99), { type, message, color, time: timestamp() }])
  }

  const fetchDag = useCallback(() => {
    api.poc.dag(sessionId).then(data => {
      if (data?.nodes) setDag(data)
    }).catch(() => {})
  }, [sessionId])

  const fetchClaims = useCallback(() => {
    api.poc.claims(sessionId).then(data => {
      if (data?.claims !== undefined) setClaims(data)
    }).catch(() => {})
  }, [sessionId])

  const fetchReport = useCallback(() => {
    api.poc.report(sessionId).then(data => {
      if (data?.session_id) {
        setReport(data)
        if (data.paper_title) setPaperTitle(data.paper_title)
      }
    }).catch(() => {})
  }, [sessionId])

  // Initial load
  useEffect(() => {
    fetchDag()
    fetchClaims()
  }, [fetchDag, fetchClaims])

  // SSE stream
  useEffect(() => {
    const es = api.poc.stream(sessionId)
    streamRef.current = es

    es.addEventListener('node_classified', (e) => {
      const d = JSON.parse(e.data)
      const label = d.testability === 'testable' ? '✓' : '·'
      addActivity('node_classified', `${label} Claim ${d.claim_id ?? ''}: ${d.testability}`, d.testability === 'testable' ? '#86efac' : '#6b7280')
      fetchDag()
      fetchClaims()
    })

    es.addEventListener('scaffold_generated', (e) => {
      const d = JSON.parse(e.data)
      addActivity('scaffold_generated', `⚙ Scaffold generated for ${d.claim_id ?? 'claim'} (${d.status})`, '#93c5fd')
      fetchClaims()
    })

    es.addEventListener('poc_ready', (e) => {
      const d = JSON.parse(e.data)
      addActivity('poc_ready', `📦 Scaffold ready — ${d.testable_count ?? ''} testable claims`, '#a3e635')
      setIsProcessing(false)
      fetchDag()
      fetchClaims()
    })

    es.addEventListener('status', (e) => {
      try {
        const d = JSON.parse(e.data)
        if (d.status === 'complete') {
          setIsProcessing(false)
          fetchDag()
          fetchClaims()
        } else if (d.status === 'error') {
          addActivity('error', `✗ Processing error: ${d.error || 'Unknown'}`, '#fca5a5')
          setIsProcessing(false)
        }
      } catch {}
    })

    es.onerror = () => {
      // SSE closed or backend done — stop trying
      if (es.readyState === EventSource.CLOSED) setIsProcessing(false)
    }

    return () => es.close()
  }, [sessionId, fetchDag, fetchClaims])

  // Poll for report when analysis is running
  useEffect(() => {
    if (!isProcessing && !report) {
      pollRef.current = setInterval(fetchReport, 3000)
    }
    return () => clearInterval(pollRef.current)
  }, [isProcessing, report, fetchReport])

  // When report arrives, stop polling and add activity
  useEffect(() => {
    if (report) {
      clearInterval(pollRef.current)
      addActivity('analysis_complete', `✓ Analysis complete — ${(report.reproduction_rate * 100).toFixed(0)}% reproduced`, '#86efac')
      if (report.paper_title) setPaperTitle(report.paper_title)
    }
  }, [report?.session_id])

  async function handleNodeClick(claimId) {
    setSelectedClaimId(claimId)
    setSpecData(null)
    try {
      const spec = await api.poc.spec(sessionId, claimId)
      setSpecData(spec)
    } catch {
      setSpecData(null)
    }
  }

  function handleDownloadScaffold() {
    window.open(api.poc.scaffoldZipUrl(sessionId), '_blank')
  }

  function handleUploadComplete() {
    addActivity('results_uploaded', '📊 Results uploaded — analyzing...', '#fcd34d')
    // Start polling for report
    pollRef.current = setInterval(() => {
      fetchReport()
    }, 2000)
  }

  return (
    <div className="h-screen w-screen flex flex-col overflow-hidden" style={{ background: '#131714', fontFamily: 'Fira Sans, sans-serif' }}>
      {/* Header */}
      <div className="flex items-center justify-between px-5 py-2.5 border-b border-[#1e2a1e]" style={{ background: '#0f1510' }}>
        <div className="flex items-center gap-4">
          <button
            onClick={() => navigate('/')}
            className="text-[#4b5563] hover:text-[#a3e635] text-xs tracking-widest transition-colors"
          >
            ← VERIDIAN
          </button>
          <div className="w-px h-4 bg-[#2a2e3f]" />
          <div className="flex items-center gap-2">
            <span className="text-[10px] px-2 py-0.5 rounded tracking-widest font-bold" style={{ background: '#1a2a1a', color: '#a3e635', border: '1px solid #a3e63540' }}>
              EXECUTE / POC
            </span>
            {paperTitle && (
              <span className="text-xs text-[#94a3b8] max-w-xs truncate">{paperTitle}</span>
            )}
          </div>
        </div>

        <div className="flex items-center gap-3">
          {isProcessing && (
            <div className="flex items-center gap-2 text-[10px] text-[#a3e635] tracking-widest">
              <span className="w-2 h-2 rounded-full bg-[#a3e635] animate-pulse" />
              PROCESSING
            </div>
          )}
          <div className="text-[10px] text-[#4b5563] font-mono">{sessionId?.slice(0, 8)}</div>
          {/* Testable toggle */}
          <button
            onClick={() => setShowOnlyTestable(v => !v)}
            className={`text-[10px] px-2.5 py-1 rounded tracking-wider font-bold border transition-all ${
              showOnlyTestable
                ? 'bg-[#a3e635]/20 text-[#a3e635] border-[#a3e635]/40'
                : 'text-[#4b5563] border-[#2a2e3f] hover:text-[#94a3b8]'
            }`}
          >
            TESTABLE ONLY
          </button>
        </div>
      </div>

      {/* Main content */}
      <div className="flex flex-1 overflow-hidden">
        {/* DAG canvas (65%) */}
        <div className="flex flex-col border-r border-[#1e2a1e]" style={{ width: '65%', background: '#0d110e' }}>
          <div className="px-4 pt-3 pb-1 flex items-center justify-between">
            <div className="text-[10px] text-[#4b5563] tracking-widest">CLAIM DEPENDENCY GRAPH</div>
            <div className="text-[10px] text-[#4b5563]">
              {dag.nodes.length} nodes · {dag.edges.length} edges
            </div>
          </div>
          <PoCDagCanvas
            nodes={dag.nodes}
            edges={dag.edges}
            selectedClaimId={selectedClaimId}
            showOnlyTestable={showOnlyTestable}
            onNodeClick={handleNodeClick}
          />
        </div>

        {/* Right panel (35%) */}
        <div className="flex flex-col overflow-hidden" style={{ width: '35%' }}>
          {selectedClaimId ? (
            <SpecPanel
              claimId={selectedClaimId}
              claims={claims}
              specData={specData}
              report={report}
              onClose={() => setSelectedClaimId(null)}
            />
          ) : (
            <ClaimListPanel
              claims={claims}
              report={report}
              onClaimClick={handleNodeClick}
              onDownloadScaffold={handleDownloadScaffold}
              onUploadResults={() => setShowModal(true)}
              onViewReport={() => setShowReport(true)}
            />
          )}
        </div>
      </div>

      {/* Activity feed */}
      <ActivityFeed activities={activities} />

      {/* Modals */}
      {showModal && (
        <UploadResultsModal
          sessionId={sessionId}
          onClose={() => setShowModal(false)}
          onComplete={handleUploadComplete}
        />
      )}
      {showReport && (
        <ReproducibilityReportView
          sessionId={sessionId}
          report={report}
          onClose={() => setShowReport(false)}
        />
      )}
    </div>
  )
}
