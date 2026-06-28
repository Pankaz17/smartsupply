import { useCallback, useEffect, useState } from 'react'
import { getCategories } from '../api/categories'
import { createProduct, getProducts, updateProduct } from '../api/products'
import { getSuppliers } from '../api/suppliers'
import PageHeader from '../components/layout/PageHeader'
import Alert from '../components/ui/Alert'
import Button from '../components/ui/Button'
import DataTable from '../components/ui/DataTable'
import Input from '../components/ui/Input'
import Select from '../components/ui/Select'
import StatusBadge from '../components/ui/StatusBadge'
import { useAuth } from '../context/AuthContext'

const UNIT_OPTIONS = [
  { value: 'pcs', label: 'Pieces' },
  { value: 'kg', label: 'Kilograms' },
  { value: 'litre', label: 'Litres' },
  { value: 'pack', label: 'Packs' },
]

const emptyForm = {
  sku: '',
  name: '',
  category: '',
  supplier: '',
  cost_price: '',
  selling_price: '',
  unit: 'pcs',
  is_active: true,
}

export default function ProductsPage() {
  const { isOwner } = useAuth()
  const [products, setProducts] = useState([])
  const [categories, setCategories] = useState([])
  const [suppliers, setSuppliers] = useState([])
  const [loading, setLoading] = useState(true)
  const [showForm, setShowForm] = useState(false)
  const [editing, setEditing] = useState(null)
  const [form, setForm] = useState(emptyForm)
  const [filters, setFilters] = useState({ search: '', category: '', supplier: '', is_active: '' })
  const [error, setError] = useState('')
  const [success, setSuccess] = useState('')

  const loadProducts = useCallback(() => {
    const params = {}
    if (filters.search) params.search = filters.search
    if (filters.category) params.category = filters.category
    if (filters.supplier) params.supplier = filters.supplier
    if (filters.is_active !== '') params.is_active = filters.is_active

    setLoading(true)
    getProducts(params)
      .then(setProducts)
      .catch(() => setError('Failed to load products.'))
      .finally(() => setLoading(false))
  }, [filters])

  useEffect(() => {
    getCategories({ is_active: true }).then(setCategories).catch(() => {})
    getSuppliers({ is_active: true }).then(setSuppliers).catch(() => {})
  }, [])

  useEffect(() => { loadProducts() }, [loadProducts])

  const openCreate = () => {
    setEditing(null)
    setForm(emptyForm)
    setShowForm(true)
    setError('')
    setSuccess('')
  }

  const openEdit = (p) => {
    setEditing(p)
    setForm({
      sku: p.sku,
      name: p.name,
      category: String(p.category),
      supplier: String(p.supplier),
      cost_price: p.cost_price,
      selling_price: p.selling_price,
      unit: p.unit,
      is_active: p.is_active,
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
        supplier: Number(form.supplier),
        cost_price: form.cost_price,
        selling_price: form.selling_price,
      }
      if (editing) {
        const data = await updateProduct(editing.id, payload)
        setSuccess(
          data.warnings?.length
            ? `Product updated. ${data.warnings.join(' ')}`
            : 'Product updated.',
        )
      } else {
        await createProduct(payload)
        setSuccess('Product created.')
      }
      setShowForm(false)
      loadProducts()
    } catch (err) {
      const data = err.response?.data
      setError(
        data?.current_stock?.[0]
        || data?.sku?.[0] || data?.selling_price?.[0] || data?.detail
        || Object.values(data || {}).flat()[0]
        || 'Failed to save product.',
      )
    }
  }

  const toggleActive = async (p) => {
    try {
      await updateProduct(p.id, { is_active: !p.is_active })
      loadProducts()
    } catch {
      setError('Failed to update product status.')
    }
  }

  const categoryOptions = categories.map((c) => ({ value: c.id, label: c.name }))
  const supplierOptions = suppliers.map((s) => ({ value: s.id, label: s.name }))

  const columns = [
    { key: 'sku', label: 'SKU' },
    { key: 'name', label: 'Name' },
    { key: 'category_name', label: 'Category' },
    { key: 'supplier_name', label: 'Supplier' },
    { key: 'current_stock', label: 'Stock' },
    { key: 'cost_price', label: 'Cost', render: (r) => `$${r.cost_price}` },
    { key: 'selling_price', label: 'Price', render: (r) => `$${r.selling_price}` },
    { key: 'unit', label: 'Unit' },
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
        title="Products"
        subtitle="Manage inventory items."
        action={isOwner && (
          <Button onClick={openCreate}>{showForm && !editing ? 'Cancel' : 'Add Product'}</Button>
        )}
      />

      <Alert type="error" message={error} />
      <Alert type="success" message={success} />

      <div className="mb-4 grid gap-3 rounded-xl border border-slate-200 bg-white p-4 shadow-sm md:grid-cols-4">
        <Input
          id="search"
          placeholder="Search by name or SKU..."
          value={filters.search}
          onChange={(e) => setFilters({ ...filters, search: e.target.value })}
        />
        <Select
          id="filter-category"
          placeholder="All categories"
          options={categoryOptions}
          value={filters.category}
          onChange={(e) => setFilters({ ...filters, category: e.target.value })}
        />
        <Select
          id="filter-supplier"
          placeholder="All suppliers"
          options={supplierOptions}
          value={filters.supplier}
          onChange={(e) => setFilters({ ...filters, supplier: e.target.value })}
        />
        <Select
          id="filter-active"
          placeholder="All statuses"
          options={[
            { value: 'true', label: 'Active' },
            { value: 'false', label: 'Inactive' },
          ]}
          value={filters.is_active}
          onChange={(e) => setFilters({ ...filters, is_active: e.target.value })}
        />
      </div>

      {showForm && isOwner && (
        <form onSubmit={handleSubmit} className="mb-6 grid max-w-3xl gap-4 rounded-xl border border-slate-200 bg-white p-5 shadow-sm md:grid-cols-2">
          <Input id="sku" label="SKU" required value={form.sku} onChange={(e) => setForm({ ...form, sku: e.target.value })} disabled={!!editing} />
          <Input id="name" label="Name" required value={form.name} onChange={(e) => setForm({ ...form, name: e.target.value })} />
          <Select id="category" label="Category" required options={categoryOptions} value={form.category} onChange={(e) => setForm({ ...form, category: e.target.value })} />
          <Select id="supplier" label="Supplier" required options={supplierOptions} value={form.supplier} onChange={(e) => setForm({ ...form, supplier: e.target.value })} />
          <Input id="cost_price" label="Cost Price" type="number" step="0.01" min="0" required value={form.cost_price} onChange={(e) => setForm({ ...form, cost_price: e.target.value })} />
          <Input id="selling_price" label="Selling Price" type="number" step="0.01" min="0" required value={form.selling_price} onChange={(e) => setForm({ ...form, selling_price: e.target.value })} />
          {editing && (
            <p className="text-sm text-slate-500 md:col-span-2">
              Current stock: {editing.current_stock} — stock is updated through sales and purchase orders only.
            </p>
          )}
          {!editing && (
            <p className="text-sm text-slate-500 md:col-span-2">
              New products start with zero stock. Record sales or receive purchase orders to adjust inventory.
            </p>
          )}
          <Select id="unit" label="Unit" options={UNIT_OPTIONS} value={form.unit} onChange={(e) => setForm({ ...form, unit: e.target.value })} />
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
        <p className="text-sm text-slate-500">Loading products...</p>
      ) : (
        <DataTable columns={columns} data={products} emptyMessage="No products yet." />
      )}
    </div>
  )
}
