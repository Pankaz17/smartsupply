import axiosClient from './axiosClient'

const unwrap = (data) => data.results ?? data

export const getProducts = async (params) => {
  const { data } = await axiosClient.get('/products/', { params })
  return unwrap(data)
}

export const createProduct = async (payload) => {
  const { data } = await axiosClient.post('/products/', payload)
  return data
}

export const updateProduct = async (id, payload) => {
  const { data } = await axiosClient.patch(`/products/${id}/`, payload)
  return data
}
