const COLORS = {
  idle: 'bg-white/5 text-white/60 border-white/10',
  running: 'bg-cyan-500/15 text-cyan-100 border-cyan-300/30',
  pending: 'bg-slate-500/15 text-slate-200 border-slate-400/30',
  success: 'bg-emerald-500/15 text-emerald-100 border-emerald-400/30',
  queued: 'bg-slate-500/15 text-slate-200 border-slate-400/30',
  building_context: 'bg-blue-500/15 text-blue-200 border-blue-400/30',
  llm_thinking: 'bg-indigo-500/15 text-indigo-200 border-indigo-400/30',
  axle_running: 'bg-cyan-500/15 text-cyan-100 border-cyan-300/30',
  complete: 'bg-emerald-500/15 text-emerald-100 border-emerald-400/30',
  error: 'bg-red-500/15 text-red-100 border-red-400/30',
  fully_verified: 'bg-emerald-500/15 text-emerald-100 border-emerald-400/30',
  conditionally_verified: 'bg-amber-500/15 text-amber-100 border-amber-400/30',
  formalized_only: 'bg-blue-500/15 text-blue-100 border-blue-400/30',
  disproved: 'bg-red-500/15 text-red-100 border-red-400/30',
  formalization_failed: 'bg-red-500/15 text-red-100 border-red-400/30',
  not_a_theorem: 'bg-slate-500/15 text-slate-200 border-slate-400/30',
  gave_up: 'bg-zinc-500/15 text-zinc-100 border-zinc-400/30',
}

export default function StatusBadge({ value }) {
  const label = (value || 'idle').replace(/_/g, ' ')
  const color = COLORS[value] || 'bg-white/5 text-white/70 border-white/10'
  return (
    <span className={`inline-flex items-center rounded border px-2 py-0.5 text-[10px] uppercase tracking-wide ${color}`}>
      {label}
    </span>
  )
}
