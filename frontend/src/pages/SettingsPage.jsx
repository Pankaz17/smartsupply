import { useEffect, useState } from 'react'
import { getBusinessSettings, updateBusinessSettings } from '../api/auth'
import PageHeader from '../components/layout/PageHeader'

const CURRENCIES = ['USD', 'EUR', 'GBP', 'CAD', 'AUD', 'INR']

export default function SettingsPage() {
  const [form, setForm] = useState({
    store_name: '',
    currency: 'USD',
    dead_stock_threshold_days: 90,
    seasonal_alert_window_days: 14,
  })
  const [loading, setLoading] = useState(true)
  const [saving, setSaving] = useState(false)
  const [message, setMessage] = useState('')
  const [error, setError] = useState('')

  useEffect(() => {
    getBusinessSettings()
      .then((data) => {
        setForm(data)
      })
      .catch(() => setError('Failed to load settings.'))
      .finally(() => setLoading(false))
  }, [])

  const handleChange = (e) => {
    const { name, value } = e.target
    setForm((prev) => ({
      ...prev,
      [name]: name.includes('_days') ? Number(value) : value,
    }))
  }

  const handleSubmit = async (e) => {
    e.preventDefault()
    setSaving(true)
    setMessage('')
    setError('')
    try {
      const updated = await updateBusinessSettings(form)
      setForm(updated)
      setMessage('Settings saved successfully.')
    } catch {
      setError('Failed to save settings.')
    } finally {
      setSaving(false)
    }
  }

  if (loading) {
    return <div className="text-sm text-slate-500">Loading settings...</div>
  }

  return (
    <div>
      <PageHeader
        title="Business Settings"
        subtitle="Configure your store preferences."
      />

      <form onSubmit={handleSubmit} className="max-w-xl space-y-5 rounded-xl border border-slate-200 bg-white p-6 shadow-sm">
        {message && (
          <div className="rounded-lg bg-green-50 px-4 py-3 text-sm text-green-700">{message}</div>
        )}
        {error && (
          <div className="rounded-lg bg-red-50 px-4 py-3 text-sm text-red-700">{error}</div>
        )}

        <Field label="Store Name" name="store_name" value={form.store_name} onChange={handleChange} />

        <div>
          <label htmlFor="currency" className="mb-1 block text-sm font-medium text-slate-700">
            Currency
          </label>
          <select
            id="currency"
            name="currency"
            value={form.currency}
            onChange={handleChange}
            className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm focus:border-brand-500 focus:outline-none focus:ring-2 focus:ring-brand-100"
          >
            {CURRENCIES.map((c) => (
              <option key={c} value={c}>{c}</option>
            ))}
          </select>
        </div>

        <Field
          label="Dead Stock Threshold (days)"
          name="dead_stock_threshold_days"
          type="number"
          min={1}
          value={form.dead_stock_threshold_days}
          onChange={handleChange}
          hint="Products with no sales beyond this period are flagged as dead stock."
        />

        <Field
          label="Seasonal Alert Window (days)"
          name="seasonal_alert_window_days"
          type="number"
          min={1}
          value={form.seasonal_alert_window_days}
          onChange={handleChange}
          hint="How many days ahead to alert about upcoming seasonal events."
        />

        <button
          type="submit"
          disabled={saving}
          className="rounded-lg bg-brand-600 px-4 py-2 text-sm font-semibold text-white hover:bg-brand-700 disabled:opacity-60"
        >
          {saving ? 'Saving...' : 'Save Settings'}
        </button>
      </form>
    </div>
  )
}

function Field({ label, name, value, onChange, type = 'text', min, hint }) {
  return (
    <div>
      <label htmlFor={name} className="mb-1 block text-sm font-medium text-slate-700">
        {label}
      </label>
      <input
        id={name}
        name={name}
        type={type}
        min={min}
        value={value}
        onChange={onChange}
        className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm focus:border-brand-500 focus:outline-none focus:ring-2 focus:ring-brand-100"
      />
      {hint && <p className="mt-1 text-xs text-slate-400">{hint}</p>}
    </div>
  )
}
