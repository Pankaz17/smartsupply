import axiosClient from './axiosClient'

export const login = async (email, password) => {
  const { data } = await axiosClient.post('/auth/login/', { email, password })
  return data
}

export const getMe = async () => {
  const { data } = await axiosClient.get('/auth/me/')
  return data
}

export const changePassword = async (currentPassword, newPassword) => {
  const { data } = await axiosClient.post('/auth/change-password/', {
    current_password: currentPassword,
    new_password: newPassword,
  })
  return data
}

export const getBusinessSettings = async () => {
  const { data } = await axiosClient.get('/settings/')
  return data
}

export const updateBusinessSettings = async (settings) => {
  const { data } = await axiosClient.patch('/settings/', settings)
  return data
}

export const getStaff = async () => {
  const { data } = await axiosClient.get('/staff/')
  return data
}

export const createStaff = async (staffData) => {
  const { data } = await axiosClient.post('/staff/', staffData)
  return data
}

export const updateStaff = async (id, staffData) => {
  const { data } = await axiosClient.patch(`/staff/${id}/`, staffData)
  return data
}
