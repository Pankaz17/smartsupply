import { useCallback, useEffect, useState } from 'react'
import { getInventoryReport } from '../../api/reports'
import DateRangeFilter, { DEFAULT_DATE_RANGE } from '../../components/reports/DateRangeFilter'
import ExportButtons from '../../components/reports/ExportButtons'
import SimpleBarChart from '../../components/reports/SimpleBarChart'
import SummaryCards from '../../components/reports/SummaryCards'
import PageHeader from '../../components/layout/PageHeader'
import Alert from '../../components/ui/Alert'
import DataTable from '../../components/ui/DataTable'

export default function InventoryReportPage() {
  const [dateRange, setDateRange] = useState(DEFAULT_DATE_RANGE)
  const [report, setReport] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  const load = useCallback(() => {
    if (dateRange.mode === 'custom' && (!dateRange.startDate || !dateRange.endDate)) return
    setLoading(true)
    getInventoryReport(dateRange)
      .then(setReport)
      .catch(() => setError('Failed to load inventory report.'))
      .finally(() => setLoading(false))
  }, [dateRange])

  useEffect(() => { load() }, [load])

  const formatMoney = (value) =>
    new Intl.NumberFormat('en-US', { style: 'currency', currency: 'USD' }).format(Number(value || 0))

  const columns = [
    { key: 'sku', label: 'SKU' },
    { key: 'product', label: 'Product' },
    { key: 'category', label: 'Category' },
    { key: 'supplier', label: 'Supplier' },
    { key: 'current_stock', label: 'Current Stock' },
    { key: 'cost_price', label: 'Cost Price', render: (r) => formatMoney(r.cost_price) },
    { key: 'inventory_value', label: 'Inventory Value', render: (r) => formatMoney(r.inventory_value) },
  ]

  return (
    <div>
      <PageHeader
        title="Inventory Valuation Report"
        subtitle="Current value tied up in inventory."
        action={<ExportButtons reportKey="inventory" dateRange={dateRange} />}
      />

      <Alert type="error" message={error} />
      <DateRangeFilter value={dateRange} onChange={setDateRange} />

      {loading ? (
        <p className="text-sm text-slate-500">Loading report...</p>
      ) : (
        <>
          <SummaryCards
            items={[
              { label: 'Total Inventory Value', value: formatMoney(report?.summary?.total_inventory_value) },
              { label: 'Total Products', value: report?.summary?.total_products ?? 0 },
              { label: 'Out Of Stock', value: report?.summary?.out_of_stock_count ?? 0 },
            ]}
          />

          <div className="mb-8">
            <h2 className="mb-3 text-lg font-semibold text-slate-900">Inventory Value by Category</h2>
            <SimpleBarChart
              data={report?.chart?.inventory_value_by_category}
              xKey="category"
              yKey="value"
              yLabel="Value"
            />
          </div>

          <DataTable
            columns={columns}
            data={report?.rows ?? []}
            emptyMessage="No products found."
            rowKey={(row) => row.sku}
          />
        </>
      )}
    </div>
  )
}
