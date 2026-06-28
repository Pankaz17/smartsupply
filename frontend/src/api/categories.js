import axiosClient from './axiosClient'

const unwrap = (data) => data.results ?? data

export const getCategories = async (params) => {
  const { data } = await axiosClient.get('/categories/', { params })
  return unwrap(data)
}

export const createCategory = async (payload) => {
  const { data } = await axiosClient.post('/categories/', payload)
  return data
}

export const updateCategory = async (id, payload) => {
  const { data } = await axiosClient.patch(`/categories/${id}/`, payload)
  return data
}
