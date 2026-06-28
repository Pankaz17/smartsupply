const STYLES = {
  HIGH: 'bg-green-100 text-green-800',
  MEDIUM: 'bg-amber-100 text-amber-800',
  LOW: 'bg-slate-100 text-slate-600',
}

export default function PriorityBadge({ level }) {
  if (!level) return '—'
  return (
    <span className={`rounded-full px-2 py-0.5 text-xs font-semibold ${STYLES[level] || STYLES.LOW}`}>
      {level}
    </span>
  )
}

export { STYLES as PRIORITY_STYLES }
