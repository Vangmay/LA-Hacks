export default function LeanCodeBlock({ code }) {
  if (!code) {
    return <div className="text-xs text-white/45">No Lean artifact selected.</div>
  }
  return (
    <pre className="max-h-72 overflow-auto rounded border border-white/10 bg-[#090B10] p-3 text-[11px] leading-relaxed text-slate-100">
      <code>{code}</code>
    </pre>
  )
}
