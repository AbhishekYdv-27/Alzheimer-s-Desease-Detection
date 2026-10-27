import { useContext } from 'react'
import { AuthContext } from './auth-context'
import { User } from '@/types'

export function useAuth(): { user: User | null; token: string | null; isAuthenticated: boolean; isLoading: boolean; login: (email: string, password: string) => Promise<User>; register: (name: string, email: string, password: string) => Promise<User>; updateUser: (user: User) => void; logout: () => void } {
  const context = useContext(AuthContext)
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider')
  }
  return context
}