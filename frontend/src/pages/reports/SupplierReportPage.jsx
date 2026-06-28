import { useCallback, useEffect, useState } from 'react'
import { getSupplierReport } from '../../api/reports'
import DateRangeFilter, { DEFAULT_DATE_RANGE } from '../../components/reports/DateRangeFilter'
import ExportButtons from '../../components/reports/ExportButtons'
import SimpleBarChart from '../../components/reports/SimpleBarChart'
import SummaryCards from '../../components/reports/SummaryCards'
import PageHeader from '../../components/layout/PageHeader'
import Alert from '../../components/ui/Alert'
import DataTable from '../../components/ui/DataTable'

export default function SupplierReportPage() {
  const [dateRange, setDateRange] = useState(DEFAULT_DATE_RANGE)
  const [report, setReport] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  const load = useCallback(() => {
    if (dateRange.mode === 'custom' && (!dateRange.startDate || !dateRange.endDate)) return
    setLoading(true)
    getSupplierReport(dateRange)
      .then(setReport)
      .catch(() => setError('Failed to load supplier report.'))
      .finally(() => setLoading(false))
  }, [dateRange])

  useEffect(() => { load() }, [load])

  const columns = [
    { key: 'supplier', label: 'Supplier' },
    { key: 'promised_lead_time', label: 'Promised Lead Time' },
    { key: 'actual_lead_time', label: 'Actual Lead Time' },
    { key: 'average_delay', label: 'Average Delay' },
    { key: 'on_time_rate', label: 'On-Time Rate', render: (r) => `${r.on_time_rate}%` },
    { key: 'total_orders', label: 'Total Orders' },
  ]

  return (
    <div>
      <PageHeader
        title="Supplier Performance Report"
        subtitle="Delivery performance from analytics snapshots."
        action={<ExportButtons reportKey="suppliers" dateRange={dateRange} />}
      />

      <Alert type="error" message={error} />
      <DateRangeFilter value={dateRange} onChange={setDateRange} />

      {loading ? (
        <p className="text-sm text-slate-500">Loading report...</p>
      ) : (
        <>
          <SummaryCards
            items={[
              { label: 'Best Supplier', value: report?.summary?.best_supplier || '—' },
              { label: 'Worst Supplier', value: report?.summary?.worst_supplier || '—' },
              { label: 'Average Delay', value: `${report?.summary?.average_delay_across_suppliers ?? 0} days` },
            ]}
          />

          <div className="mb-8">
            <h2 className="mb-3 text-lg font-semibold text-slate-900">On-Time Rate by Supplier</h2>
            <SimpleBarChart
              data={report?.chart?.on_time_rate_by_supplier}
              xKey="supplier"
              yKey="on_time_rate"
              yLabel="On-Time Rate (%)"
              color="#059669"
            />
          </div>

          <DataTable
            columns={columns}
            data={report?.rows ?? []}
            emptyMessage="No supplier data in this period."
            rowKey={(row) => row.supplier}
          />
        </>
      )}
    </div>
  )
}
