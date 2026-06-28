import {
  CartesianGrid,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts'

export default function SimpleLineChart({ data, xKey, yKey, yLabel, color = '#2563eb' }) {
  if (!data?.length) {
    return (
      <div className="flex h-64 min-h-[16rem] items-center justify-center rounded-xl border border-slate-200 bg-white text-sm text-slate-500">
        No chart data available.
      </div>
    )
  }

  return (
    <div className="h-64 min-h-[16rem] w-full rounded-xl border border-slate-200 bg-white p-4">
      <ResponsiveContainer width="100%" height="100%" minWidth={0} minHeight={256}>
        <LineChart data={data} margin={{ top: 8, right: 8, left: 0, bottom: 0 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
          <XAxis dataKey={xKey} tick={{ fontSize: 12 }} />
          <YAxis tick={{ fontSize: 12 }} />
          <Tooltip formatter={(val) => [Number(val).toLocaleString(), yLabel]} />
          <Line type="monotone" dataKey={yKey} stroke={color} strokeWidth={2} dot={{ r: 3 }} />
        </LineChart>
      </ResponsiveContainer>
    </div>
  )
}
