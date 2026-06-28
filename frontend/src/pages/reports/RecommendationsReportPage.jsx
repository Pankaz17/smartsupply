import { useCallback, useEffect, useState } from 'react'
import { getRecommendationsReport } from '../../api/reports'
import DateRangeFilter, { DEFAULT_DATE_RANGE } from '../../components/reports/DateRangeFilter'
import ExportButtons from '../../components/reports/ExportButtons'
import SummaryCards from '../../components/reports/SummaryCards'
import PageHeader from '../../components/layout/PageHeader'
import Alert from '../../components/ui/Alert'
import DataTable from '../../components/ui/DataTable'
import PriorityBadge from '../../components/ui/PriorityBadge'

const STATUS_STYLES = {
  pending: 'bg-amber-100 text-amber-700',
  approved: 'bg-green-100 text-green-700',
  dismissed: 'bg-slate-100 text-slate-600',
}

export default function RecommendationsReportPage() {
  const [dateRange, setDateRange] = useState(DEFAULT_DATE_RANGE)
  const [report, setReport] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  const load = useCallback(() => {
    if (dateRange.mode === 'custom' && (!dateRange.startDate || !dateRange.endDate)) return
    setLoading(true)
    getRecommendationsReport(dateRange)
      .then(setReport)
      .catch(() => setError('Failed to load recommendations report.'))
      .finally(() => setLoading(false))
  }, [dateRange])

  useEffect(() => { load() }, [load])

  const formatMoney = (value) =>
    new Intl.NumberFormat('en-US', { style: 'currency', currency: 'USD' }).format(Number(value || 0))

  const columns = [
    { key: 'product', label: 'Product' },
    { key: 'recommended_quantity', label: 'Recommended Quantity' },
    { key: 'unit_profit', label: 'Unit Profit', render: (r) => formatMoney(r.unit_profit) },
    { key: 'priority_score', label: 'Priority Score', render: (r) => Number(r.priority_score || 0).toFixed(2) },
    {
      key: 'expected_restock_profit',
      label: 'Expected Restock Profit',
      render: (r) => formatMoney(r.expected_restock_profit),
    },
    {
      key: 'priority_level',
      label: 'Priority Level',
      render: (r) => <PriorityBadge level={r.priority_level} />,
    },
    { key: 'generated_date', label: 'Generated Date' },
    {
      key: 'status',
      label: 'Status',
      render: (r) => (
        <span className={`rounded-full px-2 py-0.5 text-xs font-medium capitalize ${STATUS_STYLES[r.status] || ''}`}>
          {r.status}
        </span>
      ),
    },
    { key: 'approved_date', label: 'Approved Date', render: (r) => r.approved_date || '—' },
  ]

  return (
    <div>
      <PageHeader
        title="Recommendation History Report"
        subtitle="Reorder recommendations with profit-based priority metrics."
        action={<ExportButtons reportKey="recommendations" dateRange={dateRange} />}
      />

      <Alert type="error" message={error} />
      <DateRangeFilter value={dateRange} onChange={setDateRange} />

      {loading ? (
        <p className="text-sm text-slate-500">Loading report...</p>
      ) : (
        <>
          <SummaryCards
            items={[
              { label: 'Total Recommendations', value: report?.summary?.total_recommendations ?? 0 },
              { label: 'Approved', value: report?.summary?.approved ?? 0 },
              { label: 'Dismissed', value: report?.summary?.dismissed ?? 0 },
              { label: 'Pending', value: report?.summary?.pending ?? 0 },
            ]}
          />

          <DataTable
            columns={columns}
            data={report?.rows ?? []}
            emptyMessage="No recommendations in this period."
            rowKey={(row) => `${row.sku}-${row.generated_date}-${row.status}`}
          />
        </>
      )}
    </div>
  )
}
