export interface User {
  id: string
  email: string
  walletAddress?: string
  createdAt: string
}

export interface LoginCredentials {
  email: string
  password: string
  rememberMe?: boolean
}

export interface RegisterCredentials {
  email: string
  password: string
  confirmPassword: string
  acceptTerms: boolean
}

export interface WalletLoginCredentials {
  walletAddress: string
  signature: string
}

export interface AuthResponse {
  success: boolean
  data?: {
    user: User
    token: string
  }
  error?: string
}

export interface AuthContextType {
  user: User | null
  token: string | null
  isAuthenticated: boolean
  isLoading: boolean
  login: (credentials: LoginCredentials) => Promise<void>
  register: (credentials: RegisterCredentials) => Promise<void>
  loginWithWallet: (credentials: WalletLoginCredentials) => Promise<void>
  logout: () => void
}
