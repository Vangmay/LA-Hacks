// Chip.jsx — Small badge for status/type, mono font
export default function Chip({ children, color, bg, border }) {
  return (
    <span style={{
      fontFamily: 'JetBrains Mono, monospace',
      fontSize: 9,
      fontWeight: 700,
      letterSpacing: '0.06em',
      textTransform: 'uppercase',
      color: color || '#6B7280',
      background: bg || 'rgba(255,255,255,0.05)',
      border: `1px solid ${border || 'rgba(255,255,255,0.08)'}`,
      padding: '1px 6px',
      borderRadius: 3,
      display: 'inline-block',
    }}>
      {children}
    </span>
  )
}
