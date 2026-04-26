const TOOL_STYLES = {
  axle_check: 'bg-sky-500/15 text-sky-100 border-sky-400/30',
  axle_verify_proof: 'bg-emerald-500/15 text-emerald-100 border-emerald-400/30',
  axle_repair_proofs: 'bg-orange-500/15 text-orange-100 border-orange-400/30',
  axle_sorry2lemma: 'bg-violet-500/15 text-violet-100 border-violet-400/30',
  axle_have2lemma: 'bg-fuchsia-500/15 text-fuchsia-100 border-fuchsia-400/30',
  axle_disprove: 'bg-red-500/15 text-red-100 border-red-400/30',
  record_artifact: 'bg-blue-500/15 text-blue-100 border-blue-400/30',
  emit_verdict: 'bg-emerald-500/15 text-emerald-100 border-emerald-400/30',
  give_up: 'bg-zinc-500/15 text-zinc-100 border-zinc-400/30',
}

export default function AxleToolBadge({ tool }) {
  const style = TOOL_STYLES[tool] || 'bg-white/5 text-white/70 border-white/10'
  return (
    <span className={`inline-flex rounded border px-1.5 py-0.5 font-mono text-[10px] ${style}`}>
      {(tool || 'tool').replace(/^axle_/, '')}
    </span>
  )
}
