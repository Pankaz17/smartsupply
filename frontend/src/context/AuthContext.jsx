import { createContext, useCallback, useContext, useEffect, useMemo, useState } from 'react'
import { getMe, login as apiLogin } from '../api/auth'
import { clearAuthStorage, getAccessToken, getStoredJson } from '../utils/storage'

const AuthContext = createContext(null)

export function AuthProvider({ children }) {
  const [user, setUser] = useState(() => getStoredJson('user'))
  const [loading, setLoading] = useState(true)

  const logout = useCallback(() => {
    clearAuthStorage()
    setUser(null)
  }, [])

  const login = useCallback(async (email, password) => {
    const data = await apiLogin(email, password)
    localStorage.setItem('access_token', data.access)
    localStorage.setItem('refresh_token', data.refresh)
    localStorage.setItem('user', JSON.stringify(data.user))
    setUser(data.user)
    return data.user
  }, [])

  useEffect(() => {
    const token = getAccessToken()
    if (!token) {
      clearAuthStorage()
      setUser(null)
      setLoading(false)
      return
    }

    getMe()
      .then((me) => {
        setUser(me)
        localStorage.setItem('user', JSON.stringify(me))
      })
      .catch(() => {
        clearAuthStorage()
        setUser(null)
      })
      .finally(() => setLoading(false))
  }, [logout])

  const value = useMemo(
    () => ({
      user,
      loading,
      isAuthenticated: Boolean(user),
      isOwner: user?.role === 'owner',
      isStaff: user?.role === 'staff',
      login,
      logout,
    }),
    [user, loading, login, logout],
  )

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>
}

export function useAuth() {
  const context = useContext(AuthContext)
  if (!context) {
    throw new Error('useAuth must be used within AuthProvider')
  }
  return context
}
