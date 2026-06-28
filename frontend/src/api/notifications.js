import axiosClient from './axiosClient'

const unwrap = (data) => data.results ?? data

export const getNotifications = async (params) => {
  const { data } = await axiosClient.get('/notifications/', { params })
  return data
}

export const getUnreadCount = async () => {
  const { data } = await axiosClient.get('/notifications/unread-count/')
  return data.unread_count
}

export const markNotificationRead = async (id) => {
  const { data } = await axiosClient.post(`/notifications/${id}/read/`)
  return data
}

export const markAllNotificationsRead = async () => {
  const { data } = await axiosClient.post('/notifications/mark-all-read/')
  return data
}

export const NOTIFICATION_TYPE_LABELS = {
  LOW_STOCK: 'Low Stock',
  OUT_OF_STOCK: 'Out of Stock',
  DEAD_STOCK: 'Dead Stock',
  SUPPLIER_DELAY: 'Supplier Delay',
  REORDER_RECOMMENDATION: 'Reorder Recommendation',
}
