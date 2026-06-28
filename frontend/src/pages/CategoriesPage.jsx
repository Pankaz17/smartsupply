import { useCallback, useEffect, useState } from 'react'
import { createCategory, getCategories, updateCategory } from '../api/categories'
import PageHeader from '../components/layout/PageHeader'
import Alert from '../components/ui/Alert'
import Button from '../components/ui/Button'
import DataTable from '../components/ui/DataTable'
import Input from '../components/ui/Input'
import StatusBadge from '../components/ui/StatusBadge'
import Textarea from '../components/ui/Textarea'
import { useAuth } from '../context/AuthContext'

const emptyForm = { name: '', description: '', is_active: true }

export default function CategoriesPage() {
  const { isOwner } = useAuth()
  const [categories, setCategories] = useState([])
  const [loading, setLoading] = useState(true)
  const [showForm, setShowForm] = useState(false)
  const [editing, setEditing] = useState(null)
  const [form, setForm] = useState(emptyForm)
  const [error, setError] = useState('')
  const [success, setSuccess] = useState('')

  const load = useCallback(() => {
    setLoading(true)
    getCategories()
      .then(setCategories)
      .catch(() => setError('Failed to load categories.'))
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

  const openEdit = (cat) => {
    setEditing(cat)
    setForm({ name: cat.name, description: cat.description || '', is_active: cat.is_active })
    setShowForm(true)
    setError('')
    setSuccess('')
  }

  const handleSubmit = async (e) => {
    e.preventDefault()
    setError('')
    setSuccess('')
    try {
      if (editing) {
        await updateCategory(editing.id, form)
        setSuccess('Category updated.')
      } else {
        await createCategory(form)
        setSuccess('Category created.')
      }
      setShowForm(false)
      load()
    } catch (err) {
      const data = err.response?.data
      setError(data?.name?.[0] || data?.detail || 'Failed to save category.')
    }
  }

  const toggleActive = async (cat) => {
    try {
      await updateCategory(cat.id, { is_active: !cat.is_active })
      load()
    } catch {
      setError('Failed to update category status.')
    }
  }

  const columns = [
    { key: 'name', label: 'Name' },
    { key: 'description', label: 'Description', render: (r) => r.description || '—' },
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
        title="Categories"
        subtitle="Organize products by category."
        action={isOwner && (
          <Button onClick={openCreate}>{showForm && !editing ? 'Cancel' : 'Add Category'}</Button>
        )}
      />

      <Alert type="error" message={error} />
      <Alert type="success" message={success} />

      {showForm && isOwner && (
        <form onSubmit={handleSubmit} className="mb-6 max-w-lg space-y-4 rounded-xl border border-slate-200 bg-white p-5 shadow-sm">
          <Input
            id="name"
            label="Name"
            required
            value={form.name}
            onChange={(e) => setForm({ ...form, name: e.target.value })}
          />
          <Textarea
            id="description"
            label="Description"
            value={form.description}
            onChange={(e) => setForm({ ...form, description: e.target.value })}
          />
          <label className="flex items-center gap-2 text-sm text-slate-700">
            <input
              type="checkbox"
              checked={form.is_active}
              onChange={(e) => setForm({ ...form, is_active: e.target.checked })}
            />
            Active
          </label>
          <div className="flex gap-2">
            <Button type="submit">{editing ? 'Update' : 'Create'}</Button>
            <Button type="button" variant="secondary" onClick={() => setShowForm(false)}>Cancel</Button>
          </div>
        </form>
      )}

      {loading ? (
        <p className="text-sm text-slate-500">Loading categories...</p>
      ) : (
        <DataTable columns={columns} data={categories} emptyMessage="No categories yet." />
      )}
    </div>
  )
}
