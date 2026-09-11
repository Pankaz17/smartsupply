import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { getReportsOverview } from '../../api/reports'
import PageHeader from '../../components/layout/PageHeader'
import Alert from '../../components/ui/Alert'

const REPORT_LINKS = [
  { to: '/reports/inventory', label: 'Inventory Report', key: 'inventory' },
  { to: '/reports/sales', label: 'Sales Report', key: 'sales' },
  { to: '/reports/dead-stock', label: 'Dead Stock Report', key: 'dead-stock' },
  { to: '/reports/suppliers', label: 'Supplier Report', key: 'suppliers' },
  { to: '/reports/recommendations', label: 'Recommendation Report', key: 'recommendations' },
  { to: '/reports/demand-forecast', label: 'Demand Forecast Report', key: 'demand-forecast' },
  { to: '/reports/profit-advisor', label: 'Profit Advisor Report', key: 'profit-advisor' },
]

export default function ReportsDashboardPage() {
  const [overview, setOverview] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  useEffect(() => {
    getReportsOverview()
      .then(setOverview)
      .catch(() => setError('Failed to load reports overview.'))
      .finally(() => setLoading(false))
  }, [])

  const formatMoney = (value) =>
    new Intl.NumberFormat('en-US', { style: 'currency', currency: 'USD' }).format(Number(value || 0))

  const cards = [
    {
      label: 'Total Inventory Value',
      value: formatMoney(overview?.total_inventory_value),
      link: '/reports/inventory',
    },
    {
      label: 'Revenue (30 Days)',
      value: formatMoney(overview?.revenue_30_days),
      link: '/reports/sales',
    },
    {
      label: 'Capital At Risk',
      value: formatMoney(overview?.capital_at_risk),
      link: '/reports/dead-stock',
    },
    {
      label: 'Supplier On-Time Rate',
      value: `${overview?.supplier_on_time_rate ?? 0}%`,
      link: '/reports/suppliers',
    },
    {
      label: 'Pending Recommendations',
      value: overview?.pending_recommendations ?? 0,
      link: '/reports/recommendations',
    },
  ]

  return (
    <div>
      <PageHeader
        title="Reports"
        subtitle="Business intelligence summaries and exportable reports."
      />

      <Alert type="error" message={error} />

      {loading ? (
        <p className="text-sm text-slate-500">Loading reports...</p>
      ) : (
        <>
          <div className="mb-8 grid gap-4 md:grid-cols-2 lg:grid-cols-3">
            {cards.map((card) => (
              <Link
                key={card.label}
                to={card.link}
                className="block rounded-xl border border-slate-200 bg-white p-5 shadow-sm transition-opacity hover:opacity-90"
              >
                <div className="text-sm font-medium text-slate-500">{card.label}</div>
                <div className="mt-2 text-2xl font-bold text-slate-900">{card.value}</div>
              </Link>
            ))}
          </div>

          <div className="rounded-xl border border-slate-200 bg-white p-6">
            <h2 className="mb-4 text-lg font-semibold text-slate-900">Available Reports</h2>
            <ul className="grid gap-2 sm:grid-cols-2">
              {REPORT_LINKS.map((item) => (
                <li key={item.key}>
                  <Link
                    to={item.to}
                    className="block rounded-lg px-3 py-2 text-sm font-medium text-brand-600 hover:bg-brand-50"
                  >
                    {item.label}
                  </Link>
                </li>
              ))}
            </ul>
          </div>
        </>
      )}
    </div>
  )
}
