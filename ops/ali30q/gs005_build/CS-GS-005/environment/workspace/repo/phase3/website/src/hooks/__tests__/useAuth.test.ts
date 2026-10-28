import { describe, it, expect, vi, beforeEach } from 'vitest'
import { renderHook, waitFor } from '@testing-library/react'
import { useLogin, useRegister, useWalletLogin, useLogout, useAuthCheck } from '../useAuth'
import * as AuthContext from '../../context/AuthContext'

// Mock AuthContext
vi.mock('../../context/AuthContext', () => ({
  useAuth: vi.fn()
}))

describe('useLogin', () => {
  const mockLogin = vi.fn()

  beforeEach(() => {
    vi.clearAllMocks()
    vi.mocked(AuthContext.useAuth).mockReturnValue({
      login: mockLogin,
      logout: vi.fn(),
      register: vi.fn(),
      loginWithWallet: vi.fn(),
      user: null,
      token: null,
    isAuthenticated: false,
      isLoading: false
    })
  })

  it('should handle successful login', async () => {
    mockLogin.mockResolvedValueOnce(undefined)

    const { result } = renderHook(() => useLogin())

    expect(result.current.isLoading).toBe(false)
    expect(result.current.error).toBe(null)

    const loginPromise = result.current.login({
      email: 'test@example.com',
      password: 'password123'
    })

    await waitFor(() => {
      expect(result.current.isLoading).toBe(false)
    })

    await loginPromise

    expect(mockLogin).toHaveBeenCalledWith({
      email: 'test@example.com',
      password: 'password123'
    })
    expect(result.current.error).toBe(null)
  })

  it('should handle login error', async () => {
    const errorMessage = '登录失败：用户名或密码错误'
    mockLogin.mockRejectedValueOnce(new Error(errorMessage))

    const { result } = renderHook(() => useLogin())

    try {
      await result.current.login({
        email: 'test@example.com',
        password: 'wrongpassword'
      })
    } catch (err) {
      // Expected error
    }

    await waitFor(() => {
      expect(result.current.error).toBe(errorMessage)
      expect(result.current.isLoading).toBe(false)
    })
  })

  it('should set loading state during login', async () => {
    mockLogin.mockImplementation(() => new Promise(resolve => setTimeout(resolve, 100)))

    const { result } = renderHook(() => useLogin())

    const loginPromise = result.current.login({
      email: 'test@example.com',
      password: 'password123'
    })

    // Should be loading immediately after calling login
    await waitFor(() => {
      expect(result.current.isLoading).toBe(true)
    })

    await loginPromise

  // Should not be loading after completion
    await waitFor(() => {
   expect(result.current.isLoading).toBe(false)
    })
  })
})

describe('useRegister', () => {
  const mockRegister = vi.fn()

  beforeEach(() => {
    vi.clearAllMocks()
    vi.mocked(AuthContext.useAuth).mockReturnValue({
      login: vi.fn(),
      logout: vi.fn(),
      register: mockRegister,
      loginWithWallet: vi.fn(),
      user: null,
      token: null,
      isAuthenticated: false,
      isLoading: false
    })
  })

  it('should handle successful registration', async () => {
    mockRegister.mockResolvedValueOnce(undefined)

    const { result } = renderHook(() => useRegister())

    await result.current.register({
      email: 'newuser@example.com',
      password: 'password123',
      confirmPassword: 'password123',
      acceptTerms: true
    })

    expect(mockRegister).toHaveBeenCalledWith({
      email: 'newuser@example.com',
      password: 'password123',
      confirmPassword: 'password123',
      acceptTerms: true
    })
    expect(result.current.error).toBe(null)
  })

  it('should handle registration error', async () => {
    const errorMessage = '注册失败：邮箱已存在'
    mockRegister.mockRejectedValueOnce(new Error(errorMessage))

    const { result } = renderHook(() => useRegister())

    try {
      await result.current.register({
        email: 'existing@example.com',
        password: 'password123',
        confirmPassword: 'password123',
        acceptTerms: true
      })
    } catch (err) {
      // Expected error
    }

    await waitFor(() => {
      expect(result.current.error).toBe(errorMessage)
    })
  })
})

