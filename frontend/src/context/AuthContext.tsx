import { useState, useEffect, ReactNode } from 'react'
import { AuthContext } from './auth-context'
import { User, AuthResponse } from '@/types'
import { authApi } from '@/services/api'

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null)
  const [token, setToken] = useState<string | null>(null)
  const [isLoading, setIsLoading] = useState(true)

  useEffect(() => {
    const storedToken = localStorage.getItem('token')
    const storedUser = localStorage.getItem('user')

    if (storedToken && storedUser) {
      setToken(storedToken)
      const parsedUser = JSON.parse(storedUser)
      setUser({ ...parsedUser, role: parsedUser.role || 'patient' })
    }
    setIsLoading(false)
  }, [])

  const login = async (email: string, password: string) => {
    const data = await authApi.login(email, password) as AuthResponse
    localStorage.setItem('token', data.access_token)
    localStorage.setItem('user', JSON.stringify(data.user))
    setToken(data.access_token)
    setUser(data.user)
    return data.user
  }

  const register = async (name: string, email: string, password: string) => {
    const data = await authApi.register(name, email, password) as AuthResponse
    localStorage.setItem('token', data.access_token)
    localStorage.setItem('user', JSON.stringify(data.user))
    setToken(data.access_token)
    setUser(data.user)
    return data.user
  }

  const logout = () => {
    localStorage.removeItem('token')
    localStorage.removeItem('user')
    setToken(null)
    setUser(null)
  }

  const updateUser = (updatedUser: User) => {
    localStorage.setItem('user', JSON.stringify(updatedUser))
    setUser(updatedUser)
  }

  return (
    <AuthContext.Provider
      value={{
        user,
        token,
        isAuthenticated: !!token,
        isLoading,
        login,
        register,
        updateUser,
        logout,
      }}
    >
      {children}
    </AuthContext.Provider>
  )
}

export default AuthProvider
