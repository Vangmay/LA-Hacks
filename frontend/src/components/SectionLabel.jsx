// SectionLabel.jsx — Uppercase section label, mono font
export default function SectionLabel({ children }) {
  return (
    <div style={{
      fontFamily: 'JetBrains Mono, monospace',
      fontSize: 9,
      color: '#6B7280',
      fontWeight: 700,
      letterSpacing: '0.1em',
      textTransform: 'uppercase',
      marginBottom: 8,
    }}>
      {children}
    </div>
  )
}
