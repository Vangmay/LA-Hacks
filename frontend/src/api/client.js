const BASE = '/api'

async function postFile(url, file) {
  const fd = new FormData()
  if (file) fd.append('file', file)
  const r = await fetch(url, { method: 'POST', body: fd })
  return r.json()
}

async function postJson(url, body) {
  const r = await fetch(url, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  })
  return r.json()
}

export const api = {
  review: {
    submit: (arxivUrl) => postJson(`${BASE}/review/arxiv`, { arxiv_url: arxivUrl }),
    status: (jobId) => fetch(`${BASE}/review/${jobId}/status`).then(r => r.json()),
    dag: (jobId) => fetch(`${BASE}/review/${jobId}/dag`).then(r => r.json()),
    atom: (jobId, atomId) => fetch(`${BASE}/review/${jobId}/atoms/${atomId}`).then(r => r.json()),
    stream: (jobId) => new EventSource(`${BASE}/review/${jobId}/stream`),
    report: (jobId) => fetch(`${BASE}/review/${jobId}/report`).then(r => r.json()),
    reportMarkdown: (jobId) => fetch(`${BASE}/review/${jobId}/report/markdown`).then(r => r.text()),
  },
  poc: {
    submit: (file) => postFile(`${BASE}/poc`, file),
    claims: (sessionId) => fetch(`${BASE}/poc/${sessionId}/claims`).then(r => r.json()),
    spec: (sessionId, claimId) => fetch(`${BASE}/poc/${sessionId}/claim/${claimId}/spec`).then(r => r.json()),
    uploadResults: (sessionId, file) => postFile(`${BASE}/poc/${sessionId}/results`, file),
    uploadResultsJson: (sessionId, data) => postJson(`${BASE}/poc/${sessionId}/results`, data),
    report: (sessionId) => fetch(`${BASE}/poc/${sessionId}/report`).then(r => r.json()),
    reportMarkdown: (sessionId) => fetch(`${BASE}/poc/${sessionId}/report/markdown`).then(r => r.text()),
    stream: (sessionId) => new EventSource(`${BASE}/poc/${sessionId}/stream`),
    dag: (sessionId) => fetch(`${BASE}/poc/${sessionId}/dag`).then(r => r.json()),
    scaffoldZipUrl: (sessionId) => `${BASE}/poc/${sessionId}/scaffold.zip`,
  },
}
