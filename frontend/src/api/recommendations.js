import axiosClient from './axiosClient'

const unwrap = (data) => data.results ?? data

export const getRecommendations = async (params) => {
  const { data } = await axiosClient.get('/recommendations/', { params })
  return unwrap(data)
}

export const generateRecommendations = async () => {
  const { data } = await axiosClient.post('/recommendations/generate/')
  return data
}

export const approveRecommendation = async (id) => {
  const { data } = await axiosClient.post(`/recommendations/${id}/approve/`)
  return data
}

export const dismissRecommendation = async (id) => {
  const { data } = await axiosClient.post(`/recommendations/${id}/dismiss/`)
  return data
}

export const getProfitAdvisorAnalysis = async () => {
  const { data } = await axiosClient.get('/recommendations/profit-advisor/')
  return data
}

export const runProfitAdvisorAnalysis = async (budget) => {
  const { data } = await axiosClient.post('/recommendations/profit-advisor/', { budget })
  return data
}

export async function exportProfitAdvisorAnalysis(format) {
  const response = await axiosClient.get('/recommendations/profit-advisor/export/', {
    params: { export_format: format },
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
  link.download = `profit_advisor_analysis.${ext}`
  document.body.appendChild(link)
  link.click()
  link.remove()
  window.URL.revokeObjectURL(url)
}
