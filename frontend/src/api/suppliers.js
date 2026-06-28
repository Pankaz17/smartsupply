import axiosClient from './axiosClient'

const unwrap = (data) => data.results ?? data

export const getSuppliers = async (params) => {
  const { data } = await axiosClient.get('/suppliers/', { params })
  return unwrap(data)
}

export const createSupplier = async (payload) => {
  const { data } = await axiosClient.post('/suppliers/', payload)
  return data
}

export const updateSupplier = async (id, payload) => {
  const { data } = await axiosClient.patch(`/suppliers/${id}/`, payload)
  return data
}
