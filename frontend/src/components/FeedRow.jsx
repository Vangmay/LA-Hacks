// FeedRow.jsx — Activity feed row, mono font
export default function FeedRow({ event }) {
  return (
    <div style={{
      fontFamily: 'JetBrains Mono, monospace',
      fontSize: 10,
      color: '#A1A1AA',
      padding: '4px 0 4px 2px',
      borderLeft: `2px solid ${event.level === 'error' ? '#EF4444' : event.level === 'warn' ? '#F59E42' : '#6366F1'}`,
      marginBottom: 2,
      background: event.level === 'error' ? 'rgba(239,68,68,0.07)' : event.level === 'warn' ? 'rgba(245,158,66,0.07)' : 'none',
    }}>
      <span style={{marginRight:6}}>
        {event.level === 'error' ? '✗' : event.level === 'warn' ? '!' : '⟳'}
      </span>
      {event.message}
    </div>
  )
}
