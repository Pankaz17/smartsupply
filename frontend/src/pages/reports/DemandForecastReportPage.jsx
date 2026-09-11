import { useCallback, useEffect, useState } from 'react'
import { getDemandForecastReport } from '../../api/reports'
import DateRangeFilter, { DEFAULT_DATE_RANGE } from '../../components/reports/DateRangeFilter'
import ExportButtons from '../../components/reports/ExportButtons'
import SimpleBarChart from '../../components/reports/SimpleBarChart'
import SummaryCards from '../../components/reports/SummaryCards'
import PageHeader from '../../components/layout/PageHeader'
import Alert from '../../components/ui/Alert'
import DataTable from '../../components/ui/DataTable'

export default function DemandForecastReportPage() {
  const [dateRange, setDateRange] = useState(DEFAULT_DATE_RANGE)
  const [report, setReport] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  const load = useCallback(() => {
    if (dateRange.mode === 'custom' && (!dateRange.startDate || !dateRange.endDate)) return
    setLoading(true)
    getDemandForecastReport(dateRange)
      .then(setReport)
      .catch(() => setError('Failed to load demand forecast report.'))
      .finally(() => setLoading(false))
  }, [dateRange])

  useEffect(() => { load() }, [load])

  const columns = [
    { key: 'product', label: 'Product' },
    { key: 'sku', label: 'SKU' },
    { key: 'historical_ads', label: 'Historical ADS' },
    {
      key: 'predicted_daily_demand',
      label: 'Predicted Daily Demand',
      render: (r) => (r.predicted_daily_demand != null ? r.predicted_daily_demand : '—'),
    },
    { key: 'forecast_horizon', label: 'Forecast Horizon' },
    {
      key: 'model',
      label: 'Model',
      render: (r) => r.model || '—',
    },
    { key: 'status', label: 'Status' },
    { key: 'historical_observations', label: 'Observations' },
    {
      key: 'mae',
      label: 'MAE',
      render: (r) => (r.mae != null ? r.mae : '—'),
    },
  ]

  return (
    <div>
      <PageHeader
        title="Demand Forecast Report"
        subtitle="ARIMA predicted demand versus historical ADS."
        action={<ExportButtons reportKey="demand-forecast" dateRange={dateRange} />}
      />

      <Alert type="error" message={error} />
      <DateRangeFilter value={dateRange} onChange={setDateRange} />

      {loading ? (
        <p className="text-sm text-slate-500">Loading report...</p>
      ) : (
        <>
          <SummaryCards
            items={[
              {
                label: 'Products With Forecast',
                value: report?.summary?.products_with_forecast ?? 0,
              },
              {
                label: 'Insufficient Data',
                value: report?.summary?.products_insufficient_data ?? 0,
              },
              {
                label: 'Forecast As Of',
                value: report?.summary?.forecast_as_of ?? '—',
              },
            ]}
          />

          <div className="mb-8">
            <h2 className="mb-3 text-lg font-semibold text-slate-900">
              Predicted Daily Demand
            </h2>
            <SimpleBarChart
              data={report?.chart?.predicted_demand_by_product}
              xKey="product"
              yKey="predicted_daily_demand"
              yLabel="Units/day"
            />
          </div>

          <DataTable
            columns={columns}
            data={report?.rows ?? []}
            emptyMessage="No forecast data found."
            rowKey={(row) => row.sku}
          />
        </>
      )}
    </div>
  )
}
