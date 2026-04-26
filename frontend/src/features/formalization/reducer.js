import { FORMALIZATION_EVENTS } from './types'

export const initialFormalizationState = withCounts({
  runId: null,
  status: 'idle',
  selected: { kind: 'run', id: 'run' },
  selectedAtomId: null,
  atomOrder: [],
  atoms: {},
  events: [],
  summary: {},
  runtime: {},
  error: '',
  connection: 'idle',
})

export function formalizationReducer(state, action) {
  switch (action.type) {
    case 'START_RESPONSE':
      return startState(state, action.payload)
    case 'RUN_SNAPSHOT':
      return snapshotToState(state, action.payload)
    case 'SELECT':
      return { ...state, selected: action.selected }
    case 'SELECT_ATOM':
      return { ...state, selectedAtomId: action.atomId, selected: { kind: 'atom', id: action.atomId } }
    case 'CONNECTION_STATE':
      return { ...state, connection: action.connection, error: action.error || state.error }
    case 'ERROR':
      return { ...state, error: action.error || 'Formalization failed', connection: 'disconnected' }
    case 'EVENT':
      return applyEvent(state, action.event)
    default:
      return state
  }
}

function startState(state, payload = {}) {
  const atomOrder = payload.selected_atom_ids || []
  const atoms = Object.fromEntries(atomOrder.map((atomId) => [atomId, emptyAtom(atomId)]))
  return withCounts({
    ...initialFormalizationState,
    runId: payload.run_id,
    status: payload.status || 'queued',
    atomOrder,
    atoms,
    runtime: payload.runtime || {},
    connection: 'connecting',
    selectedAtomId: atomOrder[0] || state.selectedAtomId,
    selected: atomOrder[0] ? { kind: 'atom', id: atomOrder[0] } : { kind: 'run', id: payload.run_id || 'run' },
  })
}

function snapshotToState(state, run = {}) {
  const atomOrder = run.selected_atom_ids || state.atomOrder || []
  const atoms = {}
  for (const atomId of atomOrder) {
    atoms[atomId] = hydrateAtom(atomId, run.atom_formalizations?.[atomId] || state.atoms[atomId])
  }
  return withCounts({
    ...state,
    runId: run.run_id || state.runId,
    status: run.status || state.status,
    atomOrder,
    atoms,
    summary: run.summary || state.summary || {},
    runtime: run.runtime || state.runtime || {},
    error: run.error || state.error,
    connection: ['complete', 'error'].includes(run.status) ? 'closed' : state.connection,
    selectedAtomId: state.selectedAtomId || atomOrder[0] || null,
    selected: state.selected || (atomOrder[0] ? { kind: 'atom', id: atomOrder[0] } : { kind: 'run', id: run.run_id || 'run' }),
  })
}

