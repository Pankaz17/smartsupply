import axiosClient from './axiosClient'

function buildParams(dateRange) {
  const params = {}
  if (dateRange.mode === 'custom' && dateRange.startDate && dateRange.endDate) {
    params.start_date = dateRange.startDate
    params.end_date = dateRange.endDate
  } else if (dateRange.range) {
    params.range = dateRange.range
  }
  return params
}

export function getReportsOverview() {
  return axiosClient.get('/reports/').then((r) => r.data)
}

export function getInventoryReport(dateRange = { range: '30d' }) {
  return axiosClient.get('/reports/inventory/', { params: buildParams(dateRange) }).then((r) => r.data)
}

export function getSalesReport(dateRange = { range: '30d' }) {
  return axiosClient.get('/reports/sales/', { params: buildParams(dateRange) }).then((r) => r.data)
}

export function getDeadStockReport(dateRange = { range: '30d' }) {
  return axiosClient.get('/reports/dead-stock/', { params: buildParams(dateRange) }).then((r) => r.data)
}

export function getSupplierReport(dateRange = { range: '30d' }) {
  return axiosClient.get('/reports/suppliers/', { params: buildParams(dateRange) }).then((r) => r.data)
}

export function getRecommendationsReport(dateRange = { range: '30d' }) {
  return axiosClient.get('/reports/recommendations/', { params: buildParams(dateRange) }).then((r) => r.data)
}

export function getDemandForecastReport(dateRange = { range: '30d' }) {
  return axiosClient.get('/reports/demand-forecast/', { params: buildParams(dateRange) }).then((r) => r.data)
}

export async function exportReport(reportKey, format, dateRange = { range: '30d' }) {
  const params = { export_format: format, ...buildParams(dateRange) }
  const response = await axiosClient.get(`/reports/${reportKey}/export/`, {
    params,
    responseType: 'blob',
  })

  const ext = format === 'xlsx' ? 'xlsx' : 'csv'
  const mime = format === 'xlsx'
    ? 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    : 'text/csv'

  const blob = new Blob([response.data], { type: mime })
  const url = window.URL.createObjectURL(blob)
  const link = document.createElement('a')
  link.href = url
  link.download = `${reportKey.replace('-', '_')}_report.${ext}`
  document.body.appendChild(link)
  link.click()
  link.remove()
  window.URL.revokeObjectURL(url)
}
