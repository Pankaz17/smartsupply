const STYLES = {
  HIGH: 'bg-red-100 text-red-800',
  MEDIUM: 'bg-yellow-100 text-yellow-800',
  LOW: 'bg-slate-100 text-slate-600',
}

export default function OperationalPriorityBadge({ level }) {
  if (!level) return <span className="text-slate-400">—</span>

  const normalized = String(level).toUpperCase()
  const label = normalized.charAt(0) + normalized.slice(1).toLowerCase()

  return (
    <span className={`rounded-full px-2 py-0.5 text-xs font-semibold ${STYLES[normalized] || STYLES.LOW}`}>
      {label}
    </span>
  )
}
