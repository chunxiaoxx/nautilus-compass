import { createContext, useContext, useState, useEffect, ReactNode } from 'react'
import { apiClient, handleApiError } from '../utils/api'
import { tokenUtils } from '../utils/token'
import {
  User,
  AuthContextType,
  LoginCredentials,
  RegisterCredentials,
  WalletLoginCredentials,
  AuthResponse,
} from '../types/auth'

const AuthContext = createContext<AuthContextType | undefined>(undefined)

interface AuthProviderProps {
  children: ReactNode
}

export const AuthProvider = ({ children }: AuthProviderProps) => {
  const [user, setUser] = useState<User | null>(null)
  const [token, setToken] = useState<string | null>(null)
  const [isLoading, setIsLoading] = useState(true)

  // Check authentication on mount
  useEffect(() => {
    const checkAuth = async () => {
      const savedToken = tokenUtils.get()

      if (!savedToken || !tokenUtils.isValid(savedToken)) {
        tokenUtils.remove()
        setIsLoading(false)
        return
      }

      try {
        const response = await apiClient.get<AuthResponse>('/api/auth/me')
        if (response.data.success && response.data.data) {
          setUser(response.data.data.user)
          setToken(savedToken)
        } else {
          tokenUtils.remove()
        }
      } catch (error) {
        console.error('Auth check failed:', error)
        tokenUtils.remove()
      } finally {
        setIsLoading(false)
      }
    }

    checkAuth()
  }, [])

  const login = async (credentials: LoginCredentials): Promise<void> => {
    try {
      const response = await apiClient.post<AuthResponse>('/api/auth/login', {
        email: credentials.email,
        password: credentials.password,
      })

      if (!response.data.success || !response.data.data) {
        throw new Error(response.data.error || '登录失败')
      }

      const { user: userData, token: authToken } = response.data.data

      tokenUtils.save(authToken, credentials.rememberMe || false)
      setUser(userData)
      setToken(authToken)
    } catch (error) {
      const errorMessage = handleApiError(error)
      throw new Error(errorMessage)
    }
  }

  const register = async (credentials: RegisterCredentials): Promise<void> => {
    try {
      const response = await apiClient.post<AuthResponse>('/api/auth/register', {
        email: credentials.email,
        password: credentials.password,
      })

      if (!response.data.success || !response.data.data) {
        throw new Error(response.data.error || '注册失败')
      }

      const { user: userData, token: authToken } = response.data.data

      tokenUtils.save(authToken, false)
      setUser(userData)
      setToken(authToken)
    } catch (error) {
      const errorMessage = handleApiError(error)
      throw new Error(errorMessage)
    }
  }

  const loginWithWallet = async (
    credentials: WalletLoginCredentials
  ): Promise<void> => {
    try {
      const response = await apiClient.post<AuthResponse>('/api/auth/wallet-login', {
        walletAddress: credentials.walletAddress,
        signature: credentials.signature,
      })

      if (!response.data.success || !response.data.data) {
        throw new Error(response.data.error || '钱包登录失败')
      }

      const { user: userData, token: authToken } = response.data.data

      tokenUtils.save(authToken, true)
      setUser(userData)
      setToken(authToken)
    } catch (error) {
      const errorMessage = handleApiError(error)
      throw new Error(errorMessage)
    }
  }

  const logout = (): void => {
    tokenUtils.remove()
    setUser(null)
    setToken(null)
  }

  const value: AuthContextType = {
    user,
    token,
    isAuthenticated: !!user && !!token,
    isLoading,
    login,
    register,
    loginWithWallet,
    logout,
  }

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>
}

export const useAuth = (): AuthContextType => {
  const context = useContext(AuthContext)
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider')
  }
  return context
}
