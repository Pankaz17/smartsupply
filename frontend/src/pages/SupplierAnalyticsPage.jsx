import { useEffect, useState } from 'react'
import { getSupplierAnalytics, performanceBadge } from '../api/analytics'
import PageHeader from '../components/layout/PageHeader'
import Alert from '../components/ui/Alert'
import DataTable from '../components/ui/DataTable'

export default function SupplierAnalyticsPage() {
  const [snapshots, setSnapshots] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  useEffect(() => {
    getSupplierAnalytics()
      .then(setSnapshots)
      .catch(() => setError('Failed to load supplier analytics.'))
      .finally(() => setLoading(false))
  }, [])

  const columns = [
    { key: 'supplier_name', label: 'Supplier' },
    {
      key: 'avg_promised_lead_time',
      label: 'Promised Lead Time',
      render: (r) => `${Number(r.avg_promised_lead_time).toFixed(1)} days`,
    },
    {
      key: 'avg_actual_lead_time',
      label: 'Actual Lead Time',
      render: (r) => `${Number(r.avg_actual_lead_time).toFixed(1)} days`,
    },
    {
      key: 'avg_delay_days',
      label: 'Average Delay',
      render: (r) => `${Number(r.avg_delay_days).toFixed(1)} days`,
    },
    {
      key: 'on_time_delivery_rate',
      label: 'On-Time Rate',
      render: (r) => `${Number(r.on_time_delivery_rate).toFixed(1)}%`,
    },
    { key: 'total_orders', label: 'Total Orders' },
    {
      key: 'rating',
      label: 'Rating',
      render: (r) => {
        const badge = performanceBadge(
          Number(r.on_time_delivery_rate),
          Number(r.avg_delay_days),
        )
        return (
          <span className={`rounded-full px-2 py-0.5 text-xs font-medium ${badge.className}`}>
            {badge.label}
          </span>
        )
      },
    },
  ]

  return (
    <div>
      <PageHeader
        title="Supplier Analytics"
        subtitle="Factual delivery performance metrics — no AI scores."
      />

      <Alert type="error" message={error} />

      {loading ? (
        <p className="text-sm text-slate-500">Loading supplier analytics...</p>
      ) : (
        <>
          <DataTable
            columns={columns}
            data={snapshots}
            emptyMessage="No supplier data yet. Receive purchase orders and run analytics."
          />
          {snapshots.length > 0 && (
            <div className="mt-6 space-y-4">
              {snapshots.map((snapshot) => (
                <div key={snapshot.id} className="rounded-xl border border-slate-200 bg-white p-4">
                  <h3 className="text-sm font-semibold text-slate-900">
                    Supplier Insights — {snapshot.supplier_name}
                  </h3>
                  <ul className="mt-2 space-y-1 text-sm text-slate-700">
                    {(snapshot.supplier_insights || []).map((insight) => (
                      <li key={insight} className="flex items-start gap-2">
                        <span className="mt-1 h-1.5 w-1.5 shrink-0 rounded-full bg-brand-500" />
                        <span>{insight}</span>
                      </li>
                    ))}
                  </ul>
                </div>
              ))}
            </div>
          )}
        </>
      )}
    </div>
  )
}
