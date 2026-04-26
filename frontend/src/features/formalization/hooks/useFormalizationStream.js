import { useEffect } from 'react'
import { formalizationApi } from '../api'
import { TERMINAL_EVENTS } from '../types'

export function useFormalizationStream(runId, dispatch) {
  useEffect(() => {
    if (!runId) return undefined
    const eventSource = formalizationApi.stream(runId)

    eventSource.addEventListener('formalization_update', (event) => {
      try {
        const data = JSON.parse(event.data)
        dispatch({ type: 'EVENT', event: data })
        if (TERMINAL_EVENTS.has(data.event_type)) {
          eventSource.close()
        }
      } catch (err) {
        dispatch({ type: 'ERROR', error: err.message || 'Failed to parse formalization event' })
      }
    })

    eventSource.onerror = () => {
      if (eventSource.readyState !== EventSource.CLOSED) {
        dispatch({ type: 'ERROR', error: 'Lost formalization stream connection' })
        eventSource.close()
      }
    }

    return () => eventSource.close()
  }, [runId, dispatch])
}
