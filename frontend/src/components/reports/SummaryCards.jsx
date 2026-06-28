export default function SummaryCards({ items }) {
  return (
    <div className="mb-6 grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
      {items.map((item) => (
        <div
          key={item.label}
          className="rounded-xl border border-slate-200 bg-white p-4 shadow-sm"
        >
          <div className="text-sm font-medium text-slate-500">{item.label}</div>
          <div className="mt-1 text-2xl font-bold text-slate-900">{item.value}</div>
        </div>
      ))}
    </div>
  )
}
