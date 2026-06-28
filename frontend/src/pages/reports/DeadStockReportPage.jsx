import { useCallback, useEffect, useState } from 'react'
import { getDeadStockReport } from '../../api/reports'
import DateRangeFilter, { DEFAULT_DATE_RANGE } from '../../components/reports/DateRangeFilter'
import ExportButtons from '../../components/reports/ExportButtons'
import SummaryCards from '../../components/reports/SummaryCards'
import PageHeader from '../../components/layout/PageHeader'
import Alert from '../../components/ui/Alert'
import DataTable from '../../components/ui/DataTable'

const SEVERITY_STYLES = {
  warning: 'bg-amber-100 text-amber-700',
  critical: 'bg-red-100 text-red-700',
}

export default function DeadStockReportPage() {
  const [dateRange, setDateRange] = useState(DEFAULT_DATE_RANGE)
  const [report, setReport] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  const load = useCallback(() => {
    if (dateRange.mode === 'custom' && (!dateRange.startDate || !dateRange.endDate)) return
    setLoading(true)
    getDeadStockReport(dateRange)
      .then(setReport)
      .catch(() => setError('Failed to load dead stock report.'))
      .finally(() => setLoading(false))
  }, [dateRange])

  useEffect(() => { load() }, [load])

  const formatMoney = (value) =>
    new Intl.NumberFormat('en-US', { style: 'currency', currency: 'USD' }).format(Number(value || 0))

  const columns = [
    { key: 'product', label: 'Product' },
    { key: 'days_without_sale', label: 'Days Without Sale' },
    { key: 'current_stock', label: 'Current Stock' },
    { key: 'inventory_value', label: 'Inventory Value', render: (r) => formatMoney(r.inventory_value) },
    {
      key: 'severity',
      label: 'Severity',
      render: (r) => (
        <span className={`rounded-full px-2 py-0.5 text-xs font-medium capitalize ${SEVERITY_STYLES[r.severity] || ''}`}>
          {r.severity}
        </span>
      ),
    },
  ]

  return (
    <div>
      <PageHeader
        title="Dead Stock Report"
        subtitle="Slow-moving inventory and capital at risk."
        action={<ExportButtons reportKey="dead-stock" dateRange={dateRange} />}
      />

      <Alert type="error" message={error} />
      <DateRangeFilter value={dateRange} onChange={setDateRange} />

      {loading ? (
        <p className="text-sm text-slate-500">Loading report...</p>
      ) : (
        <>
          <SummaryCards
            items={[
              { label: 'Dead Stock Count', value: report?.summary?.dead_stock_count ?? 0 },
              { label: 'Total Capital At Risk', value: formatMoney(report?.summary?.total_capital_at_risk) },
            ]}
          />

          <DataTable
            columns={columns}
            data={report?.rows ?? []}
            emptyMessage="No dead stock in this period."
            rowKey={(row) => row.sku}
          />
        </>
      )}
    </div>
  )
}
