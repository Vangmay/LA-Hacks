import AxleToolBadge from './AxleToolBadge'

export default function ToolCallRow({ event, onClick }) {
  const payload = event.payload || {}
  const status = payload.status || 'pending'
  const okay = payload.result_summary?.okay
  const errorCount = payload.result_summary?.lean_errors
  return (
    <button
      onClick={onClick}
      className="block w-full rounded border border-white/5 bg-black/15 px-2 py-2 text-left hover:bg-white/5"
    >
      <div className="flex items-center gap-2">
        <AxleToolBadge tool={payload.tool_name} />
        <span className="font-mono text-[10px] uppercase text-white/50">{status}</span>
        {typeof okay === 'boolean' && (
          <span className={`ml-auto text-[10px] ${okay ? 'text-emerald-200' : 'text-red-200'}`}>
            {okay ? 'ok' : 'failed'}
          </span>
        )}
      </div>
      {Number.isFinite(errorCount) && errorCount > 0 && (
        <div className="mt-1 truncate text-[11px] text-red-200/80">
          {errorCount} Lean error{errorCount === 1 ? '' : 's'}
        </div>
      )}
      {payload.error && (
        <div className="mt-1 line-clamp-2 text-[11px] text-red-200/80">{payload.error}</div>
      )}
    </button>
  )
}