describe('useWalletLogin', () => {
  const mockLoginWithWallet = vi.fn()

  beforeEach(() => {
    vi.clearAllMocks()
    vi.mocked(AuthContext.useAuth).mockReturnValue({
      login: vi.fn(),
      logout: vi.fn(),
      register: vi.fn(),
    loginWithWallet: mockLoginWithWallet,
      user: null,
      token: null,
      isAuthenticated: false,
      isLoading: false
    })
  })

  it('should handle successful wallet login', async () => {
    mockLoginWithWallet.mockResolvedValueOnce(undefined)

    const { result } = renderHook(() => useWalletLogin())

    await result.current.loginWithWallet({
      walletAddress: '0x1234567890abcdef',
      signature: 'signature123'
    })

    expect(mockLoginWithWallet).toHaveBeenCalledWith({
      walletAddress: '0x1234567890abcdef',
      signature: 'signature123'
    })
    expect(result.current.error).toBe(null)
  })

  it('should handle wallet login error', async () => {
    const errorMessage = '钱包登录失败：签名无效'
    mockLoginWithWallet.mockRejectedValueOnce(new Error(errorMessage))

    const { result } = renderHook(() => useWalletLogin())

    try {
      await result.current.loginWithWallet({
        walletAddress: '0x1234567890abcdef',
        signature: 'invalidsignature'
      })
    } catch (err) {
      // Expected error
    }

    await waitFor(() => {
      expect(result.current.error).toBe(errorMessage)
    })
  })
})

describe('useLogout', () => {
  const mockLogout = vi.fn()

  beforeEach(() => {
    vi.clearAllMocks()
    vi.mocked(AuthContext.useAuth).mockReturnValue({
      login: vi.fn(),
      logout: mockLogout,
      register: vi.fn(),
      loginWithWallet: vi.fn(),
      user: null,
      token: null,
      isAuthenticated: false,
      isLoading: false
    })
  })

  it('should return logout function', () => {
    const { result } = renderHook(() => useLogout())

    expect(result.current.logout).toBe(mockLogout)
  })
})

describe('useAuthCheck', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('should return auth state when not authenticated', () => {
    vi.mocked(AuthContext.useAuth).mockReturnValue({
      login: vi.fn(),
      logout: vi.fn(),
      register: vi.fn(),
      loginWithWallet: vi.fn(),
      user: null,
      token: null,
      isAuthenticated: false,
      isLoading: false
    })

    const { result } = renderHook(() => useAuthCheck())

    expect(result.current.user).toBe(null)
    expect(result.current.isAuthenticated).toBe(false)
    expect(result.current.isLoading).toBe(false)
  })

  it('should return auth state when authenticated', () => {
    const mockUser = {
      id: '1',
    email: 'test@example.com',
      createdAt: new Date().toISOString()
    }

    vi.mocked(AuthContext.useAuth).mockReturnValue({
      login: vi.fn(),
      logout: vi.fn(),
      register: vi.fn(),
      loginWithWallet: vi.fn(),
    user: mockUser,
      token: 'mock-token',
      isAuthenticated: true,
      isLoading: false
    })
    const { result } = renderHook(() => useAuthCheck())

    expect(result.current.user).toEqual(mockUser)
    expect(result.current.isAuthenticated).toBe(true)
    expect(result.current.isLoading).toBe(false)
  })

  it('should return loading state', () => {
    vi.mocked(AuthContext.useAuth).mockReturnValue({
      login: vi.fn(),
      logout: vi.fn(),
      register: vi.fn(),
      loginWithWallet: vi.fn(),
      user: null,
      token: null,
      isAuthenticated: false,
      isLoading: true
    })

    const { result } = renderHook(() => useAuthCheck())

    expect(result.current.isLoading).toBe(true)
  })
})
