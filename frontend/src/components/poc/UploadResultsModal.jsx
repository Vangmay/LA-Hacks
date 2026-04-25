import { useState, useRef } from 'react'
import { api } from '../../api/client'

export default function UploadResultsModal({ sessionId, onClose, onComplete }) {
  const fileInputRef = useRef(null)
  const [dragging, setDragging] = useState(false)
  const [file, setFile] = useState(null)
  const [preview, setPreview] = useState(null)
  const [uploading, setUploading] = useState(false)
  const [error, setError] = useState(null)
  const [done, setDone] = useState(false)

  function readFile(f) {
    setFile(f)
    setError(null)
    const reader = new FileReader()
    reader.onload = (e) => {
      const text = e.target.result
      const lines = text.split('\n').slice(0, 20)
      setPreview(lines.join('\n'))
    }
    reader.readAsText(f)
  }

  function onDrop(e) {
    e.preventDefault()
    setDragging(false)
    const f = e.dataTransfer.files?.[0]
    if (f) readFile(f)
  }

  async function handleUpload() {
    if (!file) return
    setUploading(true)
    setError(null)
    try {
      const result = await api.poc.uploadResults(sessionId, file)
      if (result.status === 'analyzing') {
        setDone(true)
        setTimeout(() => {
          onComplete?.()
          onClose()
        }, 1500)
      } else {
        setError(`Unexpected response: ${JSON.stringify(result)}`)
      }
    } catch (e) {
      setError('Upload failed: ' + e.message)
    } finally {
      setUploading(false)
    }
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center" style={{ background: 'rgba(0,0,0,0.75)' }}>
      <div className="relative rounded-xl border border-[#2a2e3f] w-[520px] max-h-[80vh] flex flex-col" style={{ background: '#14181f' }}>
        {/* Header */}
        <div className="flex items-center justify-between px-5 py-3 border-b border-[#2a2e3f]">
          <div>
            <div className="text-xs text-[#a3e635] tracking-widest font-bold">UPLOAD RESULTS</div>
            <div className="text-[10px] text-[#4b5563] mt-0.5">Drop your poc_results.json file</div>
          </div>
          <button onClick={onClose} className="text-[#4b5563] hover:text-white text-xl leading-none">×</button>
        </div>

        <div className="flex-1 overflow-y-auto p-4">
          {done ? (
            <div className="flex flex-col items-center justify-center py-8 gap-3">
              <div className="text-4xl">✓</div>
              <div className="text-[#86efac] text-sm font-bold tracking-widest">ANALYZING RESULTS...</div>
              <div className="text-[#4b5563] text-xs">Results are being processed. The report will update shortly.</div>
            </div>
          ) : (
            <>
              {/* Drop zone */}
              <div
                className={`border-2 border-dashed rounded-lg p-6 flex flex-col items-center justify-center cursor-pointer transition-all mb-3 ${
                  dragging ? 'border-[#a3e635] bg-[#a3e635]/5' : 'border-[#2a2e3f] hover:border-[#4b5563]'
                }`}
                onDragOver={e => { e.preventDefault(); setDragging(true) }}
                onDragLeave={() => setDragging(false)}
                onDrop={onDrop}
                onClick={() => fileInputRef.current?.click()}
              >
                <input
                  ref={fileInputRef}
                  type="file"
                  accept=".json"
                  className="hidden"
                  onChange={e => { const f = e.target.files?.[0]; if (f) readFile(f); e.target.value = '' }}
                />
                <div className="text-2xl mb-2">📄</div>
                {file ? (
                  <div className="text-center">
                    <div className="text-[#a3e635] text-sm font-bold">{file.name}</div>
                    <div className="text-[#4b5563] text-[10px] mt-0.5">{(file.size / 1024).toFixed(1)} KB · Click to replace</div>
                  </div>
                ) : (
                  <div className="text-center">
                    <div className="text-[#94a3b8] text-sm">Drop JSON file here</div>
                    <div className="text-[#4b5563] text-[10px] mt-0.5">or click to browse</div>
                  </div>
                )}
              </div>

              {/* Preview */}
              {preview && (
                <div className="mb-3">
                  <div className="text-[10px] text-[#4b5563] tracking-widest mb-1">PREVIEW (first 20 lines)</div>
                  <pre className="bg-[#0d1117] rounded p-2 text-[10px] font-mono text-[#94a3b8] overflow-x-auto max-h-36 overflow-y-auto whitespace-pre">
                    {preview}
                  </pre>
                </div>
              )}

              {error && (
                <div className="text-red-400 text-xs mb-2 bg-red-900/20 rounded px-3 py-2">{error}</div>
              )}
            </>
          )}
        </div>

        {!done && (
          <div className="flex gap-2 px-4 pb-4">
            <button
              className="flex-1 py-2 rounded-lg text-xs text-[#4b5563] border border-[#2a2e3f] hover:text-[#94a3b8] transition-all"
              onClick={onClose}
            >
              CANCEL
            </button>
            <button
              className={`flex-1 py-2 rounded-lg text-xs font-bold tracking-widest transition-all ${
                file && !uploading
                  ? 'bg-[#a3e635]/20 text-[#a3e635] border border-[#a3e635]/40 hover:bg-[#a3e635]/30'
                  : 'text-[#374151] border border-[#2a2e3f] cursor-not-allowed'
              }`}
              disabled={!file || uploading}
              onClick={handleUpload}
            >
              {uploading ? (
                <span className="flex items-center justify-center gap-2">
                  <span className="w-3 h-3 border-2 border-[#a3e635] border-t-transparent rounded-full animate-spin" />
                  UPLOADING...
                </span>
              ) : 'CONFIRM UPLOAD'}
            </button>
          </div>
        )}
      </div>
    </div>
  )
}
