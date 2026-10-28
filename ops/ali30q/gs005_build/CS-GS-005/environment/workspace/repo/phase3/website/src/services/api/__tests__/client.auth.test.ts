import { describe, it, expect, beforeEach } from 'vitest'
import { tokenUtils } from '../../../utils/token'
import { apiClient } from '../client'

/**
 * 登录失效根因回归测试。
 * 生产 HTTPS 上 apiClient 此前:
 *   1) baseURL = http://43.160.239.61:8000 → mixed-content 阻断
 *   2) 拦截器读 TokenManager 的 `nautilus_token`,而真实登录路径(OAuth/钱包/AuthContext)
 *      把 token 存在 tokenUtils 的 `nautilus_auth_token` → 请求永不带 Authorization → /auth/me 401 → 登出
 */
// The global test setup stubs localStorage to a no-op (getItem → null).
// Install a real in-memory store so tokenUtils persistence can be exercised.
function memoryStorage(): Storage {
  const m = new Map<string, string>()
  return {
    getItem: (k: string) => (m.has(k) ? m.get(k)! : null),
    setItem: (k: string, v: string) => void m.set(k, String(v)),
    removeItem: (k: string) => void m.delete(k),
    clear: () => m.clear(),
    key: (i: number) => Array.from(m.keys())[i] ?? null,
    get length() {
      return m.size
    },
  } as Storage
}

describe('apiClient auth wiring', () => {
  beforeEach(() => {
    global.localStorage = memoryStorage()
    global.sessionStorage = memoryStorage()
  })

  it('uses a same-origin base (not the hard-coded http IP:8000 → no mixed-content)', () => {
    const base = String(apiClient.defaults.baseURL ?? '')
    expect(base).not.toContain('43.160.239.61')
    expect(base.startsWith('http://')).toBe(false)
  })

  it('attaches Bearer token saved by tokenUtils (nautilus_auth_token) to outgoing requests', async () => {
    tokenUtils.save('test-jwt-abc', true)
    expect(tokenUtils.get()).toBe('test-jwt-abc') // sanity: storage works in test env
    // run the request interceptor the way axios would
    const handlers = (apiClient.interceptors.request as unknown as {
      handlers: Array<{ fulfilled: (c: { headers: Record<string, string> }) => unknown } | null>
    }).handlers
    const fulfilled = handlers.find((h) => h && h.fulfilled)!.fulfilled
    const cfg = (await fulfilled({ headers: {} })) as { headers: Record<string, string> }
    expect(cfg.headers.Authorization).toBe('Bearer test-jwt-abc')
  })
})
