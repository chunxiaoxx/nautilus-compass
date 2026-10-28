import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import { BrowserRouter } from 'react-router-dom'
import Login from '../Login'
import * as useAuthHook from '../../hooks/useAuth'

// Mock react-router-dom
const mockNavigate = vi.fn()
vi.mock('react-router-dom', async () => {
  const actual = await vi.importActual('react-router-dom')
  return {
    ...actual,
    useNavigate: () => mockNavigate,
    useLocation: () => ({ state: null })
  }
})

// Mock useAuth hooks
vi.mock('../../hooks/useAuth', () => ({
  useLogin: vi.fn(),
  useWalletLogin: vi.fn()
}))

describe('Login', () => {
  const mockLogin = vi.fn()
  const mockLoginWithWallet = vi.fn()

  beforeEach(() => {
    vi.clearAllMocks()

    vi.mocked(useAuthHook.useLogin).mockReturnValue({
      login: mockLogin,
      isLoading: false,
      error: null
    })

  vi.mocked(useAuthHook.useWalletLogin).mockReturnValue({
      loginWithWallet: mockLoginWithWallet,
      isLoading: false,
      error: null
    })
  })

  const renderLogin = () => {
    return render(
      <BrowserRouter>
        <Login />
      </BrowserRouter>
    )
  }

  it('should render login page title', () => {
    renderLogin()

    expect(screen.getByText('登录到 Nautilus')).toBeInTheDocument()
  })

  it('should render register link', () => {
    renderLogin()

    expect(screen.getByText('还没有账户?')).toBeInTheDocument()
    expect(screen.getByText('立即注册')).toBeInTheDocument()
  })

  it('should render mode toggle buttons', () => {
    renderLogin()

    expect(screen.getByText('邮箱登录')).toBeInTheDocument()
    expect(screen.getByText('钱包登录')).toBeInTheDocument()
  })

  it('should show email form by default', () => {
    renderLogin()

    expect(screen.getByLabelText('邮箱地址')).toBeInTheDocument()
    expect(screen.getByLabelText('密码')).toBeInTheDocument()
    expect(screen.getByLabelText('记住我')).toBeInTheDocument()
  })

  it('should switch to wallet mode when clicking wallet button', () => {
    renderLogin()

    const walletButton = screen.getByText('钱包登录')
    fireEvent.click(walletButton)

    expect(screen.getByText('使用您的 Web3 钱包登录')).toBeInTheDocument()
    expect(screen.getByText('连接 MetaMask')).toBeInTheDocument()
  })

  it('should switch back to email mode', () => {
    renderLogin()

    // Switch to wallet
    fireEvent.click(screen.getByText('钱包登录'))

    // Switch back to email
    fireEvent.click(screen.getByText('邮箱登录'))

    expect(screen.getByLabelText('邮箱地址')).toBeInTheDocument()
  })

  it('should render forgot password link', () => {
    renderLogin()

    expect(screen.getByText('忘记密码?')).toBeInTheDocument()
  })

  it('should call login function with valid data', async () => {
    mockLogin.mockResolvedValue(undefined)
    renderLogin()

    const emailInput = screen.getByLabelText('邮箱地址')
    const passwordInput = screen.getByLabelText('密码')
    const submitButton = screen.getByRole('button', { name: '登录' })

    fireEvent.change(emailInput, { target: { value: 'test@example.com' } })
    fireEvent.change(passwordInput, { target: { value: 'Password123' } })
    fireEvent.click(submitButton)

    await waitFor(() => {
      expect(mockLogin).toHaveBeenCalledWith({
        email: 'test@example.com',
        password: 'Password123',
        rememberMe: false
      })
    })
  })

  it('should navigate to home after successful login', async () => {
    mockLogin.mockResolvedValue(undefined)
    renderLogin()

    const emailInput = screen.getByLabelText('邮箱地址')
    const passwordInput = screen.getByLabelText('密码')
    const submitButton = screen.getByRole('button', { name: '登录' })

    fireEvent.change(emailInput, { target: { value: 'test@example.com' } })
    fireEvent.change(passwordInput, { target: { value: 'Password123' } })
    fireEvent.click(submitButton)

    await waitFor(() => {
      expect(mockNavigate).toHaveBeenCalledWith('/', { replace: true })
    })
  })

  it('should display login error message', () => {
    vi.mocked(useAuthHook.useLogin).mockReturnValue({
      login: mockLogin,
      isLoading: false,
      error: '邮箱或密码错误'
    })

    renderLogin()

    expect(screen.getByText('邮箱或密码错误')).toBeInTheDocument()
  })

  it('should show loading state during login', () => {
    vi.mocked(useAuthHook.useLogin).mockReturnValue({
      login: mockLogin,
      isLoading: true,
      error: null
    })

    renderLogin()

    expect(screen.getByText('登录中...')).toBeInTheDocument()
  })

  it('should disable submit button when loading', () => {
    vi.mocked(useAuthHook.useLogin).mockReturnValue({
      login: mockLogin,
      isLoading: true,
      error: null
    })

    renderLogin()

    const submitButton = screen.getByRole('button', { name: '登录中...' })
    expect(submitButton).toBeDisabled()
  })

  it('should handle remember me checkbox', async () => {
    mockLogin.mockResolvedValue(undefined)
    renderLogin()

  const emailInput = screen.getByLabelText('邮箱地址')
    const passwordInput = screen.getByLabelText('密码')
    const rememberMeCheckbox = screen.getByLabelText('记住我')
    const submitButton = screen.getByRole('button', { name: '登录' })

    fireEvent.change(emailInput, { target: { value: 'test@example.com' } })
    fireEvent.change(passwordInput, { target: { value: 'Password123' } })
    fireEvent.click(rememberMeCheckbox)
    fireEvent.click(submitButton)

    await waitFor(() => {
      expect(mockLogin).toHaveBeenCalledWith({
        email: 'test@example.com',
        password: 'Password123',
        rememberMe: true
      })
    })
  })

  it('should render wallet login button', () => {
    renderLogin()

    fireEvent.click(screen.getByText('钱包登录'))

    expect(screen.getByText('连接 MetaMask')).toBeInTheDocument()
  })

  it('should show wallet loading state', () => {
    vi.mocked(useAuthHook.useWalletLogin).mockReturnValue({
      loginWithWallet: mockLoginWithWallet,
      isLoading: true,
      error: null
    })

    renderLogin()

    fireEvent.click(screen.getByText('钱包登录'))

    expect(screen.getByText('连接中...')).toBeInTheDocument()
  })

  it('should handle form submission without filling fields', async () => {
    renderLogin()

    const submitButton = screen.getByRole('button', { name: '登录' })
    fireEvent.click(submitButton)

    // Should not call login with empty data
    await waitFor(() => {
      expect(mockLogin).not.toHaveBeenCalled()
    })
  })
})
