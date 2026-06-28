import { useCallback, useEffect, useState } from 'react'
import {
  getNotifications,
  markAllNotificationsRead,
  markNotificationRead,
  NOTIFICATION_TYPE_LABELS,
} from '../api/notifications'
import PageHeader from '../components/layout/PageHeader'
import Alert from '../components/ui/Alert'
import Button from '../components/ui/Button'
import DataTable from '../components/ui/DataTable'
import Select from '../components/ui/Select'
import StatusBadge from '../components/ui/StatusBadge'

const TYPE_OPTIONS = [
  { value: '', label: 'All types' },
  ...Object.entries(NOTIFICATION_TYPE_LABELS).map(([value, label]) => ({ value, label })),
]

const READ_OPTIONS = [
  { value: '', label: 'All statuses' },
  { value: 'false', label: 'Unread' },
  { value: 'true', label: 'Read' },
]

export default function NotificationsPage() {
  const [notifications, setNotifications] = useState([])
  const [typeFilter, setTypeFilter] = useState('')
  const [readFilter, setReadFilter] = useState('')
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [success, setSuccess] = useState('')

  const load = useCallback(() => {
    setLoading(true)
    const params = {}
    if (typeFilter) params.type = typeFilter
    if (readFilter !== '') params.is_read = readFilter
    getNotifications(params)
      .then((data) => setNotifications(data.results ?? data))
      .catch(() => setError('Failed to load notifications.'))
      .finally(() => setLoading(false))
  }, [typeFilter, readFilter])

  useEffect(() => { load() }, [load])

  const handleMarkRead = async (id) => {
    setError('')
    try {
      await markNotificationRead(id)
      setSuccess('Notification marked as read.')
      load()
    } catch {
      setError('Failed to mark notification as read.')
    }
  }

  const handleMarkAllRead = async () => {
    setError('')
    try {
      await markAllNotificationsRead()
      setSuccess('All notifications marked as read.')
      load()
    } catch {
      setError('Failed to mark all as read.')
    }
  }

  const columns = [
    {
      key: 'notification_type',
      label: 'Type',
      render: (r) => NOTIFICATION_TYPE_LABELS[r.notification_type] || r.notification_type,
    },
    { key: 'title', label: 'Title' },
    {
      key: 'message',
      label: 'Message',
      render: (r) => <span className="line-clamp-2 max-w-md">{r.message}</span>,
    },
    {
      key: 'created_at',
      label: 'Created At',
      render: (r) => new Date(r.created_at).toLocaleString(),
    },
    {
      key: 'is_read',
      label: 'Status',
      render: (r) => (
        <StatusBadge
          active={!r.is_read}
          activeLabel="Unread"
          inactiveLabel="Read"
        />
      ),
    },
    {
      key: 'actions',
      label: 'Actions',
      render: (r) => (
        !r.is_read ? (
          <button
            type="button"
            onClick={() => handleMarkRead(r.id)}
            className="text-sm font-medium text-brand-600 hover:text-brand-700"
          >
            Mark Read
          </button>
        ) : '—'
      ),
    },
  ]

  return (
    <div>
      <PageHeader
        title="Notifications"
        subtitle="Inventory alerts and operational updates."
        action={
          <Button variant="secondary" onClick={handleMarkAllRead}>
            Mark All Read
          </Button>
        }
      />

      <Alert type="error" message={error} />
      <Alert type="success" message={success} />

      <div className="mb-4 grid gap-3 md:grid-cols-2">
        <Select
          id="type-filter"
          label="Filter by type"
          options={TYPE_OPTIONS}
          value={typeFilter}
          onChange={(e) => setTypeFilter(e.target.value)}
        />
        <Select
          id="read-filter"
          label="Filter by status"
          options={READ_OPTIONS}
          value={readFilter}
          onChange={(e) => setReadFilter(e.target.value)}
        />
      </div>

      {loading ? (
        <p className="text-sm text-slate-500">Loading notifications...</p>
      ) : (
        <DataTable
          columns={columns}
          data={notifications}
          emptyMessage="No notifications yet."
        />
      )}
    </div>
  )
}
