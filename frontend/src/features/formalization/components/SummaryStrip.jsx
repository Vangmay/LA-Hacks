import StatusBadge from './StatusBadge'

const ORDER = [
  'fully_verified',
  'conditionally_verified',
  'formalized_only',
  'disproved',
  'formalization_failed',
  'not_a_theorem',
  'gave_up',
]

export default function SummaryStrip({ summary = {} }) {
  return (
    <div className="flex flex-wrap gap-1.5">
      {ORDER.map(label => (
        <span key={label} className="inline-flex items-center gap-1">
          <StatusBadge value={label} />
          <span className="font-mono text-[10px] text-white/55">{summary[label] || 0}</span>
        </span>
      ))}
    </div>
  )
}
