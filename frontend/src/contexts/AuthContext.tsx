'use client'

import { createContext, useContext, useEffect, useState, ReactNode } from 'react'
import { api } from '@/lib/api'

interface User {
  id: string
  email: string
  name: string
  email_verified: boolean
  is_admin: boolean
  oauth_provider?: string
  oauth_avatar_url?: string
}

interface AuthContextType {
  user: User | null
  token: string | null
  loading: boolean
  login: (email: string, password: string) => Promise<void>
  logout: () => void
  setToken: (token: string) => void
}

const AuthContext = createContext<AuthContextType | undefined>(undefined)

interface AuthProviderProps {
  children: ReactNode
}

export function AuthProvider({ children }: AuthProviderProps) {
  const [user, setUser] = useState<User | null>(null)
  const [token, setToken] = useState<string | null>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    // Check for existing token on mount
    const savedToken = localStorage.getItem('access_token')
    if (savedToken) {
      setToken(savedToken)
      api.setToken(savedToken)
      // TODO: Validate token and get user info
    }
    setLoading(false)
  }, [])

  const login = async (email: string, password: string) => {
    const response = await api.login({ email, password })
    setToken(response.access_token)
    api.setToken(response.access_token)
    localStorage.setItem('access_token', response.access_token)

    // Set user info from response with proper type casting
    setUser({
      id: String(response.user.id),
      email: String(response.user.email),
      name: String(response.user.name),
      email_verified: Boolean(response.user.email_verified),
      is_admin: Boolean(response.user.is_admin),
      oauth_provider: response.user.oauth_provider ? String(response.user.oauth_provider) : undefined,
      oauth_avatar_url: response.user.oauth_avatar_url ? String(response.user.oauth_avatar_url) : undefined,
    })
  }

  const logout = () => {
    setUser(null)
    setToken(null)
    localStorage.removeItem('access_token')
    api.clearToken()
  }

  const saveToken = (newToken: string) => {
    setToken(newToken)
    localStorage.setItem('access_token', newToken)
    api.setToken(newToken)
  }

  return (
    <AuthContext.Provider
      value={{
        user,
        token,
        loading,
        login,
        logout,
        setToken: saveToken,
      }}
    >
      {children}
    </AuthContext.Provider>
  )
}

export function useAuth() {
  const context = useContext(AuthContext)
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider')
  }
  return context
}