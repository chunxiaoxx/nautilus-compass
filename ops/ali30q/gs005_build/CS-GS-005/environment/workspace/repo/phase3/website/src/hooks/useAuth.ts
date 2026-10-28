import { useState } from 'react'
import { useAuth as useAuthContext } from '../context/AuthContext'
import { LoginCredentials, RegisterCredentials, WalletLoginCredentials } from '../types/auth'

interface UseLoginReturn {
  login: (credentials: LoginCredentials) => Promise<void>
  isLoading: boolean
  error: string | null
}

interface UseRegisterReturn {
  register: (credentials: RegisterCredentials) => Promise<void>
  isLoading: boolean
  error: string | null
}

interface UseWalletLoginReturn {
  loginWithWallet: (credentials: WalletLoginCredentials) => Promise<void>
  isLoading: boolean
  error: string | null
}

export const useLogin = (): UseLoginReturn => {
  const { login: contextLogin } = useAuthContext()
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const login = async (credentials: LoginCredentials): Promise<void> => {
    setIsLoading(true)
    setError(null)

    try {
      await contextLogin(credentials)
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : '登录失败'
      setError(errorMessage)
      throw err
    } finally {
      setIsLoading(false)
    }
  }

  return { login, isLoading, error }
}

export const useRegister = (): UseRegisterReturn => {
  const { register: contextRegister } = useAuthContext()
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const register = async (credentials: RegisterCredentials): Promise<void> => {
    setIsLoading(true)
    setError(null)

    try {
      await contextRegister(credentials)
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : '注册失败'
      setError(errorMessage)
      throw err
    } finally {
      setIsLoading(false)
    }
  }

  return { register, isLoading, error }
}

export const useWalletLogin = (): UseWalletLoginReturn => {
  const { loginWithWallet: contextLoginWithWallet } = useAuthContext()
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const loginWithWallet = async (credentials: WalletLoginCredentials): Promise<void> => {
    setIsLoading(true)
    setError(null)

    try {
      await contextLoginWithWallet(credentials)
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : '钱包登录失败'
      setError(errorMessage)
      throw err
    } finally {
      setIsLoading(false)
    }
  }

  return { loginWithWallet, isLoading, error }
}

export const useLogout = () => {
  const { logout } = useAuthContext()
  return { logout }
}

export const useAuthCheck = () => {
  const { user, isAuthenticated, isLoading } = useAuthContext()
  return { user, isAuthenticated, isLoading }
}
