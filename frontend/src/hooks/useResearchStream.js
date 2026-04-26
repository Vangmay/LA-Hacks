import { useEffect } from 'react'
import { api } from '../api/client'

export function useResearchStream(runId, dispatch, onCatchUp) {
  useEffect(() => {
    if (!runId) return
    let eventSource = null
    let closed = false
    let receivedSnapshot = false

    try {
      eventSource = api.research.stream(runId)
    } catch (err) {
      dispatch({ type: 'CONNECTION_ERROR', error: err.message || 'Failed to open stream' })
      return
    }

    const handleEvent = (e) => {
      try {
        const event = JSON.parse(e.data)
        if (event.type === 'run.snapshot') receivedSnapshot = true
        dispatch({ type: 'EVENT', event })
        onCatchUp?.(event)
        if (
          event.type === 'run.finalized' ||
          event.type === 'run.error' ||
          (event.type === 'run.snapshot' && event.payload?.live === false)
        ) {
          closed = true
          eventSource.close()
        }
      } catch (err) {
        dispatch({ type: 'CONNECTION_ERROR', error: 'Research stream sent invalid JSON' })
      }
    }

    eventSource.addEventListener('research_update', handleEvent)
    eventSource.onmessage = handleEvent
    eventSource.onerror = () => {
      if (!closed) {
        dispatch({ type: 'CONNECTION_STATE', connection: receivedSnapshot ? 'reconnecting' : 'disconnected' })
        onCatchUp?.()
      }
    }

    return () => {
      closed = true
      if (eventSource) eventSource.close()
    }
  }, [runId, dispatch, onCatchUp])
}
