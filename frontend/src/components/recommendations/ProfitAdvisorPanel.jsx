export default function ProfitAdvisorPanel({ analysis, currency, onExport, exporting, isOwner, onRunAgain }) {
  if (!analysis) return null

  const formatMoney = (value) =>
    new Intl.NumberFormat('en-US', { style: 'currency', currency: currency || 'USD' }).format(
      Number(value || 0),
    )

  const allProducts = [
    ...(analysis.recommended_products || []).map((p) => ({ ...p, decision: 'recommended' })),
    ...(analysis.deferred_products || []).map((p) => ({ ...p, decision: 'deferred' })),
  ]

  return (
    <div className="mb-6 rounded-xl border border-brand-200 bg-brand-50/40 p-6">
      <div className="mb-4 flex flex-wrap items-start justify-between gap-3">
        <div>
          <h2 className="text-lg font-semibold text-slate-900">Profit Advisor Results</h2>
          <p className="mt-2 text-sm text-slate-700">{analysis.explanation}</p>
        </div>
        <div className="flex flex-wrap gap-2">
          {isOwner && (
            <button
              type="button"
              onClick={onRunAgain}
              className="rounded-lg border border-slate-200 bg-white px-3 py-1.5 text-sm font-medium text-slate-700 hover:bg-slate-50"
            >
              Run Again
            </button>
          )}
          <button
            type="button"
            disabled={exporting}
            onClick={() => onExport('csv')}
            className="rounded-lg border border-slate-200 bg-white px-3 py-1.5 text-sm font-medium text-slate-700 hover:bg-slate-50 disabled:opacity-50"
          >
            Export CSV
          </button>
          <button
            type="button"
            disabled={exporting}
            onClick={() => onExport('xlsx')}
            className="rounded-lg border border-slate-200 bg-white px-3 py-1.5 text-sm font-medium text-slate-700 hover:bg-slate-50 disabled:opacity-50"
          >
            Export Excel
          </button>
        </div>
      </div>

      <div className="mb-4 overflow-hidden rounded-xl border border-slate-200 bg-white">
        <table className="w-full text-left text-sm">
          <thead className="border-b border-slate-200 bg-slate-50">
            <tr>
              <th className="px-4 py-3 font-medium text-slate-600">Product</th>
              <th className="px-4 py-3 font-medium text-slate-600">Purchase Cost</th>
              <th className="px-4 py-3 font-medium text-slate-600">Expected Profit</th>
              <th className="px-4 py-3 font-medium text-slate-600">Decision</th>
            </tr>
          </thead>
          <tbody>
            {allProducts.length === 0 ? (
              <tr>
                <td colSpan={4} className="px-4 py-6 text-center text-slate-400">
                  No pending recommendations to analyze.
                </td>
              </tr>
            ) : (
              allProducts.map((row) => (
                <tr key={`${row.product}-${row.decision}`} className="border-b border-slate-100">
                  <td className="px-4 py-3">{row.product}</td>
                  <td className="px-4 py-3">{formatMoney(row.purchase_cost)}</td>
                  <td className="px-4 py-3">{formatMoney(row.expected_profit)}</td>
                  <td className="px-4 py-3">
                    {row.decision === 'recommended' ? (
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
              ))
            )}
          </tbody>
        </table>
      </div>

      <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
        <SummaryItem label="Budget" value={formatMoney(analysis.budget)} />
        <SummaryItem label="Recommended Spending" value={formatMoney(analysis.recommended_spending)} />
        <SummaryItem label="Remaining Budget" value={formatMoney(analysis.remaining_budget)} />
        <SummaryItem label="Expected Restock Profit" value={formatMoney(analysis.expected_profit)} />
      </div>
      <p className="mt-3 text-sm text-slate-600">
        Products recommended: <strong>{analysis.recommended_count ?? 0}</strong>
      </p>
    </div>
  )
}

function SummaryItem({ label, value }) {
  return (
    <div className="rounded-lg border border-slate-200 bg-white px-4 py-3">
      <div className="text-xs font-medium text-slate-500">{label}</div>
      <div className="mt-1 text-base font-semibold text-slate-900">{value}</div>
    </div>
  )
}
