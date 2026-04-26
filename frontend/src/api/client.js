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

async function pocFetch(url) {
  const r = await fetch(url)
  const data = await r.json().catch(() => ({}))
  if (!r.ok) throw new Error(data.detail || data.error || `HTTP ${r.status}`)
  return data
}

async function pocPost(url, body) {
  const r = await fetch(url, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  })
  const data = await r.json().catch(() => ({}))
  if (!r.ok) throw new Error(data.detail || data.error || `HTTP ${r.status}`)
  return data
}

async function fetchResearchJson(url) {
  const r = await fetch(url)
  const text = await r.text()
  let data = {}
  if (text) {
    try {
      data = JSON.parse(text)
    } catch (err) {
      throw new Error(`Research API returned invalid JSON from ${url}`)
    }
  }
  if (!r.ok) {
    throw new Error(data.detail || data.error || `Research API request failed with ${r.status}`)
  }
  return data
}

async function postResearchJson(url, body) {
  const r = await fetch(url, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  })
  const data = await r.json().catch(() => ({}))
  if (!r.ok) {
    throw new Error(data.detail || data.error || `Research API request failed with ${r.status}`)
  }
  return data
}

export const api = {
  reader: {
    submit: (arxivUrl, level = 'undergraduate') => {
      const fd = new FormData()
      fd.append('arxiv_url', arxivUrl)
      fd.append('level', level)
      return fetch(`${BASE}/read`, { method: 'POST', body: fd }).then(r => r.json())
    },
    status: (sessionId) => fetch(`${BASE}/read/${sessionId}/status`).then(r => r.json()),
    graph: (sessionId) => fetch(`${BASE}/read/${sessionId}/graph`).then(r => r.json()),
    atom: (sessionId, atomId, level) => {
      const query = level ? `?level=${encodeURIComponent(level)}` : ''
      return fetch(`${BASE}/read/${sessionId}/atom/${atomId}${query}`).then(r => r.json())
    },
    tutor: (sessionId, atomId, message, history = []) =>
      postJson(`${BASE}/read/${sessionId}/atom/${atomId}/tutor`, { message, history }),
    grade: (sessionId, atomId, exerciseId, answer) =>
      postJson(`${BASE}/read/${sessionId}/atom/${atomId}/grade`, { exercise_id: exerciseId, answer }),
    studyGuide: (sessionId) => fetch(`${BASE}/read/${sessionId}/study-guide`).then(r => r.text()),
  },
  review: {
    submit: (arxivUrl) => postJson(`${BASE}/review/arxiv`, { arxiv_url: arxivUrl }),
    status: (jobId) => fetch(`${BASE}/review/${jobId}/status`).then(r => r.json()),
    dag: (jobId) => fetch(`${BASE}/review/${jobId}/dag`).then(r => r.json()),
    atom: (jobId, atomId) => fetch(`${BASE}/review/${jobId}/atoms/${atomId}`).then(r => r.json()),
    stream: (jobId) => new EventSource(`${BASE}/review/${jobId}/stream`),
    report: (jobId) => fetch(`${BASE}/review/${jobId}/report`).then(r => r.json()),
    reportMarkdown: (jobId) => fetch(`${BASE}/review/${jobId}/report/markdown`).then(r => r.text()),
  },
  research: {
    runs: () => fetchResearchJson(`${BASE}/research/runs`),
    start: (req) => postResearchJson(`${BASE}/research/start`, req),
    status: (runId) => fetchResearchJson(`${BASE}/research/${runId}/status`),
    snapshot: (runId) => fetchResearchJson(`${BASE}/research/${runId}/snapshot`),
    stream: (runId) => new EventSource(`${BASE}/research/${runId}/stream`),
    artifact: (runId, path) =>
      fetchResearchJson(`${BASE}/research/${runId}/artifacts/${encodeURI(path)}`),
    report: (runId) => fetchResearchJson(`${BASE}/research/${runId}/report`),
    reportMarkdown: (runId) => fetch(`${BASE}/research/${runId}/report/markdown`).then(r => r.text()),
    shared: (runId, artifact) => fetchResearchJson(`${BASE}/research/${runId}/shared/${artifact}`),
    critique: (runId, criticId) => fetchResearchJson(`${BASE}/research/${runId}/critique/${criticId}`),
  },
  poc: {
    submit: (arxivUrl) => pocPost(`${BASE}/poc`, { arxiv_url: arxivUrl }),
    claims: (sessionId) => pocFetch(`${BASE}/poc/${sessionId}/claims`),
    spec: (sessionId, claimId) => pocFetch(`${BASE}/poc/${sessionId}/claim/${claimId}/spec`),
    generateScaffolds: (sessionId, claimIds) =>
      pocPost(`${BASE}/poc/${sessionId}/scaffold`, { claim_ids: claimIds }),
    scaffoldStatus: (sessionId) => pocFetch(`${BASE}/poc/${sessionId}/scaffold/status`),
    uploadResults: (sessionId, file) => postFile(`${BASE}/poc/${sessionId}/results`, file),
    report: (sessionId) => pocFetch(`${BASE}/poc/${sessionId}/report`),
    stream: (sessionId) => new EventSource(`${BASE}/poc/${sessionId}/stream`),
    dag: (sessionId) => pocFetch(`${BASE}/poc/${sessionId}/dag`),
  },
}
