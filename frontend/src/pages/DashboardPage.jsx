import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { getBusinessSettings } from '../api/auth'
import { getDashboard } from '../api/dashboard'
import Alert from '../components/ui/Alert'
import DataTable from '../components/ui/DataTable'
import PageHeader from '../components/layout/PageHeader'
import PriorityBadge from '../components/ui/PriorityBadge'
import { useAuth } from '../context/AuthContext'

export default function DashboardPage() {
  const { user } = useAuth()
  const [settings, setSettings] = useState(null)
  const [dashboard, setDashboard] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  useEffect(() => {
    setError('')
    Promise.all([getBusinessSettings(), getDashboard()])
      .then(([settingsData, dashboardData]) => {
        setSettings(settingsData)
        setDashboard(dashboardData)
      })
      .catch(() => setError('Failed to load dashboard data. Please refresh the page.'))
      .finally(() => setLoading(false))
  }, [])

  const currency = settings?.currency || 'USD'

  const formatMoney = (value) => {
    const num = Number(value || 0)
    return new Intl.NumberFormat('en-US', { style: 'currency', currency }).format(num)
  }

  const salesColumns = [
    { key: 'created_at', label: 'Date', render: (r) => new Date(r.created_at).toLocaleString() },
    { key: 'product_name', label: 'Product' },
    { key: 'quantity', label: 'Qty' },
    { key: 'total_amount', label: 'Total', render: (r) => formatMoney(r.total_amount) },
    { key: 'recorded_by_name', label: 'Recorded By' },
  ]

  const recommendationColumns = [
    { key: 'product_name', label: 'Product' },
    { key: 'supplier_name', label: 'Supplier' },
    { key: 'current_stock', label: 'Stock' },
    {
      key: 'priority_score',
      label: 'Priority Score',
      render: (r) => Number(r.priority_score || 0).toFixed(2),
    },
    {
      key: 'priority_level',
      label: 'Priority',
      render: (r) => <PriorityBadge level={r.priority_level} />,
    },
    { key: 'recommended_quantity', label: 'Qty' },
    { key: 'status', label: 'Status', render: (r) => <span className="capitalize">{r.status}</span> },
  ]

  const topPriorityColumns = [
    { key: 'product_name', label: 'Product' },
    {
      key: 'priority_level',
      label: 'Priority Level',
      render: (r) => <PriorityBadge level={r.priority_level} />,
    },
    {
      key: 'priority_score',
      label: 'Priority Score',
      render: (r) => Number(r.priority_score || 0).toFixed(2),
    },
  ]

  const poColumns = [
    { key: 'po_number', label: 'PO Number' },
    { key: 'supplier_name', label: 'Supplier' },
    { key: 'status', label: 'Status', render: (r) => <span className="capitalize">{r.status}</span> },
    { key: 'expected_delivery_date', label: 'Expected', render: (r) => r.expected_delivery_date || '—' },
  ]

  const notificationColumns = [
    {
      key: 'notification_type',
      label: 'Type',
      render: (r) => r.notification_type.replace(/_/g, ' '),
    },
    { key: 'title', label: 'Title' },
    {
      key: 'created_at',
      label: 'When',
      render: (r) => new Date(r.created_at).toLocaleString(),
    },
    {
      key: 'is_read',
      label: 'Status',
      render: (r) => (r.is_read ? 'Read' : 'Unread'),
    },
  ]

  return (
    <div>
      <PageHeader
        title={`Welcome, ${user?.full_name || 'there'}`}
        subtitle={
          settings
            ? `${settings.store_name} · ${settings.currency}`
            : 'Your smart inventory assistant'
        }
      />

      <Alert type="error" message={error} />

      {loading ? (
        <p className="text-sm text-slate-500">Loading dashboard...</p>
      ) : (
        <>
          <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
            <DashboardCard title="Total Products" value={dashboard?.total_products ?? 0} />
            <DashboardCard title="Active Products" value={dashboard?.active_products ?? 0} />
            <DashboardCard title="Total Suppliers" value={dashboard?.total_suppliers ?? 0} />
            <DashboardCard title="Inventory Value" value={formatMoney(dashboard?.inventory_value)} />
            <DashboardCard title="Out of Stock" value={dashboard?.out_of_stock_products ?? 0} highlight={dashboard?.out_of_stock_products > 0} />
            <DashboardCard title="Recent Sales (7 days)" value={dashboard?.recent_sales_count ?? 0} />
            <DashboardCard
              title="Pending Recommendations"
              value={dashboard?.pending_recommendations ?? 0}
              highlight={dashboard?.pending_recommendations > 0}
              link="/recommendations"
            />
            <DashboardCard
              title="Draft Purchase Orders"
              value={dashboard?.draft_purchase_orders ?? 0}
              link="/purchase-orders"
            />
            <DashboardCard
              title="Ordered Purchase Orders"
              value={dashboard?.ordered_purchase_orders ?? 0}
              link="/purchase-orders"
            />
            <DashboardCard
              title="Dead Stock Items"
              value={dashboard?.dead_stock_items ?? 0}
              highlight={dashboard?.dead_stock_items > 0}
              link="/dead-stock"
            />
            <DashboardCard
              title="Critical Dead Stock"
              value={dashboard?.critical_dead_stock ?? 0}
              highlight={dashboard?.critical_dead_stock > 0}
              link="/dead-stock"
            />
            <DashboardCard
              title="Suppliers With Delays"
              value={dashboard?.suppliers_with_delays ?? 0}
              highlight={dashboard?.suppliers_with_delays > 0}
              link="/supplier-analytics"
            />
            <DashboardCard
              title="Active Seasonal Events"
              value={dashboard?.active_seasonal_events ?? 0}
              link="/seasonal-events"
            />
            <DashboardCard
              title="Unread Notifications"
              value={dashboard?.unread_notifications ?? 0}
              highlight={dashboard?.unread_notifications > 0}
              link="/notifications"
            />
          </div>

          {dashboard?.dashboard_alerts?.length > 0 && (
            <div className="mt-6 rounded-xl border border-amber-200 bg-amber-50 p-5">
              <h2 className="mb-3 text-sm font-semibold text-amber-900">Alerts</h2>
              <ul className="space-y-2">
                {dashboard.dashboard_alerts.map((alert) => (
                  <li key={alert} className="flex items-center gap-2 text-sm text-amber-800">
                    <span className="h-1.5 w-1.5 shrink-0 rounded-full bg-amber-500" />
                    {alert}
                  </li>
                ))}
              </ul>
            </div>
          )}

          {(dashboard?.top_restock_priorities?.length > 0) && (
            <div className="mt-8 rounded-xl border border-green-100 bg-green-50/50 p-6">
              <div className="mb-4 flex items-center justify-between">
                <h2 className="text-lg font-semibold text-slate-900">Top Restock Priorities</h2>
                <Link to="/recommendations" className="text-sm text-brand-600 hover:text-brand-700">View all</Link>
              </div>
              <DataTable
                columns={topPriorityColumns}
                data={dashboard.top_restock_priorities}
                rowKey={(r) => r.product_name}
                emptyMessage="No pending recommendations."
              />
            </div>
          )}

          <div className="mt-8 grid gap-8 lg:grid-cols-2">
            <div>
              <div className="mb-3 flex items-center justify-between">
                <h2 className="text-lg font-semibold text-slate-900">Recent Recommendations</h2>
                <Link to="/recommendations" className="text-sm text-brand-600 hover:text-brand-700">View all</Link>
              </div>
              <DataTable
                columns={recommendationColumns}
                data={dashboard?.recent_recommendations ?? []}
                emptyMessage="No recommendations yet."
              />
            </div>
            <div>
              <div className="mb-3 flex items-center justify-between">
                <h2 className="text-lg font-semibold text-slate-900">Recent Purchase Orders</h2>
                <Link to="/purchase-orders" className="text-sm text-brand-600 hover:text-brand-700">View all</Link>
              </div>
              <DataTable
                columns={poColumns}
                data={dashboard?.recent_purchase_orders ?? []}
                emptyMessage="No purchase orders yet."
              />
            </div>
          </div>

          <div className="mt-8">
            <div className="mb-3 flex items-center justify-between">
              <h2 className="text-lg font-semibold text-slate-900">Recent Notifications</h2>
              <Link to="/notifications" className="text-sm text-brand-600 hover:text-brand-700">View all</Link>
            </div>
            <DataTable
              columns={notificationColumns}
              data={dashboard?.recent_notifications ?? []}
              emptyMessage="No notifications yet."
            />
          </div>

          <div className="mt-8">
            <h2 className="mb-3 text-lg font-semibold text-slate-900">Recent Sales</h2>
            <DataTable
              columns={salesColumns}
              data={dashboard?.recent_sales ?? []}
              emptyMessage="No recent sales."
            />
          </div>

          <div className="mt-8 rounded-xl border border-slate-200 bg-white p-6">
            <div className="mb-4 flex items-center justify-between">
              <h2 className="text-lg font-semibold text-slate-900">Reports</h2>
              <Link to="/reports" className="text-sm text-brand-600 hover:text-brand-700">View all</Link>
            </div>
            <ul className="grid gap-2 sm:grid-cols-2 lg:grid-cols-3">
              <ReportLink to="/reports/inventory" label="Inventory Report" />
              <ReportLink to="/reports/sales" label="Sales Report" />
              <ReportLink to="/reports/dead-stock" label="Dead Stock Report" />
              <ReportLink to="/reports/suppliers" label="Supplier Report" />
              <ReportLink to="/reports/recommendations" label="Recommendation Report" />
            </ul>
          </div>
        </>
      )}

      <div className="mt-8 rounded-xl border border-brand-100 bg-brand-50 p-6">
        <h2 className="font-semibold text-brand-900">Core Principle</h2>
        <p className="mt-2 text-sm text-brand-800">
          SmartSupply is an assistant, not an autopilot. Recommendations require your
          approval — the system never makes purchasing decisions automatically.
        </p>
      </div>
    </div>
  )
}

function DashboardCard({ title, value, highlight = false, link }) {
  const content = (
    <div className={`rounded-xl border bg-white p-5 shadow-sm ${highlight ? 'border-amber-200' : 'border-slate-200'}`}>
      <div className="text-sm font-medium text-slate-500">{title}</div>
      <div className={`mt-2 text-2xl font-bold ${highlight ? 'text-amber-600' : 'text-slate-900'}`}>{value}</div>
    </div>
  )

  if (link) {
    return <Link to={link} className="block transition-opacity hover:opacity-90">{content}</Link>
  }
  return content
}

function ReportLink({ to, label }) {
  return (
    <li>
      <Link to={to} className="block rounded-lg px-3 py-2 text-sm font-medium text-brand-600 hover:bg-brand-50">
        {label}
      </Link>
    </li>
  )
}
