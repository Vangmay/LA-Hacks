import StatusBadge from './StatusBadge'

export default function AtomList({ atomOrder, atoms, selectedAtomId, onSelect }) {
  if (!atomOrder.length) {
    return <div className="text-xs text-white/45">No formalization run yet.</div>
  }
  return (
    <div className="max-h-36 overflow-auto rounded border border-white/10">
      {atomOrder.map(atomId => {
        const atom = atoms[atomId] || { atom_id: atomId }
        const active = atomId === selectedAtomId
        return (
          <button
            key={atomId}
            onClick={() => onSelect(atomId)}
            className={`block w-full border-b border-white/5 px-3 py-2 text-left last:border-b-0 hover:bg-white/5 ${active ? 'bg-white/10' : ''}`}
          >
            <div className="flex items-center gap-2">
              <span className="truncate font-mono text-[11px] text-white/70">{atomId}</span>
              <span className="ml-auto"><StatusBadge value={atom.label || atom.status} /></span>
            </div>
            {atom.text && <div className="mt-1 line-clamp-2 text-xs text-white/60">{atom.text}</div>}
          </button>
        )
      })}
    </div>
  )
}
