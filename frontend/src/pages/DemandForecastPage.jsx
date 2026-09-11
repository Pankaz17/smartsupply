import { useCallback, useEffect, useState } from 'react'
import { getDemandForecasts, refreshDemandForecasts } from '../api/analytics'
import PageHeader from '../components/layout/PageHeader'
import Alert from '../components/ui/Alert'
import Button from '../components/ui/Button'
import { useAuth } from '../context/AuthContext'

export default function DemandForecastPage() {
  const { isOwner } = useAuth()
  const [forecasts, setForecasts] = useState([])
  const [loading, setLoading] = useState(true)
  const [refreshing, setRefreshing] = useState(false)
  const [error, setError] = useState('')
  const [success, setSuccess] = useState('')

  const load = useCallback(() => {
    setLoading(true)
    setError('')
    getDemandForecasts()
      .then(setForecasts)
      .catch(() => setError('Failed to load demand forecasts.'))
      .finally(() => setLoading(false))
  }, [])

  useEffect(() => {
    load()
  }, [load])

  const handleRefresh = async () => {
    setRefreshing(true)
    setError('')
    setSuccess('')
    try {
      const result = await refreshDemandForecasts()
      const summary = result.summary || {}
      setSuccess(
        `Forecasts refreshed — available: ${summary.forecasts_available ?? 0}, `
        + `insufficient data: ${summary.forecasts_insufficient ?? 0}.`,
      )
      load()
    } catch {
      setError('Failed to refresh forecasts.')
    } finally {
      setRefreshing(false)
    }
  }

  return (
    <div>
      <PageHeader
        title="Demand Forecast"
        action={isOwner && (
          <Button onClick={handleRefresh} disabled={refreshing}>
            {refreshing ? 'Refreshing…' : 'Refresh Forecasts'}
          </Button>
        )}
      />

      <Alert type="error" message={error} />
      <Alert type="success" message={success} />

      {loading ? (
        <p className="text-sm text-slate-500">Loading forecasts...</p>
      ) : forecasts.length === 0 ? (
        <p className="rounded-xl border border-slate-200 bg-white p-6 text-sm text-slate-500">
          No forecast data yet. Record sales history and refresh forecasts.
        </p>
      ) : (
        <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-3">
          {forecasts.map((item) => {
            const available = item.status === 'FORECAST_AVAILABLE'
            const key = item.id || item.product_id || item.product
            return (
              <div
                key={key}
                className="rounded-xl border border-slate-200 bg-white p-5 shadow-sm"
              >
                <div className="text-xs font-medium uppercase tracking-wide text-slate-500">
                  Demand Forecast
                </div>
                <h2 className="mt-1 text-lg font-semibold text-slate-900">
                  {item.product_name || item.product}
                </h2>

                {available ? (
                  <>
                    <dl className="mt-4 space-y-2 text-sm">
                      <div className="flex justify-between gap-3">
                        <dt className="text-slate-500">Predicted demand</dt>
                        <dd className="font-medium text-slate-900">
                          {Number(item.predicted_daily_demand).toFixed(1)} units/day
                        </dd>
                      </div>
                      <div className="flex justify-between gap-3">
                        <dt className="text-slate-500">
                          Next {item.forecast_horizon} days
                        </dt>
                        <dd className="font-medium text-slate-900">
                          {Number(item.predicted_horizon_total).toFixed(0)} units
                        </dd>
                      </div>
                      <div className="flex justify-between gap-3">
                        <dt className="text-slate-500">Model</dt>
                        <dd className="font-medium text-slate-900">{item.model || 'ARIMA'}</dd>
                      </div>
                      <div className="flex justify-between gap-3">
                        <dt className="text-slate-500">History</dt>
                        <dd className="font-medium text-slate-900">
                          {item.historical_observations} days
                        </dd>
                      </div>
                      {item.mae != null && (
                        <div className="flex justify-between gap-3">
                          <dt className="text-slate-500">Forecast MAE</dt>
                          <dd className="font-medium text-slate-900">
                            {Number(item.mae).toFixed(1)} units/day
                          </dd>
                        </div>
                      )}
                    </dl>
                    <p className="mt-4 text-xs font-medium text-green-700">
                      Forecast available
                    </p>
                  </>
                ) : (
                  <>
                    <p className="mt-4 text-sm font-medium text-slate-800">
                      Forecast unavailable
                    </p>
                    <p className="mt-2 text-sm text-slate-500">
                      More historical sales data is required
                      {item.historical_observations != null
                        ? ` (${item.historical_observations} daily observations so far).`
                        : '.'}
                    </p>
                    <p className="mt-3 text-xs text-slate-500">
                      Current recommendations use historical demand
                      {item.fallback ? ` (${item.fallback}).` : '.'}
                    </p>
                  </>
                )}
              </div>
            )
          })}
        </div>
      )}
    </div>
  )
}
