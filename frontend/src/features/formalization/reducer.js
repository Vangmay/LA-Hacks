import { FORMALIZATION_EVENTS } from './types'

export const initialFormalizationState = {
  runId: null,
  status: 'idle',
  selectedAtomId: null,
  atomOrder: [],
  atoms: {},
  events: [],
  summary: {},
  error: '',
}

export function formalizationReducer(state, action) {
  switch (action.type) {
    case 'START_RESPONSE':
      return {
        ...initialFormalizationState,
        runId: action.payload.run_id,
        status: action.payload.status || 'queued',
        atomOrder: action.payload.selected_atom_ids || [],
        selectedAtomId: action.payload.selected_atom_ids?.[0] || state.selectedAtomId,
      }
    case 'RUN_SNAPSHOT':
      return snapshotToState(state, action.payload)
    case 'SELECT_ATOM':
      return { ...state, selectedAtomId: action.atomId }
    case 'ERROR':
      return { ...state, error: action.error || 'Formalization failed' }
    case 'EVENT':
      return applyEvent(state, action.event)
    default:
      return state
  }
}

function snapshotToState(state, run) {
  const atoms = {}
  const atomOrder = run.selected_atom_ids || []
  for (const atomId of atomOrder) {
    atoms[atomId] = {
      atom_id: atomId,
      ...(run.atom_formalizations?.[atomId] || {}),
    }
  }
  return {
    ...state,
    runId: run.run_id,
    status: run.status,
    atomOrder,
    atoms,
    summary: run.summary || {},
    error: run.error || state.error,
    selectedAtomId: state.selectedAtomId || atomOrder[0] || null,
  }
}

function applyEvent(state, event) {
  const eventType = event.event_type
  const atomId = event.atom_id || event.payload?.atom_id
  const events = [...state.events, event].slice(-300)
  let next = { ...state, events }

  if (eventType === FORMALIZATION_EVENTS.RUN_STARTED) {
    next.status = 'running'
  }

  if (eventType === FORMALIZATION_EVENTS.ATOM_QUEUED && atomId) {
    next = upsertAtom(next, atomId, {
      atom_id: atomId,
      status: 'queued',
      text: event.payload?.text,
      atom_type: event.payload?.atom_type,
      importance: event.payload?.importance,
    })
  }

  if (eventType === FORMALIZATION_EVENTS.ATOM_CONTEXT_BUILT && atomId) {
    next = upsertAtom(next, atomId, {
      status: 'building_context',
      context: event.payload,
    })
  }

  if (
    [FORMALIZATION_EVENTS.TOOL_CALL_STARTED, FORMALIZATION_EVENTS.TOOL_CALL_COMPLETE].includes(eventType) &&
    atomId
  ) {
    const atom = next.atoms[atomId] || { atom_id: atomId }
    const existing = atom.tool_calls || []
    const call = event.payload
    const index = existing.findIndex(c => c.call_id === call.call_id)
    const toolCalls = [...existing]
    if (index >= 0) toolCalls[index] = { ...toolCalls[index], ...call }
    else toolCalls.push(call)
    next = upsertAtom(next, atomId, {
      status: eventType === FORMALIZATION_EVENTS.TOOL_CALL_STARTED ? 'axle_running' : atom.status,
      tool_calls: toolCalls,
    })
  }

  if (eventType === FORMALIZATION_EVENTS.ARTIFACT_RECORDED && atomId) {
    const atom = next.atoms[atomId] || { atom_id: atomId }
    next = upsertAtom(next, atomId, {
      artifacts: [...(atom.artifacts || []), event.payload],
    })
  }

  if (eventType === FORMALIZATION_EVENTS.ATOM_VERDICT && atomId) {
    next = upsertAtom(next, atomId, {
      status: 'complete',
      label: event.payload?.label,
      rationale: event.payload?.rationale,
      confidence: event.payload?.confidence,
      used_assumptions: event.payload?.used_assumptions || [],
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
  }
  if (eventType === FORMALIZATION_EVENTS.RUN_ERROR) {
    next.status = 'error'
    next.error = event.payload?.error || 'Formalization run failed'
  }
  return next
}

function upsertAtom(state, atomId, patch) {
  const atomOrder = state.atomOrder.includes(atomId) ? state.atomOrder : [...state.atomOrder, atomId]
  return {
    ...state,
    atomOrder,
    selectedAtomId: state.selectedAtomId || atomId,
    atoms: {
      ...state.atoms,
      [atomId]: {
        ...(state.atoms[atomId] || { atom_id: atomId }),
        ...patch,
      },
    },
  }
}
