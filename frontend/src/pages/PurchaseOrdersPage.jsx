import { useCallback, useEffect, useState } from 'react'
import {
  getPurchaseOrder,
  getPurchaseOrders,
  updatePurchaseOrderStatus,
} from '../api/purchaseOrders'
import PageHeader from '../components/layout/PageHeader'
import Alert from '../components/ui/Alert'
import Button from '../components/ui/Button'
import DataTable from '../components/ui/DataTable'
import Input from '../components/ui/Input'
import Select from '../components/ui/Select'
import { useAuth } from '../context/AuthContext'

const STATUS_OPTIONS = [
  { value: '', label: 'All statuses' },
  { value: 'draft', label: 'Draft' },
  { value: 'ordered', label: 'Ordered' },
  { value: 'received', label: 'Received' },
  { value: 'cancelled', label: 'Cancelled' },
]

const STATUS_STYLES = {
  draft: 'bg-slate-100 text-slate-700',
  ordered: 'bg-blue-100 text-blue-700',
  received: 'bg-green-100 text-green-700',
  cancelled: 'bg-red-100 text-red-600',
}

function todayISO() {
  return new Date().toISOString().slice(0, 10)
}

function formatDate(value) {
  return value || '—'
}

export default function PurchaseOrdersPage() {
  const { isOwner } = useAuth()
  const [orders, setOrders] = useState([])
  const [selected, setSelected] = useState(null)
  const [statusFilter, setStatusFilter] = useState('')
  const [loading, setLoading] = useState(true)
  const [detailLoading, setDetailLoading] = useState(false)
  const [error, setError] = useState('')
  const [success, setSuccess] = useState('')
  const [acting, setActing] = useState(false)
  const [showReceiveForm, setShowReceiveForm] = useState(false)
  const [actualDeliveryDate, setActualDeliveryDate] = useState(todayISO())

  const load = useCallback(() => {
    setLoading(true)
    const params = {}
    if (statusFilter) params.status = statusFilter
    getPurchaseOrders(params)
      .then(setOrders)
      .catch(() => setError('Failed to load purchase orders.'))
      .finally(() => setLoading(false))
  }, [statusFilter])

  useEffect(() => { load() }, [load])

  const openDetail = async (order) => {
    setDetailLoading(true)
    setShowReceiveForm(false)
    setError('')
    try {
      const detail = await getPurchaseOrder(order.id)
      setSelected(detail)
    } catch {
      setError('Failed to load purchase order details.')
    } finally {
      setDetailLoading(false)
    }
  }

  const handleStatusChange = async (newStatus, deliveryDate = null) => {
    if (!selected) return
    setActing(true)
    setError('')
    setSuccess('')
    try {
      const result = await updatePurchaseOrderStatus(
        selected.id,
        newStatus,
        deliveryDate,
      )
      setSelected(result.purchase_order)
      setSuccess(result.detail)
      setShowReceiveForm(false)
      load()
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to update status.')
    } finally {
      setActing(false)
    }
  }

  const openReceiveForm = () => {
    setActualDeliveryDate(todayISO())
    setShowReceiveForm(true)
    setError('')
  }

  const columns = [
    {
      key: 'po_number',
      label: 'PO Number',
      render: (r) => (
        <button
          type="button"
          onClick={() => openDetail(r)}
          className="font-medium text-brand-600 hover:text-brand-700"
        >
          {r.po_number}
        </button>
      ),
    },
    { key: 'supplier_name', label: 'Supplier' },
    {
      key: 'status',
      label: 'Status',
      render: (r) => (
        <span className={`rounded-full px-2 py-0.5 text-xs font-medium capitalize ${STATUS_STYLES[r.status]}`}>
          {r.status}
        </span>
      ),
    },
    {
      key: 'ordered_at',
      label: 'Ordered On',
      render: (r) => formatDate(r.ordered_at),
    },
    {
      key: 'expected_delivery_date',
      label: 'Expected Delivery',
      render: (r) => formatDate(r.expected_delivery_date),
    },
    {
      key: 'actual_delivery_date',
      label: 'Actual Delivery',
      render: (r) => formatDate(r.actual_delivery_date),
    },
    { key: 'item_count', label: 'Items' },
  ]

  return (
    <div>
      <PageHeader
        title="Purchase Orders"
        subtitle="Manage draft, ordered, and received purchase orders."
      />

      <Alert type="error" message={error} />
      <Alert type="success" message={success} />

      <div className="mb-4 max-w-xs">
        <Select
          id="po-status-filter"
          label="Filter by status"
          options={STATUS_OPTIONS}
          value={statusFilter}
          onChange={(e) => setStatusFilter(e.target.value)}
        />
      </div>

      <div className="grid gap-6 lg:grid-cols-3">
        <div className="lg:col-span-2">
          {loading ? (
            <p className="text-sm text-slate-500">Loading purchase orders...</p>
          ) : (
            <DataTable
              columns={columns}
              data={orders}
              emptyMessage="No purchase orders yet. Approve a recommendation to create one."
            />
          )}
        </div>

        <div className="rounded-xl border border-slate-200 bg-white p-5 shadow-sm">
          <h2 className="mb-4 text-lg font-semibold text-slate-900">Order Detail</h2>
          {detailLoading && <p className="text-sm text-slate-500">Loading...</p>}
          {!detailLoading && !selected && (
            <p className="text-sm text-slate-400">Select a purchase order to view details.</p>
          )}
          {selected && !detailLoading && (
            <div className="space-y-4">
              <div>
                <div className="text-xs text-slate-500">PO Number</div>
                <div className="font-semibold">{selected.po_number}</div>
              </div>
              <div>
                <div className="text-xs text-slate-500">Supplier</div>
                <div>{selected.supplier_name}</div>
              </div>
              <div>
                <div className="text-xs text-slate-500">Status</div>
                <span className={`mt-1 inline-block rounded-full px-2 py-0.5 text-xs font-medium capitalize ${STATUS_STYLES[selected.status]}`}>
                  {selected.status}
                </span>
              </div>
              <div className="grid grid-cols-1 gap-3 rounded-lg bg-slate-50 p-3 text-sm">
                <div>
                  <div className="text-xs text-slate-500">Ordered On</div>
                  <div className="font-medium">{formatDate(selected.ordered_at)}</div>
                </div>
                <div>
                  <div className="text-xs text-slate-500">Expected Delivery</div>
                  <div className="font-medium">{formatDate(selected.expected_delivery_date)}</div>
                </div>
                <div>
                  <div className="text-xs text-slate-500">Actual Delivery</div>
                  <div className="font-medium">{formatDate(selected.actual_delivery_date)}</div>
                </div>
              </div>
              {selected.notes && (
                <div>
                  <div className="text-xs text-slate-500">Notes</div>
                  <div className="text-sm">{selected.notes}</div>
                </div>
              )}

              <div>
                <div className="mb-2 text-xs font-medium text-slate-500">Line Items</div>
                <div className="space-y-2">
                  {selected.items?.map((item) => (
                    <div key={item.id} className="rounded-lg bg-slate-50 px-3 py-2 text-sm">
                      <div className="font-medium">{item.product_name}</div>
                      <div className="text-slate-500">
                        {item.quantity} × ${item.unit_cost} = ${item.total_cost}
                      </div>
                    </div>
                  ))}
                </div>
                <div className="mt-2 text-right text-sm font-semibold">
                  Total: ${selected.total_cost}
                </div>
              </div>

              {isOwner && (
                <div className="border-t border-slate-100 pt-4">
                  {showReceiveForm && selected.status === 'ordered' ? (
                    <div className="space-y-3 rounded-lg border border-slate-200 bg-white p-4">
                      <h3 className="text-sm font-semibold text-slate-900">Confirm Receipt</h3>
                      <Input
                        id="actual-delivery-date"
                        label="Actual Delivery Date"
                        type="date"
                        value={actualDeliveryDate}
                        onChange={(e) => setActualDeliveryDate(e.target.value)}
                      />
                      <div className="flex gap-2">
                        <Button
                          size="sm"
                          disabled={acting}
                          onClick={() => handleStatusChange('received', actualDeliveryDate)}
                        >
                          Confirm Receipt
                        </Button>
                        <Button
                          size="sm"
                          variant="secondary"
                          disabled={acting}
                          onClick={() => setShowReceiveForm(false)}
                        >
                          Cancel
                        </Button>
                      </div>
                    </div>
                  ) : (
                    <div className="flex flex-wrap gap-2">
                      {selected.status === 'draft' && (
                        <>
                          <Button size="sm" disabled={acting} onClick={() => handleStatusChange('ordered')}>
                            Move to Ordered
                          </Button>
                          <Button size="sm" variant="danger" disabled={acting} onClick={() => handleStatusChange('cancelled')}>
                            Cancel
                          </Button>
                        </>
                      )}
                      {selected.status === 'ordered' && (
                        <>
                          <Button size="sm" disabled={acting} onClick={openReceiveForm}>
                            Move to Received
                          </Button>
                          <Button size="sm" variant="danger" disabled={acting} onClick={() => handleStatusChange('cancelled')}>
                            Cancel
                          </Button>
                        </>
                      )}
                      {selected.status === 'received' && (
                        <p className="text-xs text-green-600">Stock has been updated.</p>
                      )}
                    </div>
                  )}
                </div>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
