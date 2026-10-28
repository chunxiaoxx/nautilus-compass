import { jwtDecode } from 'jwt-decode'

const TOKEN_KEY = 'nautilus_auth_token'
const REMEMBER_ME_KEY = 'nautilus_remember_me'

interface TokenPayload {
  userId: string
  email: string
  exp: number
}

export const tokenUtils = {
  save: (token: string, rememberMe: boolean = false): void => {
    if (rememberMe) {
      localStorage.setItem(TOKEN_KEY, token)
      localStorage.setItem(REMEMBER_ME_KEY, 'true')
    } else {
      sessionStorage.setItem(TOKEN_KEY, token)
      localStorage.removeItem(REMEMBER_ME_KEY)
    }
  },

  get: (): string | null => {
    const rememberMe = localStorage.getItem(REMEMBER_ME_KEY) === 'true'
    return rememberMe
      ? localStorage.getItem(TOKEN_KEY)
      : sessionStorage.getItem(TOKEN_KEY)
  },

  remove: (): void => {
    localStorage.removeItem(TOKEN_KEY)
    localStorage.removeItem(REMEMBER_ME_KEY)
    sessionStorage.removeItem(TOKEN_KEY)
  },

  isValid: (token: string): boolean => {
    try {
      const decoded = jwtDecode<TokenPayload>(token)
      const currentTime = Date.now() / 1000
      return decoded.exp > currentTime
    } catch {
      return false
    }
  },

  decode: (token: string): TokenPayload | null => {
    try {
      return jwtDecode<TokenPayload>(token)
    } catch {
      return null
    }
  },
}
