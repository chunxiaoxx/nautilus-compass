import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import { BrowserRouter } from 'react-router-dom'
import Register from '../Register'
import * as useAuthHook from '../../hooks/useAuth'

// Mock react-router-dom
const mockNavigate = vi.fn()
vi.mock('react-router-dom', async () => {
  const actual = await vi.importActual('react-router-dom')
  return {
    ...actual,
    useNavigate: () => mockNavigate
  }
})

// Mock useAuth hooks
vi.mock('../../hooks/useAuth', () => ({
  useRegister: vi.fn(),
  useWalletLogin: vi.fn()
}))

describe('Register', () => {
  const mockRegister = vi.fn()
  const mockLoginWithWallet = vi.fn()

  beforeEach(() => {
    vi.clearAllMocks()

    vi.mocked(useAuthHook.useRegister).mockReturnValue({
      register: mockRegister,
      isLoading: false,
      error: null
    })

    vi.mocked(useAuthHook.useWalletLogin).mockReturnValue({
      loginWithWallet: mockLoginWithWallet,
      isLoading: false,
      error: null
    })
  })

  const renderRegister = () => {
    return render(
      <BrowserRouter>
    <Register />
      </BrowserRouter>
    )
  }

  it('should render register page title', () => {
    renderRegister()

    expect(screen.getByText('创建 Nautilus 账户')).toBeInTheDocument()
  })

  it('should render login link', () => {
    renderRegister()

    expect(screen.getByText('已有账户?')).toBeInTheDocument()
    expect(screen.getByText('立即登录')).toBeInTheDocument()
  })

  it('should render mode toggle buttons', () => {
    renderRegister()

    expect(screen.getByText('邮箱注册')).toBeInTheDocument()
    expect(screen.getByText('钱包注册')).toBeInTheDocument()
  })

  it('should show email form by default', () => {
    renderRegister()

    expect(screen.getByLabelText('邮箱地址')).toBeInTheDocument()
    expect(screen.getByLabelText('密码')).toBeInTheDocument()
    expect(screen.getByLabelText('确认密码')).toBeInTheDocument()
  })

  it('should switch to wallet mode when clicking wallet button', () => {
    renderRegister()

  const walletButton = screen.getByText('钱包注册')
    fireEvent.click(walletButton)

    expect(screen.getByText('使用您的 Web3 钱包注册')).toBeInTheDocument()
    expect(screen.getByText('连接 MetaMask')).toBeInTheDocument()
  })

  it('should switch back to email mode', () => {
    renderRegister()

    // Switch to wallet
    fireEvent.click(screen.getByText('钱包注册'))

    // Switch back to email
    fireEvent.click(screen.getByText('邮箱注册'))

    expect(screen.getByLabelText('邮箱地址')).toBeInTheDocument()
  })

  it('should render all email form fields', () => {
    renderRegister()

    expect(screen.getByLabelText('邮箱地址')).toBeInTheDocument()
    expect(screen.getByLabelText('密码')).toBeInTheDocument()
    expect(screen.getByLabelText('确认密码')).toBeInTheDocument()
    expect(screen.getByLabelText(/我同意/)).toBeInTheDocument()
  })

  it('should show password requirements hint', () => {
    renderRegister()

    expect(screen.getByText(/密码必须至少8个字符/)).toBeInTheDocument()
  })

  it('should render terms and privacy links', () => {
    renderRegister()

    expect(screen.getByText('服务条款')).toBeInTheDocument()
    expect(screen.getByText('隐私政策')).toBeInTheDocument()
  })

  it('should handle form submission with invalid email', async () => {
    renderRegister()

    const emailInput = screen.getByLabelText('邮箱地址')
    const passwordInput = screen.getByLabelText('密码')
    const confirmInput = screen.getByLabelText('确认密码')
    const termsCheckbox = screen.getByLabelText(/我同意/)
    const submitButton = screen.getByRole('button', { name: '注册' })

    fireEvent.change(emailInput, { target: { value: 'invalid-email' } })
    fireEvent.change(passwordInput, { target: { value: 'Password123' } })
    fireEvent.change(confirmInput, { target: { value: 'Password123' } })
    fireEvent.click(termsCheckbox)
    fireEvent.click(submitButton)

    // Should not call register with invalid email
    await waitFor(() => {
      expect(mockRegister).not.toHaveBeenCalled()
    })
  })

  it('should show validation error for short password', async () => {
    renderRegister()

    const passwordInput = screen.getByLabelText('密码')
    const submitButton = screen.getByRole('button', { name: '注册' })

    fireEvent.change(passwordInput, { target: { value: '123' } })
    fireEvent.click(submitButton)

    await waitFor(() => {
      expect(screen.getByText('密码至少需要8个字符')).toBeInTheDocument()
    })
  })

  it('should show validation error when passwords do not match', async () => {
    renderRegister()
    const passwordInput = screen.getByLabelText('密码')
    const confirmInput = screen.getByLabelText('确认密码')
    const submitButton = screen.getByRole('button', { name: '注册' })

    fireEvent.change(passwordInput, { target: { value: 'Password123' } })
    fireEvent.change(confirmInput, { target: { value: 'Different123' } })
    fireEvent.click(submitButton)

    await waitFor(() => {
      expect(screen.getByText('两次输入的密码不一致')).toBeInTheDocument()
    })
  })

  it('should show validation error when terms not accepted', async () => {
    renderRegister()
    const emailInput = screen.getByLabelText('邮箱地址')
    const passwordInput = screen.getByLabelText('密码')
    const confirmInput = screen.getByLabelText('确认密码')
    const submitButton = screen.getByRole('button', { name: '注册' })

    fireEvent.change(emailInput, { target: { value: 'test@example.com' } })
    fireEvent.change(passwordInput, { target: { value: 'Password123' } })
    fireEvent.change(confirmInput, { target: { value: 'Password123' } })
    fireEvent.click(submitButton)

    await waitFor(() => {
      expect(screen.getByText('请同意用户协议')).toBeInTheDocument()
    })
  })

  it('should call register function with valid data', async () => {
    mockRegister.mockResolvedValue(undefined)
    renderRegister()

    const emailInput = screen.getByLabelText('邮箱地址')
    const passwordInput = screen.getByLabelText('密码')
    const confirmInput = screen.getByLabelText('确认密码')
    const termsCheckbox = screen.getByLabelText(/我同意/)
    const submitButton = screen.getByRole('button', { name: '注册' })

    fireEvent.change(emailInput, { target: { value: 'test@example.com' } })
    fireEvent.change(passwordInput, { target: { value: 'Password123' } })
    fireEvent.change(confirmInput, { target: { value: 'Password123' } })
    fireEvent.click(termsCheckbox)
    fireEvent.click(submitButton)

    await waitFor(() => {
  expect(mockRegister).toHaveBeenCalledWith({
        email: 'test@example.com',
        password: 'Password123',
        confirmPassword: 'Password123',
        acceptTerms: true
      })
    })
  })

  it('should navigate to home after successful registration', async () => {
    mockRegister.mockResolvedValue(undefined)
    renderRegister()

    const emailInput = screen.getByLabelText('邮箱地址')
    const passwordInput = screen.getByLabelText('密码')
    const confirmInput = screen.getByLabelText('确认密码')
    const termsCheckbox = screen.getByLabelText(/我同意/)
    const submitButton = screen.getByRole('button', { name: '注册' })

    fireEvent.change(emailInput, { target: { value: 'test@example.com' } })
    fireEvent.change(passwordInput, { target: { value: 'Password123' } })
    fireEvent.change(confirmInput, { target: { value: 'Password123' } })
    fireEvent.click(termsCheckbox)
    fireEvent.click(submitButton)

    await waitFor(() => {
      expect(mockNavigate).toHaveBeenCalledWith('/', { replace: true })
    })
  })

  it('should display register error message', () => {
    vi.mocked(useAuthHook.useRegister).mockReturnValue({
      register: mockRegister,
      isLoading: false,
      error: '邮箱已被注册'
    })

    renderRegister()

    expect(screen.getByText('邮箱已被注册')).toBeInTheDocument()
  })

  it('should show loading state during registration', () => {
    vi.mocked(useAuthHook.useRegister).mockReturnValue({
      register: mockRegister,
      isLoading: true,
      error: null
    })

    renderRegister()

    expect(screen.getByText('注册中...')).toBeInTheDocument()
  })

  it('should disable submit button when loading', () => {
    vi.mocked(useAuthHook.useRegister).mockReturnValue({
      register: mockRegister,
      isLoading: true,
      error: null
    })

    renderRegister()

    const submitButton = screen.getByRole('button', { name: '注册中...' })
    expect(submitButton).toBeDisabled()
  })

  it('should render wallet registration button', () => {
    renderRegister()

    fireEvent.click(screen.getByText('钱包注册'))

    expect(screen.getByText('连接 MetaMask')).toBeInTheDocument()
  })

  it('should show wallet loading state', () => {
    vi.mocked(useAuthHook.useWalletLogin).mockReturnValue({
      loginWithWallet: mockLoginWithWallet,
      isLoading: true,
      error: null
    })

    renderRegister()

    fireEvent.click(screen.getByText('钱包注册'))

    expect(screen.getByText('连接中...')).toBeInTheDocument()
  })
})
