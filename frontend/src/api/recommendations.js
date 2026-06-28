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
