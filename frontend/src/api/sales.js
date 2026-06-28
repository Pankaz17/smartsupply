import axiosClient from './axiosClient'

const unwrap = (data) => data.results ?? data

export const getSales = async (params) => {
  const { data } = await axiosClient.get('/sales/', { params })
  return unwrap(data)
}

export const createSale = async (payload) => {
  const { data } = await axiosClient.post('/sales/', payload)
  return data
}
