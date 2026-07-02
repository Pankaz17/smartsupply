const SUGGESTION_STYLES = {
  'Run a Discount Campaign': 'bg-orange-100 text-orange-800',
  'Bundle with a Popular Product': 'bg-green-100 text-green-800',
  'Stop Reordering': 'bg-red-100 text-red-800',
  'Bundle Remaining Stock': 'bg-green-100 text-green-800',
  'Heavy Discount Campaign': 'bg-orange-100 text-orange-800',
}

export default function DeadStockSuggestionBadges({ suggestions }) {
  if (!suggestions?.length) {
    return <span className="text-slate-400">—</span>
  }

  return (
    <div className="flex max-w-md flex-wrap gap-1.5">
      {suggestions.map((suggestion) => (
        <span
          key={suggestion}
          className={`rounded-full px-2 py-0.5 text-xs font-medium ${SUGGESTION_STYLES[suggestion] || 'bg-slate-100 text-slate-600'}`}
        >
          {suggestion}
        </span>
      ))}
    </div>
  )
}
