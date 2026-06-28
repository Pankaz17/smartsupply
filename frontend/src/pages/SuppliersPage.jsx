import { useCallback, useEffect, useState } from 'react'
import { createSupplier, getSuppliers, updateSupplier } from '../api/suppliers'
import PageHeader from '../components/layout/PageHeader'
import Alert from '../components/ui/Alert'
import Button from '../components/ui/Button'
import DataTable from '../components/ui/DataTable'
import Input from '../components/ui/Input'
import StatusBadge from '../components/ui/StatusBadge'
import Textarea from '../components/ui/Textarea'
import { useAuth } from '../context/AuthContext'

const emptyForm = {
  name: '',
  phone: '',
  email: '',
  address: '',
  promised_lead_time_days: 7,
  notes: '',
  is_active: true,
}

export default function SuppliersPage() {
  const { isOwner } = useAuth()
  const [suppliers, setSuppliers] = useState([])
  const [loading, setLoading] = useState(true)
  const [showForm, setShowForm] = useState(false)
  const [editing, setEditing] = useState(null)
  const [form, setForm] = useState(emptyForm)
  const [error, setError] = useState('')
  const [success, setSuccess] = useState('')

  const load = useCallback(() => {
    setLoading(true)
    getSuppliers()
      .then(setSuppliers)
      .catch(() => setError('Failed to load suppliers.'))
      .finally(() => setLoading(false))
  }, [])

  useEffect(() => { load() }, [load])

  const openCreate = () => {
    setEditing(null)
    setForm(emptyForm)
    setShowForm(true)
    setError('')
    setSuccess('')
  }

  const openEdit = (s) => {
    setEditing(s)
    setForm({
      name: s.name,
      phone: s.phone || '',
      email: s.email || '',
      address: s.address || '',
      promised_lead_time_days: s.promised_lead_time_days,
      notes: s.notes || '',
      is_active: s.is_active,
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
        promised_lead_time_days: Number(form.promised_lead_time_days),
      }
      if (editing) {
        await updateSupplier(editing.id, payload)
        setSuccess('Supplier updated.')
      } else {
        await createSupplier(payload)
        setSuccess('Supplier created.')
      }
      setShowForm(false)
      load()
    } catch (err) {
      const data = err.response?.data
      setError(data?.name?.[0] || data?.email?.[0] || data?.detail || 'Failed to save supplier.')
    }
  }

  const toggleActive = async (s) => {
    try {
      await updateSupplier(s.id, { is_active: !s.is_active })
      load()
    } catch {
      setError('Failed to update supplier status.')
    }
  }

  const columns = [
    { key: 'name', label: 'Name' },
    { key: 'email', label: 'Email', render: (r) => r.email || '—' },
    { key: 'phone', label: 'Phone', render: (r) => r.phone || '—' },
    { key: 'promised_lead_time_days', label: 'Lead Time (days)' },
    { key: 'product_count', label: 'Products' },
    {
      key: 'is_active',
      label: 'Status',
      render: (r) => <StatusBadge active={r.is_active} />,
    },
  ]

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
        title="Suppliers"
        subtitle="Manage supplier contacts and lead times."
        action={isOwner && (
          <Button onClick={openCreate}>{showForm && !editing ? 'Cancel' : 'Add Supplier'}</Button>
        )}
      />

      <Alert type="error" message={error} />
      <Alert type="success" message={success} />

      {showForm && isOwner && (
        <form onSubmit={handleSubmit} className="mb-6 grid max-w-2xl gap-4 rounded-xl border border-slate-200 bg-white p-5 shadow-sm md:grid-cols-2">
          <Input id="name" label="Name" required className="md:col-span-2" value={form.name} onChange={(e) => setForm({ ...form, name: e.target.value })} />
          <Input id="email" label="Email" type="email" value={form.email} onChange={(e) => setForm({ ...form, email: e.target.value })} />
          <Input id="phone" label="Phone" value={form.phone} onChange={(e) => setForm({ ...form, phone: e.target.value })} />
          <Input id="lead_time" label="Promised Lead Time (days)" type="number" min={1} required value={form.promised_lead_time_days} onChange={(e) => setForm({ ...form, promised_lead_time_days: e.target.value })} />
          <Textarea id="address" label="Address" className="md:col-span-2" value={form.address} onChange={(e) => setForm({ ...form, address: e.target.value })} />
          <Textarea id="notes" label="Notes" className="md:col-span-2" value={form.notes} onChange={(e) => setForm({ ...form, notes: e.target.value })} />
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
        <p className="text-sm text-slate-500">Loading suppliers...</p>
      ) : (
        <DataTable columns={columns} data={suppliers} emptyMessage="No suppliers yet." />
      )}
    </div>
  )
}
