const BASE = '/api/formalize'

async function parseJson(response) {
  const data = await response.json().catch(() => ({}))
  if (!response.ok) {
    throw new Error(data.detail || data.error || `Request failed with ${response.status}`)
  }
  return data
}

async function postJson(url, body = {}) {
  const response = await fetch(url, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  })
  return parseJson(response)
}

export const formalizationApi = {
  start: (jobId, atomIds = null, options = {}) =>
    postJson(`${BASE}/${jobId}`, { atom_ids: atomIds, options }),
  startAtom: (jobId, atomId, options = {}) =>
    postJson(`${BASE}/${jobId}/atom/${atomId}`, { options }),
  run: (runId) => fetch(`${BASE}/runs/${runId}`).then(parseJson),
  atom: (runId, atomId) => fetch(`${BASE}/runs/${runId}/atom/${atomId}`).then(parseJson),
  stream: (runId) => new EventSource(`${BASE}/runs/${runId}/stream`),
  leanUrl: (runId) => `${BASE}/runs/${runId}/lean`,
}
