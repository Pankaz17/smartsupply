import axiosClient from './axiosClient'

const unwrap = (data) => data.results ?? data

export const getDeadStock = async (params) => {
  const { data } = await axiosClient.get('/dead-stock/', { params })
  return unwrap(data)
}

export const getSupplierAnalytics = async () => {
  const { data } = await axiosClient.get('/supplier-analytics/')
  return unwrap(data)
}

export const getSeasonalEvents = async () => {
  const { data } = await axiosClient.get('/seasonal-events/')
  return unwrap(data)
}

export const createSeasonalEvent = async (payload) => {
  const { data } = await axiosClient.post('/seasonal-events/', payload)
  return data
}

export const updateSeasonalEvent = async (id, payload) => {
  const { data } = await axiosClient.patch(`/seasonal-events/${id}/`, payload)
  return data
}

export const runAnalytics = async () => {
  const { data } = await axiosClient.post('/analytics/run/')
  return data
}

export const getDemandForecasts = async (params) => {
  const { data } = await axiosClient.get('/analytics/forecast/', { params })
  return Array.isArray(data) ? data : unwrap(data)
}

export const refreshDemandForecasts = async () => {
  const { data } = await axiosClient.post('/analytics/forecast/refresh/')
  return data
}

export function performanceBadge(onTimeRate, avgDelay) {
  if (onTimeRate >= 90 && avgDelay <= 1) return { label: 'Excellent', className: 'bg-green-100 text-green-700' }
  if (onTimeRate >= 70 && avgDelay <= 3) return { label: 'Good', className: 'bg-blue-100 text-blue-700' }
  return { label: 'Poor', className: 'bg-red-100 text-red-700' }
}
