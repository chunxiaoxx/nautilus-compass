import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { tokenUtils } from '../utils/token'

const API_URL = import.meta.env.VITE_API_URL || ''

// 2026-10-10 UNIFY 1.2: 跨站回跳——?redirect= 支持各站登录后返回来源(全站统一身份,AUTH_STANDARD_V1)
// 安全校验: 仅站内相对路径(以 / 开头且非 //),防 open redirect
const safeRedirect = (): string => {
  const r = new URLSearchParams(window.location.search).get('redirect')
  return r && r.startsWith('/') && !r.startsWith('//') ? r : '/'
}

type Region = null | 'cn' | 'intl'

const Login = () => {
  const navigate = useNavigate()
  const [region, setRegion] = useState<Region>(null)
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)

  const authingLogin = () => { window.location.href = `${API_URL}/api/auth/authing/login` }
  const githubLogin = () => { window.location.href = `${API_URL}/api/auth/github/login` }
  const googleLogin = () => { window.location.href = `${API_URL}/api/auth/google/login` }

  const metamaskLogin = async () => {
    if (!(window as any).ethereum) { setError('Please install MetaMask'); return }
    setLoading(true); setError('')
    try {
      const accounts = await (window as any).ethereum.request({ method: 'eth_requestAccounts' })
      const address = accounts[0]
      const message = `Login to Nautilus\nAddress: ${address}\nTimestamp: ${Date.now()}`
      const signature = await (window as any).ethereum.request({ method: 'personal_sign', params: [message, address] })
      const resp = await fetch(`${API_URL}/api/auth/wallet-login`, {
        method: 'POST', headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ walletAddress: address, signature, message }),
      })
      const data = await resp.json()
      const token = data.data?.access_token || data.access_token
      if (token) { tokenUtils.save(token, true); navigate(safeRedirect()) }
      else setError('Wallet login failed')
    } catch (err: any) {
      if (err.code !== 4001) setError(err.message || 'Connection failed')
    } finally { setLoading(false) }
  }

  const btn = 'w-full flex items-center justify-center gap-2 py-3 px-6 rounded-xl text-white transition font-medium'

  if (!region) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-gray-900 via-blue-900 to-purple-900 py-12 px-4">
        <div className="max-w-md w-full space-y-5 bg-white/10 backdrop-blur-lg border border-white/20 p-8 rounded-xl shadow-xl">
          <div className="text-center mb-4">
            <h2 className="text-3xl font-extrabold text-white">Nautilus</h2>
            <p className="mt-2 text-gray-300">AI Agent Platform</p>
          </div>
          <button onClick={() => setRegion('cn')} className={btn + ' bg-blue-600 hover:bg-blue-700 text-lg py-4'}>
            🇨🇳 中国大陆用户
          </button>
          <button onClick={() => setRegion('intl')} className={btn + ' bg-purple-600 hover:bg-purple-700 text-lg py-4'}>
            🌏 International Users
          </button>
        </div>
      </div>
    )
  }

  return (
    <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-gray-900 via-blue-900 to-purple-900 py-12 px-4">
      <div className="max-w-md w-full space-y-4 bg-white/10 backdrop-blur-lg border border-white/20 p-8 rounded-xl shadow-xl">
        <div className="text-center mb-2">
          <h2 className="text-3xl font-extrabold text-white">Nautilus</h2>
          <p className="mt-1 text-gray-300 text-sm">
            {region === 'cn' ? 'AI Agent 平台 — 登录即创建账户' : 'AI Agent Platform — Login to get started'}
          </p>
        </div>

        {error && (
          <div className="rounded-md bg-red-500/20 border border-red-400/50 p-3">
            <p className="text-sm text-red-200">{error}</p>
          </div>
        )}

        {region === 'cn' ? (
          <>
            <button onClick={authingLogin} className={btn + ' bg-green-600 hover:bg-green-700 text-lg py-4'}>
              手机号 / 邮箱 / 微信登录
            </button>
            <button onClick={githubLogin} className={btn + ' bg-gray-800 hover:bg-gray-700 border border-white/20'}>
              <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 24 24"><path fillRule="evenodd" d="M12 2C6.477 2 2 6.484 2 12.017c0 4.425 2.865 8.18 6.839 9.504.5.092.682-.217.682-.483 0-.237-.008-.868-.013-1.703-2.782.605-3.369-1.343-3.369-1.343-.454-1.158-1.11-1.466-1.11-1.466-.908-.62.069-.608.069-.608 1.003.07 1.531 1.032 1.531 1.032.892 1.53 2.341 1.088 2.91.832.092-.647.35-1.088.636-1.338-2.22-.253-4.555-1.113-4.555-4.951 0-1.093.39-1.988 1.029-2.688-.103-.253-.446-1.272.098-2.65 0 0 .84-.27 2.75 1.026A9.564 9.564 0 0112 6.844c.85.004 1.705.115 2.504.337 1.909-1.296 2.747-1.027 2.747-1.027.546 1.379.202 2.398.1 2.651.64.7 1.028 1.595 1.028 2.688 0 3.848-2.339 4.695-4.566 4.943.359.309.678.92.678 1.855 0 1.338-.012 2.419-.012 2.747 0 .268.18.58.688.482A10.019 10.019 0 0022 12.017C22 6.484 17.522 2 12 2z" clipRule="evenodd"/></svg>
              GitHub 登录
            </button>
          </>
        ) : (
          <>
            <button onClick={githubLogin} className={btn + ' bg-gray-800 hover:bg-gray-700 border border-white/20 text-lg py-4'}>
              <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 24 24"><path fillRule="evenodd" d="M12 2C6.477 2 2 6.484 2 12.017c0 4.425 2.865 8.18 6.839 9.504.5.092.682-.217.682-.483 0-.237-.008-.868-.013-1.703-2.782.605-3.369-1.343-3.369-1.343-.454-1.158-1.11-1.466-1.11-1.466-.908-.62.069-.608.069-.608 1.003.07 1.531 1.032 1.531 1.032.892 1.53 2.341 1.088 2.91.832.092-.647.35-1.088.636-1.338-2.22-.253-4.555-1.113-4.555-4.951 0-1.093.39-1.988 1.029-2.688-.103-.253-.446-1.272.098-2.65 0 0 .84-.27 2.75 1.026A9.564 9.564 0 0112 6.844c.85.004 1.705.115 2.504.337 1.909-1.296 2.747-1.027 2.747-1.027.546 1.379.202 2.398.1 2.651.64.7 1.028 1.595 1.028 2.688 0 3.848-2.339 4.695-4.566 4.943.359.309.678.92.678 1.855 0 1.338-.012 2.419-.012 2.747 0 .268.18.58.688.482A10.019 10.019 0 0022 12.017C22 6.484 17.522 2 12 2z" clipRule="evenodd"/></svg>
              GitHub Login
            </button>
            <button onClick={googleLogin} className="w-full flex items-center justify-center gap-2 py-3 px-6 rounded-xl bg-white text-gray-800 hover:bg-gray-100 transition font-medium">
              <svg className="w-5 h-5" viewBox="0 0 24 24"><path fill="#4285F4" d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92a5.06 5.06 0 01-2.2 3.32v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.1z"/><path fill="#34A853" d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84A11 11 0 0012 23z"/><path fill="#FBBC05" d="M5.84 14.1a6.6 6.6 0 010-4.2V7.06H2.18a11 11 0 000 9.88l3.66-2.84z"/><path fill="#EA4335" d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15A11 11 0 002.18 7.06L5.84 9.9C6.71 7.3 9.14 5.38 12 5.38z"/></svg>
              Sign in with Google
            </button>
            <button onClick={authingLogin} className={btn + ' bg-blue-600 hover:bg-blue-700'}>
              Email / Phone Login
            </button>
            <button onClick={metamaskLogin} disabled={loading} className={btn + ' bg-orange-600 hover:bg-orange-700 disabled:opacity-50'}>
              {loading ? 'Connecting...' : 'MetaMask Wallet'}
            </button>
          </>
        )}

        <button onClick={() => { setRegion(null); setError('') }}
          className="w-full text-center text-xs text-gray-400 hover:text-white transition pt-2">
          {region === 'cn' ? '切换到国际版 / Switch' : 'Switch to 中国大陆版'}
        </button>
        <p className="text-center text-xs text-gray-500">首次登录自动注册</p>
      </div>
    </div>
  )
}

export default Login
