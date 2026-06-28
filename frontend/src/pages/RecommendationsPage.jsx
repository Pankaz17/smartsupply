import { useCallback, useEffect, useState } from 'react'
import {
  approveRecommendation,
  dismissRecommendation,
  generateRecommendations,
  getRecommendations,
} from '../api/recommendations'
import PageHeader from '../components/layout/PageHeader'
import Alert from '../components/ui/Alert'
import Button from '../components/ui/Button'
import DataTable from '../components/ui/DataTable'
import PriorityBadge from '../components/ui/PriorityBadge'
import Select from '../components/ui/Select'
import StatusBadge from '../components/ui/StatusBadge'
import { useAuth } from '../context/AuthContext'

const STATUS_OPTIONS = [
  { value: '', label: 'All statuses' },
  { value: 'pending', label: 'Pending' },
  { value: 'approved', label: 'Approved' },
  { value: 'dismissed', label: 'Dismissed' },
]

export default function RecommendationsPage() {
  const { isOwner } = useAuth()
  const [recommendations, setRecommendations] = useState([])
  const [statusFilter, setStatusFilter] = useState('pending')
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [success, setSuccess] = useState('')
  const [acting, setActing] = useState(null)

  const load = useCallback(() => {
    setLoading(true)
    const params = {}
    if (statusFilter) params.status = statusFilter
    getRecommendations(params)
      .then(setRecommendations)
      .catch(() => setError('Failed to load recommendations.'))
      .finally(() => setLoading(false))
  }, [statusFilter])

  useEffect(() => { load() }, [load])

  const handleGenerate = async () => {
    setError('')
    setSuccess('')
    try {
      const result = await generateRecommendations()
      setSuccess(
        `Generated — created: ${result.created}, updated: ${result.updated}, skipped: ${result.skipped}.`,
      )
      load()
    } catch {
      setError('Failed to generate recommendations.')
    }
  }

  const handleApprove = async (id) => {
    setActing(id)
    setError('')
    setSuccess('')
    try {
      const result = await approveRecommendation(id)
      setSuccess(`Approved. Draft PO ${result.po_number} created.`)
      load()
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to approve recommendation.')
    } finally {
      setActing(null)
    }
  }

  const handleDismiss = async (id) => {
    setActing(id)
    setError('')
    setSuccess('')
    try {
      await dismissRecommendation(id)
      setSuccess('Recommendation dismissed.')
      load()
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to dismiss recommendation.')
    } finally {
      setActing(null)
    }
  }

  const formatMoney = (value) =>
    new Intl.NumberFormat('en-US', { style: 'currency', currency: 'USD' }).format(Number(value || 0))

  const formatScore = (value) => Number(value || 0).toFixed(2)

  const columns = [
    { key: 'product_name', label: 'Product' },
    { key: 'supplier_name', label: 'Supplier' },
    { key: 'current_stock', label: 'Current Stock' },
    {
      key: 'calculated_reorder_point',
      label: 'ROP',
      render: (r) => Number(r.calculated_reorder_point).toFixed(1),
    },
    { key: 'recommended_quantity', label: 'Recommended Qty' },
    {
      key: 'unit_profit',
      label: 'Unit Profit',
      render: (r) => formatMoney(r.unit_profit),
    },
    {
      key: 'priority_score',
      label: 'Priority Score',
      render: (r) => formatScore(r.priority_score),
    },
    {
      key: 'expected_restock_profit',
      label: 'Expected Restock Profit',
      render: (r) => formatMoney(r.expected_restock_profit),
    },
    {
      key: 'priority_level',
      label: 'Priority Level',
      render: (r) => <PriorityBadge level={r.priority_level} />,
    },
    {
      key: 'status',
      label: 'Status',
      render: (r) => (
        <StatusBadge
          active={r.status === 'pending'}
          activeLabel="Pending"
          inactiveLabel={r.status === 'approved' ? 'Approved' : 'Dismissed'}
        />
      ),
    },
  ]

  if (isOwner) {
    columns.push({
      key: 'actions',
      label: 'Actions',
      render: (r) => (
        r.status === 'pending' ? (
          <div className="flex gap-2">
            <button
              type="button"
              disabled={acting === r.id}
              onClick={() => handleApprove(r.id)}
              className="text-sm font-medium text-green-600 hover:text-green-700 disabled:opacity-50"
            >
              Approve
            </button>
            <button
              type="button"
              disabled={acting === r.id}
              onClick={() => handleDismiss(r.id)}
              className="text-sm font-medium text-slate-600 hover:text-slate-800 disabled:opacity-50"
            >
              Dismiss
            </button>
          </div>
        ) : (
          r.purchase_order_number ? (
            <span className="text-xs text-slate-500">{r.purchase_order_number}</span>
          ) : '—'
        )
      ),
    })
  }

  return (
    <div>
      <PageHeader
        title="Reorder Recommendations"
        subtitle="Review suggestions ranked by profit and demand. You always decide."
        action={isOwner && (
          <Button onClick={handleGenerate}>Generate Recommendations</Button>
        )}
      />

      <Alert type="error" message={error} />
      <Alert type="success" message={success} />

      <div className="mb-4 max-w-xs">
        <Select
          id="status-filter"
          label="Filter by status"
          options={STATUS_OPTIONS}
          value={statusFilter}
          onChange={(e) => setStatusFilter(e.target.value)}
        />
      </div>

      {loading ? (
        <p className="text-sm text-slate-500">Loading recommendations...</p>
      ) : (
        <DataTable
          columns={columns}
          data={recommendations}
          rowKey={(r) => r.id}
          emptyMessage="No recommendations found. Generate recommendations to get started."
        />
      )}
    </div>
  )
}
