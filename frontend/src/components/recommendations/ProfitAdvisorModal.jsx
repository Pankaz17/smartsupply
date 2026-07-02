import { useState } from 'react'
import Button from '../ui/Button'
import Input from '../ui/Input'

export default function ProfitAdvisorModal({ currency, onClose, onAnalyze, analyzing }) {
  const [budget, setBudget] = useState('')

  const handleSubmit = (e) => {
    e.preventDefault()
    onAnalyze(budget)
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 p-4">
      <div className="w-full max-w-md rounded-xl border border-slate-200 bg-white p-6 shadow-xl">
        <h2 className="text-lg font-semibold text-slate-900">Profit Advisor</h2>
        <p className="mt-1 text-sm text-slate-500">
          Enter your available purchasing budget to see which restocks offer the best return.
        </p>

        <form onSubmit={handleSubmit} className="mt-5 space-y-4">
          <Input
            id="purchasing-budget"
            label={`Available Budget (${currency})`}
            type="number"
            step="0.01"
            min="0.01"
            required
            placeholder="30000"
            value={budget}
            onChange={(e) => setBudget(e.target.value)}
          />
          <div className="flex justify-end gap-2">
            <Button type="button" variant="secondary" onClick={onClose} disabled={analyzing}>
              Cancel
            </Button>
            <Button type="submit" disabled={analyzing}>
              {analyzing ? 'Analyzing...' : 'Analyze'}
            </Button>
          </div>
        </form>
      </div>
    </div>
  )
}
