import { useCallback, useEffect, useState } from 'react'
import { getBusinessSettings } from '../api/auth'
import {
  approveRecommendation,
  dismissRecommendation,
  exportProfitAdvisorAnalysis,
  generateRecommendations,
  getProfitAdvisorAnalysis,
  getRecommendations,
  runProfitAdvisorAnalysis,
} from '../api/recommendations'
import ProfitAdvisorModal from '../components/recommendations/ProfitAdvisorModal'
import ProfitAdvisorPanel from '../components/recommendations/ProfitAdvisorPanel'
import PageHeader from '../components/layout/PageHeader'
import Alert from '../components/ui/Alert'
import Button from '../components/ui/Button'
import ConfirmationDialog from '../components/ui/ConfirmationDialog'
import DataTable from '../components/ui/DataTable'
import Select from '../components/ui/Select'
import StatusBadge from '../components/ui/StatusBadge'
import OperationalPriorityBadge from '../components/ui/OperationalPriorityBadge'
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
  const [currency, setCurrency] = useState('USD')
  const [showAdvisorModal, setShowAdvisorModal] = useState(false)
  const [advisorAnalysis, setAdvisorAnalysis] = useState(null)
  const [analyzing, setAnalyzing] = useState(false)
  const [exporting, setExporting] = useState(false)
  const [pendingConfirm, setPendingConfirm] = useState(null)

  const load = useCallback(() => {
    setLoading(true)
    const params = {}
    if (statusFilter) params.status = statusFilter
    getRecommendations(params)
      .then(setRecommendations)
      .catch(() => setError('Failed to load recommendations.'))
      .finally(() => setLoading(false))
  }, [statusFilter])

  const loadAdvisor = useCallback(() => {
    getProfitAdvisorAnalysis()
      .then((data) => {
        if (data.has_analysis) {
          setAdvisorAnalysis(data)
        }
      })
      .catch(() => {})
  }, [])

  useEffect(() => {
    getBusinessSettings().then((s) => setCurrency(s.currency || 'USD')).catch(() => {})
    loadAdvisor()
  }, [loadAdvisor])

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

  const handleAnalyze = async (budget) => {
    setAnalyzing(true)
    setError('')
    try {
      const result = await runProfitAdvisorAnalysis(budget)
      setAdvisorAnalysis(result)
      setShowAdvisorModal(false)
      setSuccess('Profit Advisor analysis complete.')
    } catch (err) {
      setError(err.response?.data?.budget?.[0] || err.response?.data?.detail || 'Analysis failed.')
    } finally {
      setAnalyzing(false)
    }
  }

  const handleExport = async (format) => {
    setExporting(true)
    try {
      await exportProfitAdvisorAnalysis(format)
    } catch {
      setError('Export failed. Run an analysis first.')
    } finally {
      setExporting(false)
    }
  }

  const handleApprove = async (id) => {
    setActing(id)
    setError('')
    setSuccess('')
    try {
      const result = await approveRecommendation(id)
      setSuccess(`Approved. Draft PO ${result.po_number} created.`)
      setPendingConfirm(null)
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
      setPendingConfirm(null)
      load()
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to dismiss recommendation.')
    } finally {
      setActing(null)
    }
  }

  const handleConfirmAction = () => {
    if (!pendingConfirm) return
    if (pendingConfirm.action === 'approve') {
      handleApprove(pendingConfirm.id)
    } else {
      handleDismiss(pendingConfirm.id)
    }
  }

  const columns = [
    { key: 'product_name', label: 'Product' },
    {
      key: 'priority_level',
      label: 'Priority',
      render: (r) => <OperationalPriorityBadge level={r.priority_level} />,
    },
    { key: 'supplier_name', label: 'Supplier' },
    { key: 'current_stock', label: 'Current Stock' },
    { key: 'recommended_quantity', label: 'Recommended Qty' },
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
              onClick={() => setPendingConfirm({ action: 'approve', id: r.id })}
              className="text-sm font-medium text-green-600 hover:text-green-700 disabled:opacity-50"
            >
              Approve
            </button>
            <button
              type="button"
              disabled={acting === r.id}
              onClick={() => setPendingConfirm({ action: 'dismiss', id: r.id })}
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
        subtitle="Review suggestions before creating purchase orders. You always decide."
        action={isOwner && (
          <div className="flex flex-wrap gap-2">
            <Button variant="secondary" onClick={() => setShowAdvisorModal(true)}>
              Prioritize by Profit
            </Button>
            <Button onClick={handleGenerate}>Generate Recommendations</Button>
          </div>
        )}
      />

      <Alert type="error" message={error} />
      <Alert type="success" message={success} />

      {advisorAnalysis && (
        <ProfitAdvisorPanel
          analysis={advisorAnalysis}
          currency={advisorAnalysis.currency || currency}
          onExport={handleExport}
          exporting={exporting}
          isOwner={isOwner}
          onRunAgain={() => isOwner && setShowAdvisorModal(true)}
        />
      )}

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
          emptyMessage="Inventory levels look healthy. No products need reordering today."
        />
      )}

      {showAdvisorModal && isOwner && (
        <ProfitAdvisorModal
          currency={currency}
          onClose={() => setShowAdvisorModal(false)}
          onAnalyze={handleAnalyze}
          analyzing={analyzing}
        />
      )}

      <ConfirmationDialog
        open={pendingConfirm?.action === 'approve'}
        title="Approve Recommendation"
        confirmLabel="Approve"
        onClose={() => setPendingConfirm(null)}
        onConfirm={handleConfirmAction}
        confirming={acting === pendingConfirm?.id}
      >
        <p>
          This will create a Draft Purchase Order for the recommended product.
        </p>
        <p className="mt-2">
          No inventory will be updated until the purchase order is received.
        </p>
      </ConfirmationDialog>

      <ConfirmationDialog
        open={pendingConfirm?.action === 'dismiss'}
        title="Dismiss Recommendation"
        confirmLabel="Dismiss"
        confirmVariant="danger"
        onClose={() => setPendingConfirm(null)}
        onConfirm={handleConfirmAction}
        confirming={acting === pendingConfirm?.id}
      >
        <p>This recommendation will be marked as dismissed.</p>
        <p className="mt-2">
          You can generate recommendations again later if needed.
        </p>
      </ConfirmationDialog>
    </div>
  )
}
