import { useEffect } from 'react'
import { useSearchParams, useNavigate } from 'react-router-dom'
import { tokenUtils } from '../utils/token'

/**
 * OAuth callback handler.
 * Receives token from backend after Google/GitHub OAuth,
 * saves it to localStorage, and redirects to home.
 */
const OAuthCallback = () => {
  const [params] = useSearchParams()
  const navigate = useNavigate()

  useEffect(() => {
    const token = params.get('token')
    if (token) {
      tokenUtils.save(token, true)
      // 🔴 整页跳转(非 SPA navigate)· OAuth 登录回首页未登录态的根因修复:
      // AuthProvider 在 Router 外层,checkAuth 只在 mount 跑一次;此页是整页加载,
      // checkAuth 在 token 存入前已跑完(认作未登录)。若用 SPA navigate('/') 不重挂载
      // Provider → 永远停在未登录态。改用 location.replace 强制重载,让 AuthProvider
      // 重挂载并读到刚存的 token → /api/auth/me → 登录态生效。
      // 2026-10-10 UNIFY 1.2: ?redirect= 跨站回跳(安全校验同 Login.tsx,防 open redirect)
      const rd = params.get('redirect')
      const target = rd && rd.startsWith('/') && !rd.startsWith('//') ? rd : '/'
      window.location.replace(target)
    } else {
      navigate('/login', { replace: true })
    }
  }, [params, navigate])

  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-900">
      <p className="text-white">登录中...</p>
    </div>
  )
}

export default OAuthCallback
