import { useCallback, useEffect, useState } from 'react'
import { getCategories } from '../api/categories'
import {
  createSeasonalEvent,
  getSeasonalEvents,
  runAnalytics,
  updateSeasonalEvent,
} from '../api/analytics'
import PageHeader from '../components/layout/PageHeader'
import Alert from '../components/ui/Alert'
import Button from '../components/ui/Button'
import DataTable from '../components/ui/DataTable'
import Input from '../components/ui/Input'
import Select from '../components/ui/Select'
import StatusBadge from '../components/ui/StatusBadge'
import { useAuth } from '../context/AuthContext'

const emptyForm = {
  name: '',
  start_date: '',
  end_date: '',
  category: '',
  multiplier: '1.0',
  is_active: true,
}

export default function SeasonalEventsPage() {
  const { isOwner } = useAuth()
  const [events, setEvents] = useState([])
  const [categories, setCategories] = useState([])
  const [loading, setLoading] = useState(true)
  const [showForm, setShowForm] = useState(false)
  const [editing, setEditing] = useState(null)
  const [form, setForm] = useState(emptyForm)
  const [error, setError] = useState('')
  const [success, setSuccess] = useState('')

  const load = useCallback(() => {
    setLoading(true)
    getSeasonalEvents()
      .then(setEvents)
      .catch(() => setError('Failed to load seasonal events.'))
      .finally(() => setLoading(false))
  }, [])

  useEffect(() => {
    getCategories().then(setCategories).catch(() => {})
    load()
  }, [load])

  const categoryOptions = categories.map((c) => ({ value: c.id, label: c.name }))

  const openCreate = () => {
    setEditing(null)
    setForm(emptyForm)
    setShowForm(true)
    setError('')
    setSuccess('')
  }

  const openEdit = (event) => {
    setEditing(event)
    setForm({
      name: event.name,
      start_date: event.start_date,
      end_date: event.end_date,
      category: String(event.category),
      multiplier: event.multiplier,
      is_active: event.is_active,
    })
    setShowForm(true)
    setError('')
    setSuccess('')
  }

  const handleSubmit = async (e) => {
    e.preventDefault()
    setError('')
    setSuccess('')
    try {
      const payload = {
        ...form,
        category: Number(form.category),
        multiplier: form.multiplier,
      }
      if (editing) {
        await updateSeasonalEvent(editing.id, payload)
        setSuccess('Seasonal event updated.')
      } else {
        await createSeasonalEvent(payload)
        setSuccess('Seasonal event created.')
      }
      setShowForm(false)
      load()
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to save seasonal event.')
    }
  }

  const toggleActive = async (event) => {
    try {
      await updateSeasonalEvent(event.id, { is_active: !event.is_active })
      load()
    } catch {
      setError('Failed to update event status.')
    }
  }

  const handleRunAnalytics = async () => {
    setError('')
    setSuccess('')
    try {
      const result = await runAnalytics()
      setSuccess(result.message)
    } catch {
      setError('Failed to run analytics.')
    }
  }

  const columns = [
    { key: 'name', label: 'Event' },
    { key: 'category_name', label: 'Category' },
  ]

  columns.push(
    { key: 'start_date', label: 'Start' },
    { key: 'end_date', label: 'End' },
    { key: 'multiplier', label: 'Multiplier', render: (r) => `×${r.multiplier}` },
    {
      key: 'is_active',
      label: 'Status',
      render: (r) => <StatusBadge active={r.is_active} />,
    },
  )

  if (isOwner) {
    columns.push({
      key: 'actions',
      label: 'Actions',
      render: (r) => (
        <div className="flex gap-2">
          <button type="button" onClick={() => openEdit(r)} className="text-sm font-medium text-brand-600 hover:text-brand-700">
            Edit
          </button>
          <button type="button" onClick={() => toggleActive(r)} className="text-sm font-medium text-slate-600 hover:text-slate-800">
            {r.is_active ? 'Deactivate' : 'Activate'}
          </button>
        </div>
      ),
    })
  }

  return (
    <div>
      <PageHeader
        title="Seasonal Events"
        subtitle="Category-based demand multipliers applied during recommendation generation."
        action={isOwner && (
          <div className="flex gap-2">
            <Button variant="secondary" onClick={handleRunAnalytics}>Run Analytics</Button>
            <Button onClick={openCreate}>{showForm && !editing ? 'Cancel' : 'Add Event'}</Button>
          </div>
        )}
      />

      <Alert type="error" message={error} />
      <Alert type="success" message={success} />

      {showForm && isOwner && (
        <form onSubmit={handleSubmit} className="mb-6 grid max-w-2xl gap-4 rounded-xl border border-slate-200 bg-white p-5 shadow-sm md:grid-cols-2">
          <Input id="name" label="Event Name" required className="md:col-span-2" value={form.name} onChange={(e) => setForm({ ...form, name: e.target.value })} />
          <Input id="start_date" label="Start Date" type="date" required value={form.start_date} onChange={(e) => setForm({ ...form, start_date: e.target.value })} />
          <Input id="end_date" label="End Date" type="date" required value={form.end_date} onChange={(e) => setForm({ ...form, end_date: e.target.value })} />
          <Select id="category" label="Category" required options={categoryOptions} value={form.category} onChange={(e) => setForm({ ...form, category: e.target.value })} />
          <Input id="multiplier" label="Demand Multiplier" type="number" step="0.1" min="0.1" required value={form.multiplier} onChange={(e) => setForm({ ...form, multiplier: e.target.value })} hint="e.g. 1.3 increases ADS by 30%" />
          <label className="flex items-center gap-2 text-sm text-slate-700 md:col-span-2">
            <input type="checkbox" checked={form.is_active} onChange={(e) => setForm({ ...form, is_active: e.target.checked })} />
            Active
          </label>
          <div className="flex gap-2 md:col-span-2">
            <Button type="submit">{editing ? 'Update' : 'Create'}</Button>
            <Button type="button" variant="secondary" onClick={() => setShowForm(false)}>Cancel</Button>
          </div>
        </form>
      )}

      {loading ? (
        <p className="text-sm text-slate-500">Loading seasonal events...</p>
      ) : (
        <DataTable columns={columns} data={events} emptyMessage="No seasonal events configured." />
      )}
    </div>
  )
}
