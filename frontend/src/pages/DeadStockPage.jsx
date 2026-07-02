import { useCallback, useEffect, useState } from 'react'
import { getDeadStock } from '../api/analytics'
import PageHeader from '../components/layout/PageHeader'
import Alert from '../components/ui/Alert'
import DataTable from '../components/ui/DataTable'
import DeadStockSuggestionBadges from '../components/analytics/DeadStockSuggestionBadges'
import Select from '../components/ui/Select'

const SEVERITY_OPTIONS = [
  { value: '', label: 'All severities' },
  { value: 'warning', label: 'Warning' },
  { value: 'critical', label: 'Critical' },
]

const SEVERITY_STYLES = {
  warning: 'bg-amber-100 text-amber-700',
  critical: 'bg-red-100 text-red-700',
}

export default function DeadStockPage() {
  const [items, setItems] = useState([])
  const [severityFilter, setSeverityFilter] = useState('')
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  const load = useCallback(() => {
    setLoading(true)
    const params = {}
    if (severityFilter) params.severity = severityFilter
    getDeadStock(params)
      .then(setItems)
      .catch(() => setError('Failed to load dead stock data.'))
      .finally(() => setLoading(false))
  }, [severityFilter])

  useEffect(() => { load() }, [load])

  const formatMoney = (value) =>
    new Intl.NumberFormat('en-US', { style: 'currency', currency: 'USD' }).format(Number(value))

  const columns = [
    { key: 'product_name', label: 'Product' },
    { key: 'category_name', label: 'Category' },
    { key: 'days_without_sale', label: 'Days Without Sale' },
    { key: 'current_stock', label: 'Current Stock' },
    {
      key: 'inventory_value',
      label: 'Inventory Value',
      render: (r) => formatMoney(r.inventory_value),
    },
    {
      key: 'severity',
      label: 'Severity',
      render: (r) => (
        <span className={`rounded-full px-2 py-0.5 text-xs font-medium capitalize ${SEVERITY_STYLES[r.severity]}`}>
          {r.severity}
        </span>
      ),
    },
    {
      key: 'suggestions',
      label: 'Suggested Action',
      render: (r) => <DeadStockSuggestionBadges suggestions={r.suggestions} />,
    },
  ]

  return (
    <div>
      <PageHeader
        title="Dead Stock Analysis"
        subtitle="Products with stock on hand but no recent sales."
      />

      <Alert type="error" message={error} />

      <div className="mb-4 max-w-xs">
        <Select
          id="severity-filter"
          label="Filter by severity"
          options={SEVERITY_OPTIONS}
          value={severityFilter}
          onChange={(e) => setSeverityFilter(e.target.value)}
        />
      </div>

      {loading ? (
        <p className="text-sm text-slate-500">Loading dead stock...</p>
      ) : (
        <DataTable
          columns={columns}
          data={items}
          emptyMessage="Great! No products have become dead stock."
        />
      )}
    </div>
  )
}