function applyEvent(state, event) {
  const eventType = event.event_type
  if (eventType === FORMALIZATION_EVENTS.RUN_SNAPSHOT) {
    const next = snapshotToState(state, event.payload?.run || {})
    return withCounts({
      ...next,
      runtime: event.payload?.runtime || next.runtime,
      connection: event.payload?.live === false ? 'closed' : 'connected',
    })
  }

  const events = [...state.events, event].slice(-600)
  const atomId = event.atom_id || event.payload?.atom_id
  let next = { ...state, events, connection: 'connected' }

  if (eventType === FORMALIZATION_EVENTS.RUN_STARTED) {
    next.status = 'running'
    next.runtime = event.payload?.runtime || next.runtime
  }

  if (eventType === FORMALIZATION_EVENTS.ATOM_QUEUED && atomId) {
    next = upsertAtom(next, atomId, {
      status: 'queued',
      text: event.payload?.text,
      atom_type: event.payload?.atom_type,
      importance: event.payload?.importance,
      section_id: event.payload?.section_id,
      section_heading: event.payload?.section_heading,
      queue_index: event.payload?.queue_index,
      queue_total: event.payload?.queue_total,
      max_iterations: event.payload?.max_iterations,
      max_axle_calls: event.payload?.max_axle_calls,
    })
  }

  if (eventType === FORMALIZATION_EVENTS.ATOM_CONTEXT_BUILT && atomId) {
    next = upsertAtom(next, atomId, {
      status: 'building_context',
      text: event.payload?.atom_text || next.atoms[atomId]?.text,
      section_heading: event.payload?.section_heading || next.atoms[atomId]?.section_heading,
      context: event.payload,
    })
  }

  if (eventType === FORMALIZATION_EVENTS.LLM_THOUGHT && atomId) {
    next = upsertAtom(next, atomId, appendThought(next.atoms[atomId], event.payload))
  }

  if (
    [FORMALIZATION_EVENTS.TOOL_CALL_STARTED, FORMALIZATION_EVENTS.TOOL_CALL_COMPLETE].includes(eventType) &&
    atomId
  ) {
    const atom = next.atoms[atomId] || emptyAtom(atomId)
    const toolCalls = upsertById(atom.tool_calls || [], event.payload, 'call_id')
    const isAxleTool = String(event.payload?.tool_name || '').startsWith('axle_')
    let nextStatus = atom.status
    if (!atom.label) {
      if (eventType === FORMALIZATION_EVENTS.TOOL_CALL_STARTED) {
        nextStatus = isAxleTool ? 'axle_running' : atom.status
      } else {
        nextStatus = 'llm_thinking'
      }
    }
    next = upsertAtom(next, atomId, {
      status: nextStatus,
      active_tool: eventType === FORMALIZATION_EVENTS.TOOL_CALL_STARTED ? event.payload?.tool_name : '',
      tool_calls: toolCalls,
    })
  }

  if (eventType === FORMALIZATION_EVENTS.ARTIFACT_RECORDED && atomId) {
    const atom = next.atoms[atomId] || emptyAtom(atomId)
    next = upsertAtom(next, atomId, {
      artifacts: [...(atom.artifacts || []), event.payload],
    })
  }

  if (eventType === FORMALIZATION_EVENTS.ARTIFACT_UPDATED && atomId) {
    const atom = next.atoms[atomId] || emptyAtom(atomId)
    next = upsertAtom(next, atomId, {
      artifacts: upsertById(atom.artifacts || [], event.payload, 'artifact_id'),
    })
  }

  if (eventType === FORMALIZATION_EVENTS.ATOM_VERDICT && atomId) {
    next = upsertAtom(next, atomId, {
      status: 'complete',
      label: event.payload?.label,
      rationale: event.payload?.rationale,
      confidence: event.payload?.confidence,
      used_assumptions: event.payload?.used_assumptions || [],
      error: event.payload?.error,
    })
  }

  if (eventType === FORMALIZATION_EVENTS.ATOM_ERROR && atomId) {
    next = upsertAtom(next, atomId, {
      status: 'error',
      error: event.payload?.error,
    })
  }

  if (eventType === FORMALIZATION_EVENTS.RUN_COMPLETE) {
    next.status = 'complete'
    next.summary = event.payload?.summary || next.summary
    next.connection = 'closed'
  }
  if (eventType === FORMALIZATION_EVENTS.RUN_ERROR) {
    next.status = 'error'
    next.error = event.payload?.error || 'Formalization run failed'
    next.connection = 'closed'
  }
  return withCounts(next)
}

function emptyAtom(atomId) {
  return {
    atom_id: atomId,
    status: 'queued',
    artifacts: [],
    tool_calls: [],
    thoughts: [],
  }
}

function hydrateAtom(atomId, atom = {}) {
  return {
    ...emptyAtom(atomId),
    ...atom,
    atom_id: atom.atom_id || atomId,
    artifacts: atom.artifacts || [],
    tool_calls: atom.tool_calls || [],
    thoughts: atom.thoughts || [],
  }
}

function upsertAtom(state, atomId, patch) {
  const atomOrder = state.atomOrder.includes(atomId) ? state.atomOrder : [...state.atomOrder, atomId]
  return {
    ...state,
    atomOrder,
    selectedAtomId: state.selectedAtomId || atomId,
    selected: state.selected || { kind: 'atom', id: atomId },
    atoms: {
      ...state.atoms,
      [atomId]: {
        ...(state.atoms[atomId] || emptyAtom(atomId)),
        ...patch,
      },
    },
  }
}

function appendThought(atom = {}, payload = {}) {
  const thoughts = [...(atom.thoughts || [])]
  const last = thoughts[thoughts.length - 1]
  const iteration = payload.iteration || 0
  if (last && last.iteration === iteration) {
    thoughts[thoughts.length - 1] = {
      ...last,
      content: `${last.content || ''}${payload.delta || ''}`,
    }
  } else {
    thoughts.push({
      iteration,
      model_name: payload.model_name,
      content: payload.delta || '',
    })
  }
  return { status: 'llm_thinking', thoughts: thoughts.slice(-80) }
}

function upsertById(items, item = {}, key) {
  const index = items.findIndex((existing) => existing[key] === item[key])
  if (index < 0) return [...items, item]
  const next = [...items]
  next[index] = { ...next[index], ...item }
  return next
}

function withCounts(state) {
  const atoms = Object.values(state.atoms || {})
  const completed = atoms.filter((atom) => atom.label || ['complete', 'error'].includes(atom.status)).length
  const running = atoms.filter((atom) => ['building_context', 'llm_thinking', 'axle_running'].includes(atom.status)).length
  const toolCalls = atoms.reduce((sum, atom) => sum + (atom.tool_calls?.length || 0), 0)
  const artifacts = atoms.reduce((sum, atom) => sum + (atom.artifacts?.length || 0), 0)
  return {
    ...state,
    counts: {
      atoms: atoms.length,
      completed_atoms: completed,
      running_atoms: running,
      queued_atoms: atoms.filter((atom) => atom.status === 'queued').length,
      tool_calls: toolCalls,
      artifacts,
      llm_thoughts: atoms.reduce((sum, atom) => sum + (atom.thoughts?.length || 0), 0),
    },
  }
}
