import React, { useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { User, Mail, Lock, Wallet } from 'lucide-react'
import { authAPI } from '../lib/api'

// 密码验证函数
const validatePassword = (password: string): string | null => {
  if (password.length < 12) {
    return '密码至少需要12个字符'
  }
  if (!/[A-Z]/.test(password)) {
    return '密码必须包含至少一个大写字母'
  }
  if (!/[a-z]/.test(password)) {
    return '密码必须包含至少一个小写字母'
  }
  if (!/[0-9]/.test(password)) {
    return '密码必须包含至少一个数字'
  }
  if (!/[!@#$%^&*(),.?":{}|<>]/.test(password)) {
    return '密码必须包含至少一个特殊字符 (!@#$%^&*等)'
  }
  return null
}

export default function RegisterPage() {
  const navigate = useNavigate()
  const [formData, setFormData] = useState({
    username: '',
    email: '',
    password: '',
    confirmPassword: '',
    walletAddress: ''
  })
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setError('')

    // 验证密码强度
    const passwordError = validatePassword(formData.password)
    if (passwordError) {
      setError(passwordError)
      return
    }

    if (formData.password !== formData.confirmPassword) {
      setError('密码不匹配')
      return
    }

    setLoading(true)

    try {
      const data: any = {
        username: formData.username,
        email: formData.email,
        password: formData.password
      }

      if (formData.walletAddress.trim()) {
        data.wallet_address = formData.walletAddress
      }

      console.log('Sending registration request:', { ...data, password: '***' })
      const response = await authAPI.register(data)
      console.log('Registration response:', response)

      if (response.token || response.access_token) {
        const token = response.token || response.access_token
        localStorage.setItem('token', token)
        if (response.user) {
          localStorage.setItem('user', JSON.stringify(response.user))
        }
        navigate('/dashboard')
      } else {
        setError('注册成功但未收到token，请尝试登录')
      }
    } catch (err: any) {
      console.error('Registration error:', err)
      console.error('Error response:', err.response)
      const errorMsg = err.response?.data?.detail || err.message || '注册失败，请稍后重试'
      setError(typeof errorMsg === 'string' ? errorMsg : JSON.stringify(errorMsg))
    } finally {
      setLoading(false)
    }
  }

  return (
    <div style={{
      minHeight: '100vh',
      background: 'linear-gradient(135deg, #2563EB 0%, #8B5CF6 100%)',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
      padding: '24px'
    }}>
      <div style={{
        backgroundColor: 'white',
        borderRadius: '16px',
        boxShadow: '0 25px 50px -12px rgba(0, 0, 0, 0.25)',
        maxWidth: '480px',
        width: '100%',
        padding: '48px'
      }}>
        <div style={{ textAlign: 'center', marginBottom: '32px' }}>
          <Link to="/" style={{
            display: 'inline-block',
            textDecoration: 'none',
            marginBottom: '16px'
          }}>
            <img
              src="/nautilus-icon-final.png"
              alt="Nautilus"
              style={{
                height: '80px',
                width: 'auto',
                filter: 'drop-shadow(0 8px 20px rgba(37, 99, 235, 0.3)) brightness(1.1) contrast(1.1)',
              }}
            />
          </Link>
          <h2 style={{
            fontSize: '1.875rem',
            fontWeight: 'bold',
            color: '#111827',
            marginBottom: '8px'
          }}>
            创建账户
          </h2>
          <p style={{
            fontSize: '0.875rem',
            color: '#6B7280'
          }}>
            加入 Nautilus AI 智能体生态系统
          </p>
        </div>

        {error && (
          <div style={{
            backgroundColor: '#FEE2E2',
            border: '1px solid #EF4444',
            color: '#991B1B',
            padding: '12px',
            borderRadius: '8px',
            marginBottom: '20px',
            fontSize: '0.875rem'
          }}>
            {error}
          </div>
        )}

        <form onSubmit={handleSubmit}>
          <div style={{ marginBottom: '20px' }}>
            <label style={{
              display: 'block',
              fontSize: '0.875rem',
              fontWeight: '500',
              color: '#374151',
              marginBottom: '8px'
            }}>
              <User size={16} style={{ display: 'inline', marginRight: '4px' }} />
              用户名 *
            </label>
            <input
              type="text"
              value={formData.username}
              onChange={(e) => setFormData({ ...formData, username: e.target.value })}
              placeholder="输入用户名"
              style={{
                width: '100%',
                padding: '12px 16px',
                border: '1px solid #D1D5DB',
                borderRadius: '8px',
                fontSize: '0.875rem',
                boxSizing: 'border-box'
              }}
              required
              disabled={loading}
            />
          </div>

          <div style={{ marginBottom: '20px' }}>
            <label style={{
              display: 'block',
              fontSize: '0.875rem',
              fontWeight: '500',
              color: '#374151',
              marginBottom: '8px'
            }}>
              <Mail size={16} style={{ display: 'inline', marginRight: '4px' }} />
              邮箱 *
            </label>
            <input
              type="email"
              value={formData.email}
              onChange={(e) => setFormData({ ...formData, email: e.target.value })}
              placeholder="your@email.com"
              style={{
                width: '100%',
                padding: '12px 16px',
                border: '1px solid #D1D5DB',
                borderRadius: '8px',
                fontSize: '0.875rem',
                boxSizing: 'border-box'
              }}
              required
              disabled={loading}
            />
          </div>

          <div style={{ marginBottom: '20px' }}>
            <label style={{
              display: 'block',
              fontSize: '0.875rem',
              fontWeight: '500',
              color: '#374151',
              marginBottom: '8px'
            }}>
              <Lock size={16} style={{ display: 'inline', marginRight: '4px' }} />
              密码 *
            </label>
            <input
              type="password"
              value={formData.password}
              onChange={(e) => setFormData({ ...formData, password: e.target.value })}
              placeholder="至少12个字符，包含大小写字母、数字和特殊字符"
              style={{
                width: '100%',
                padding: '12px 16px',
                border: '1px solid #D1D5DB',
                borderRadius: '8px',
                fontSize: '0.875rem',
                boxSizing: 'border-box'
              }}
              required
              disabled={loading}
            />
            <p style={{
              fontSize: '0.75rem',
              color: '#6B7280',
              marginTop: '4px'
            }}>
              必须包含：大写字母、小写字母、数字、特殊字符
            </p>
          </div>

          <div style={{ marginBottom: '20px' }}>
            <label style={{
              display: 'block',
              fontSize: '0.875rem',
              fontWeight: '500',
              color: '#374151',
              marginBottom: '8px'
            }}>
              <Lock size={16} style={{ display: 'inline', marginRight: '4px' }} />
              确认密码 *
            </label>
            <input
              type="password"
              value={formData.confirmPassword}
              onChange={(e) => setFormData({ ...formData, confirmPassword: e.target.value })}
              placeholder="再次输入密码"
              style={{
                width: '100%',
                padding: '12px 16px',
                border: '1px solid #D1D5DB',
                borderRadius: '8px',
                fontSize: '0.875rem',
                boxSizing: 'border-box'
              }}
              required
              disabled={loading}
            />
          </div>

          <div style={{ marginBottom: '24px' }}>
            <label style={{
              display: 'block',
              fontSize: '0.875rem',
              fontWeight: '500',
              color: '#374151',
              marginBottom: '8px'
            }}>
              <Wallet size={16} style={{ display: 'inline', marginRight: '4px' }} />
              钱包地址 (可选)
            </label>
            <input
              type="text"
              value={formData.walletAddress}
              onChange={(e) => setFormData({ ...formData, walletAddress: e.target.value })}
              placeholder="可稍后在个人设置中添加"
              style={{
                width: '100%',
                padding: '12px 16px',
                border: '1px solid #D1D5DB',
                borderRadius: '8px',
                fontSize: '0.875rem',
                boxSizing: 'border-box'
              }}
              disabled={loading}
            />
            <p style={{
              fontSize: '0.75rem',
              color: '#6B7280',
              marginTop: '4px'
            }}>
              您可以稍后在个人设置中完善钱包信息
            </p>
          </div>

          <button
            type="submit"
            disabled={loading}
            style={{
              width: '100%',
              padding: '12px',
              backgroundColor: loading ? '#9CA3AF' : '#2563EB',
              color: 'white',
              borderRadius: '8px',
              fontWeight: '600',
              fontSize: '0.875rem',
              border: 'none',
              cursor: loading ? 'not-allowed' : 'pointer',
              marginBottom: '16px'
            }}
          >
            {loading ? '创建中...' : '创建账户'}
          </button>

          <div style={{
            textAlign: 'center',
            fontSize: '0.875rem',
            color: '#6B7280'
          }}>
            已有账户？{' '}
            <Link to="/login" style={{
              color: '#2563EB',
              fontWeight: '500',
              textDecoration: 'none'
            }}>
              立即登录
            </Link>
          </div>
        </form>

        <div style={{
          marginTop: '24px',
          paddingTop: '24px',
          borderTop: '1px solid #E5E7EB',
          fontSize: '0.75rem',
          color: '#9CA3AF',
          textAlign: 'center'
        }}>
          注册即表示您同意我们的{' '}
          <a href="#" style={{ color: '#2563EB', textDecoration: 'none' }}>服务条款</a>
          {' '}和{' '}
          <a href="#" style={{ color: '#2563EB', textDecoration: 'none' }}>隐私政策</a>
        </div>
      </div>
    </div>
  )
}
