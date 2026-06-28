import axios from 'axios'
import { clearAuthStorage, getAccessToken, getRefreshToken } from '../utils/storage'

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || '/api'

const axiosClient = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
})

function redirectToLogin() {
  clearAuthStorage()
  if (window.location.pathname !== '/login') {
    window.location.href = '/login'
  }
}

axiosClient.interceptors.request.use((config) => {
  const token = getAccessToken()
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

axiosClient.interceptors.response.use(
  (response) => response,
  async (error) => {
    const originalRequest = error.config

    if (error.response?.status === 401 && originalRequest && !originalRequest._retry) {
      originalRequest._retry = true
      const refreshToken = getRefreshToken()

      if (refreshToken && !originalRequest.url?.includes('/auth/refresh')) {
        try {
          const { data } = await axios.post(`${API_BASE_URL}/auth/refresh/`, {
            refresh: refreshToken,
          })
          localStorage.setItem('access_token', data.access)
          originalRequest.headers.Authorization = `Bearer ${data.access}`
          return axiosClient(originalRequest)
        } catch {
          redirectToLogin()
          return Promise.reject(error)
        }
      }

      redirectToLogin()
    }

    return Promise.reject(error)
  },
)

export default axiosClient
