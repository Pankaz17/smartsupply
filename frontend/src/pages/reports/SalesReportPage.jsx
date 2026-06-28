import { useCallback, useEffect, useState } from 'react'
import { getSalesReport } from '../../api/reports'
import DateRangeFilter, { DEFAULT_DATE_RANGE } from '../../components/reports/DateRangeFilter'
import ExportButtons from '../../components/reports/ExportButtons'
import SimpleLineChart from '../../components/reports/SimpleLineChart'
import SummaryCards from '../../components/reports/SummaryCards'
import PageHeader from '../../components/layout/PageHeader'
import Alert from '../../components/ui/Alert'
import DataTable from '../../components/ui/DataTable'

export default function SalesReportPage() {
  const [dateRange, setDateRange] = useState(DEFAULT_DATE_RANGE)
  const [report, setReport] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  const load = useCallback(() => {
    if (dateRange.mode === 'custom' && (!dateRange.startDate || !dateRange.endDate)) return
    setLoading(true)
    getSalesReport(dateRange)
      .then(setReport)
      .catch(() => setError('Failed to load sales report.'))
      .finally(() => setLoading(false))
  }, [dateRange])

  useEffect(() => { load() }, [load])

  const formatMoney = (value) =>
    new Intl.NumberFormat('en-US', { style: 'currency', currency: 'USD' }).format(Number(value || 0))

  const columns = [
    { key: 'product', label: 'Product' },
    { key: 'units_sold', label: 'Units Sold' },
    { key: 'revenue', label: 'Revenue', render: (r) => formatMoney(r.revenue) },
  ]

  return (
    <div>
      <PageHeader
        title="Sales Performance Report"
        subtitle="Revenue and units sold over the selected period."
        action={<ExportButtons reportKey="sales" dateRange={dateRange} />}
      />

      <Alert type="error" message={error} />
      <DateRangeFilter value={dateRange} onChange={setDateRange} />

      {loading ? (
        <p className="text-sm text-slate-500">Loading report...</p>
      ) : (
        <>
          <SummaryCards
            items={[
              { label: 'Revenue', value: formatMoney(report?.summary?.revenue) },
              { label: 'Units Sold', value: report?.summary?.units_sold ?? 0 },
              { label: 'Transactions', value: report?.summary?.transactions ?? 0 },
              { label: 'Average Sale Value', value: formatMoney(report?.summary?.average_sale_value) },
            ]}
          />

          <div className="mb-8">
            <h2 className="mb-3 text-lg font-semibold text-slate-900">Revenue Trend</h2>
            <SimpleLineChart
              data={report?.chart?.revenue_trend}
              xKey="date"
              yKey="revenue"
              yLabel="Revenue"
            />
          </div>

          <DataTable
            columns={columns}
            data={report?.rows ?? []}
            emptyMessage="No sales in this period."
            rowKey={(row) => `${row.sku}-${row.product}`}
          />
        </>
      )}
    </div>
  )
}
