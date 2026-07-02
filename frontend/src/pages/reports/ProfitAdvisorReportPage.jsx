import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { getBusinessSettings } from '../../api/auth'
import { exportProfitAdvisorAnalysis, getProfitAdvisorAnalysis } from '../../api/recommendations'
import PageHeader from '../../components/layout/PageHeader'
import Alert from '../../components/ui/Alert'

export default function ProfitAdvisorReportPage() {
  const [currency, setCurrency] = useState('USD')
  const [analysis, setAnalysis] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [exporting, setExporting] = useState(false)

  useEffect(() => {
    getBusinessSettings()
      .then((s) => setCurrency(s.currency || 'USD'))
      .catch(() => {})
    getProfitAdvisorAnalysis()
      .then((data) => {
        if (data.has_analysis) {
          setAnalysis(data)
        }
      })
      .catch(() => setError('Failed to load Profit Advisor analysis.'))
      .finally(() => setLoading(false))
  }, [])

  const formatMoney = (value) =>
    new Intl.NumberFormat('en-US', { style: 'currency', currency }).format(Number(value || 0))

  const handleExport = async (format) => {
    setExporting(true)
    try {
      await exportProfitAdvisorAnalysis(format)
    } catch {
      setError('Export failed.')
    } finally {
      setExporting(false)
    }
  }

  const allProducts = [
    ...(analysis?.recommended_products || []).map((p) => ({ ...p, decision: 'Recommended' })),
    ...(analysis?.deferred_products || []).map((p) => ({ ...p, decision: 'Deferred' })),
  ]

  return (
    <div>
      <PageHeader
        title="Profit Advisor Report"
        subtitle="Latest budget-based purchasing analysis. Independent from operational priority."
        action={
          analysis && (
            <div className="flex gap-2">
              <button
                type="button"
                disabled={exporting}
                onClick={() => handleExport('csv')}
                className="rounded-lg border border-slate-200 bg-white px-3 py-1.5 text-sm font-medium text-slate-700 hover:bg-slate-50 disabled:opacity-50"
              >
                Export CSV
              </button>
              <button
                type="button"
                disabled={exporting}
                onClick={() => handleExport('xlsx')}
                className="rounded-lg border border-slate-200 bg-white px-3 py-1.5 text-sm font-medium text-slate-700 hover:bg-slate-50 disabled:opacity-50"
              >
                Export Excel
              </button>
            </div>
          )
        }
      />

      <Alert type="error" message={error} />

      {loading ? (
        <p className="text-sm text-slate-500">Loading report...</p>
      ) : !analysis ? (
        <div className="rounded-xl border border-slate-200 bg-white p-6">
          <p className="text-sm text-slate-600">No Profit Advisor analysis has been performed yet.</p>
          <Link to="/recommendations" className="mt-3 inline-block text-sm font-medium text-brand-600 hover:text-brand-700">
            Run Profit Advisor on Recommendations
          </Link>
        </div>
      ) : (
        <>
          <div className="mb-6 grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
            <SummaryCard label="Budget" value={formatMoney(analysis.budget)} />
            <SummaryCard label="Recommended Spending" value={formatMoney(analysis.recommended_spending)} />
            <SummaryCard label="Deferred Spending" value={formatMoney(analysis.deferred_spending)} />
            <SummaryCard label="Expected Profit" value={formatMoney(analysis.expected_profit)} />
          </div>

          <p className="mb-4 text-sm text-slate-700">{analysis.explanation}</p>

          <div className="overflow-hidden rounded-xl border border-slate-200 bg-white">
            <table className="w-full text-left text-sm">
              <thead className="border-b border-slate-200 bg-slate-50">
                <tr>
                  <th className="px-4 py-3 font-medium text-slate-600">Product</th>
                  <th className="px-4 py-3 font-medium text-slate-600">Unit Profit</th>
                  <th className="px-4 py-3 font-medium text-slate-600">Purchase Cost</th>
                  <th className="px-4 py-3 font-medium text-slate-600">Expected Profit</th>
                  <th className="px-4 py-3 font-medium text-slate-600">Decision</th>
                </tr>
              </thead>
              <tbody>
                {allProducts.map((row) => (
                  <tr key={`${row.product}-${row.decision}`} className="border-b border-slate-100">
                    <td className="px-4 py-3">{row.product}</td>
                    <td className="px-4 py-3">{formatMoney(row.unit_profit)}</td>
                    <td className="px-4 py-3">{formatMoney(row.purchase_cost)}</td>
                    <td className="px-4 py-3">{formatMoney(row.expected_profit)}</td>
                    <td className="px-4 py-3">
                      {row.decision === 'Recommended' ? (
                        <span className="rounded-full bg-green-100 px-2 py-0.5 text-xs font-semibold text-green-800">
                          Recommended
                        </span>
                      ) : (
                        <span className="rounded-full bg-slate-100 px-2 py-0.5 text-xs font-semibold text-slate-600">
                          Deferred
                        </span>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </>
      )}
    </div>
  )
}

function SummaryCard({ label, value }) {
  return (
    <div className="rounded-xl border border-slate-200 bg-white p-4">
      <div className="text-sm text-slate-500">{label}</div>
      <div className="mt-1 text-xl font-semibold text-slate-900">{value}</div>
    </div>
  )
}
