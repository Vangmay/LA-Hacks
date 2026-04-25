import { useEffect, useRef } from 'react'

const EVENT_ICON = {
  node_classified: '🔍',
  scaffold_generated: '⚙',
  poc_ready: '📦',
  results_uploaded: '📊',
  analysis_complete: '✓',
  error: '✗',
}

export default function ActivityFeed({ activities = [] }) {
  const bottomRef = useRef(null)

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [activities])

  return (
    <div className="h-28 border-t border-[#2a2e3f] overflow-y-auto" style={{ background: '#12151f' }}>
      <div className="px-4 py-2">
        <div className="text-[10px] text-[#4b5563] tracking-widest mb-1">ACTIVITY</div>
        {activities.length === 0 && (
          <div className="text-[#374151] text-xs italic">Waiting for events...</div>
        )}
        {activities.map((act, i) => (
          <div key={i} className="flex items-start gap-2 text-xs py-0.5">
            <span className="text-base leading-none flex-shrink-0" style={{ lineHeight: '1.3' }}>
              {EVENT_ICON[act.type] || '·'}
            </span>
            <span style={{ color: act.color || '#94a3b8' }} className="leading-snug">{act.message}</span>
            {act.time && (
              <span className="text-[#374151] ml-auto flex-shrink-0">{act.time}</span>
            )}
          </div>
        ))}
        <div ref={bottomRef} />
      </div>
    </div>
  )
}
