import { useCallback, useEffect, useState } from 'react'
import { getProducts } from '../api/products'
import { createSale, getSales } from '../api/sales'
import PageHeader from '../components/layout/PageHeader'
import Alert from '../components/ui/Alert'
import Button from '../components/ui/Button'
import DataTable from '../components/ui/DataTable'
import Input from '../components/ui/Input'
import Select from '../components/ui/Select'

export default function SalesPage() {
  const [products, setProducts] = useState([])
  const [sales, setSales] = useState([])
  const [form, setForm] = useState({ product: '', quantity: 1, unit_price: '' })
  const [loading, setLoading] = useState(true)
  const [submitting, setSubmitting] = useState(false)
  const [error, setError] = useState('')
  const [success, setSuccess] = useState('')

  const loadSales = useCallback(() => {
    getSales()
      .then(setSales)
      .catch(() => setError('Failed to load sales.'))
      .finally(() => setLoading(false))
  }, [])

  useEffect(() => {
    getProducts({ is_active: true })
      .then(setProducts)
      .catch(() => setError('Failed to load products.'))
    loadSales()
  }, [loadSales])

  const selectedProduct = products.find((p) => String(p.id) === String(form.product))

  useEffect(() => {
    if (selectedProduct && !form.unit_price) {
      setForm((prev) => ({ ...prev, unit_price: selectedProduct.selling_price }))
    }
  }, [selectedProduct, form.unit_price])

  const totalAmount = form.quantity && form.unit_price
    ? (Number(form.quantity) * Number(form.unit_price)).toFixed(2)
    : '0.00'

  const handleProductChange = (e) => {
    const productId = e.target.value
    const product = products.find((p) => String(p.id) === productId)
    setForm({
      product: productId,
      quantity: 1,
      unit_price: product ? product.selling_price : '',
    })
  }

  const handleSubmit = async (e) => {
    e.preventDefault()
    setError('')
    setSuccess('')
    setSubmitting(true)
    try {
      await createSale({
        product: Number(form.product),
        quantity: Number(form.quantity),
        unit_price: form.unit_price,
      })
      setSuccess('Sale recorded successfully.')
      setForm({ product: '', quantity: 1, unit_price: '' })
      getProducts({ is_active: true }).then(setProducts)
      loadSales()
    } catch (err) {
      const data = err.response?.data
      setError(data?.quantity?.[0] || data?.product?.[0] || data?.detail || 'Failed to record sale.')
    } finally {
      setSubmitting(false)
    }
  }

  const productOptions = products
    .filter((p) => p.current_stock > 0)
    .map((p) => ({
      value: p.id,
      label: `${p.sku} — ${p.name} (stock: ${p.current_stock})`,
    }))

  const columns = [
    { key: 'created_at', label: 'Date', render: (r) => new Date(r.created_at).toLocaleString() },
    { key: 'product_sku', label: 'SKU' },
    { key: 'product_name', label: 'Product' },
    { key: 'quantity', label: 'Qty' },
    { key: 'unit_price', label: 'Unit Price', render: (r) => `$${r.unit_price}` },
    { key: 'total_amount', label: 'Total', render: (r) => `$${r.total_amount}` },
    { key: 'recorded_by_name', label: 'Recorded By' },
  ]

  return (
    <div>
      <PageHeader title="Record Sale" subtitle="Log a sale and update stock automatically." />

      <Alert type="error" message={error} />
      <Alert type="success" message={success} />

      <form onSubmit={handleSubmit} className="mb-8 max-w-lg space-y-4 rounded-xl border border-slate-200 bg-white p-5 shadow-sm">
        <Select
          id="product"
          label="Product"
          required
          placeholder="Select a product"
          options={productOptions}
          value={form.product}
          onChange={handleProductChange}
        />
        {selectedProduct && (
          <p className="text-xs text-slate-500">
            Available stock: {selectedProduct.current_stock} {selectedProduct.unit}
          </p>
        )}
        <Input
          id="quantity"
          label="Quantity"
          type="number"
          min={1}
          max={selectedProduct?.current_stock || undefined}
          required
          value={form.quantity}
          onChange={(e) => setForm({ ...form, quantity: e.target.value })}
        />
        <Input
          id="unit_price"
          label="Unit Price"
          type="number"
          step="0.01"
          min="0"
          required
          value={form.unit_price}
          onChange={(e) => setForm({ ...form, unit_price: e.target.value })}
        />
        <div className="rounded-lg bg-slate-50 px-4 py-3">
          <span className="text-sm text-slate-500">Total Amount: </span>
          <span className="text-lg font-bold text-slate-900">${totalAmount}</span>
        </div>
        <Button type="submit" disabled={submitting || !form.product}>
          {submitting ? 'Recording...' : 'Record Sale'}
        </Button>
      </form>

      <h2 className="mb-3 text-lg font-semibold text-slate-900">Recent Sales</h2>
      {loading ? (
        <p className="text-sm text-slate-500">Loading sales...</p>
      ) : (
        <DataTable columns={columns} data={sales} emptyMessage="No sales recorded yet." />
      )}
    </div>
  )
}
