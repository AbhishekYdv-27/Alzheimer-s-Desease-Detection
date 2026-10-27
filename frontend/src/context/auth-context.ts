import { createContext } from 'react'
import { User } from '@/types'

interface AuthContextType {
  user: User | null
  token: string | null
  isAuthenticated: boolean
  isLoading: boolean
  login: (email: string, password: string) => Promise<User>
  register: (name: string, email: string, password: string) => Promise<User>
  updateUser: (user: User) => void
  logout: () => void
}

export const AuthContext = createContext<AuthContextType | undefined>(undefined)