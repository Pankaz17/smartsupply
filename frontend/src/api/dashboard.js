import axiosClient from './axiosClient'

export const getDashboard = async () => {
  const { data } = await axiosClient.get('/dashboard/')
  return data
}
