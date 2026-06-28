import axiosClient from './axiosClient'

const unwrap = (data) => data.results ?? data

export const getPurchaseOrders = async (params) => {
  const { data } = await axiosClient.get('/purchase-orders/', { params })
  return unwrap(data)
}

export const getPurchaseOrder = async (id) => {
  const { data } = await axiosClient.get(`/purchase-orders/${id}/`)
  return data
}

export const updatePurchaseOrderStatus = async (id, status, actualDeliveryDate = null) => {
  const payload = { status }
  if (actualDeliveryDate) {
    payload.actual_delivery_date = actualDeliveryDate
  }
  const { data } = await axiosClient.patch(`/purchase-orders/${id}/status/`, payload)
  return data
}
