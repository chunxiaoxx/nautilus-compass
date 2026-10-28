import { useState, useEffect } from 'react'

const API_URL = import.meta.env.VITE_API_URL || ''

interface Transaction {
  id: number
  type: string
  amount: number
  balance_after: number
  description: string
  created_at: string
}

export default function BillingPage() {
  const [balance, setBalance] = useState<number | null>(null)
  const [totalDeposited, setTotalDeposited] = useState(0)
  const [totalSpent, setTotalSpent] = useState(0)
  const [transactions, setTransactions] = useState<Transaction[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  const token = localStorage.getItem('token')

  useEffect(() => {
    if (!token) {
      setError('请先登录')
      setLoading(false)
      return
    }
    const headers = { Authorization: `Bearer ${token}` }

    Promise.all([
      fetch(`${API_URL}/api/payments/balance`, { headers }).then(r => r.json()),
      fetch(`${API_URL}/api/payments/transactions?limit=20`, { headers }).then(r => r.json()),
    ])
      .then(([bal, txs]) => {
        if (bal.balance !== undefined) {
          setBalance(bal.balance)
          setTotalDeposited(bal.total_deposited || 0)
          setTotalSpent(bal.total_spent || 0)
        }
        if (txs.success && txs.data) {
          setTransactions(txs.data)
        }
      })
      .catch(() => setError('加载失败'))
      .finally(() => setLoading(false))
  }, [token])

  const typeLabel = (t: string) => {
    if (t === 'deposit') return '充值'
    if (t === 'task_charge') return '任务扣费'
    if (t === 'refund') return '退款'
    return t
  }

  const typeColor = (t: string) => {
    if (t === 'deposit') return 'text-green-400'
    if (t === 'task_charge') return 'text-red-400'
    if (t === 'refund') return 'text-blue-400'
    return 'text-gray-400'
  }

  if (loading) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-gray-900 via-blue-900 to-purple-900 flex items-center justify-center">
        <p className="text-gray-400">加载中...</p>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-900 via-blue-900 to-purple-900">
      <div className="max-w-4xl mx-auto px-4 py-12">
        <h1 className="text-3xl font-bold text-white mb-8">账户余额</h1>

        {error && <p className="text-red-400 mb-4">{error}</p>}

        {/* Balance Card */}
        <div className="grid md:grid-cols-3 gap-6 mb-10">
          <div className="bg-white/10 backdrop-blur-lg border border-white/20 rounded-xl p-6 text-center">
            <div className="text-sm text-gray-400 mb-1">当前余额</div>
            <div className="text-3xl font-bold text-white">{balance?.toFixed(2) ?? '0.00'}</div>
            <div className="text-xs text-gray-500 mt-1">RMB</div>
          </div>
          <div className="bg-white/10 backdrop-blur-lg border border-white/20 rounded-xl p-6 text-center">
            <div className="text-sm text-gray-400 mb-1">累计充值</div>
            <div className="text-2xl font-bold text-green-400">{totalDeposited.toFixed(2)}</div>
            <div className="text-xs text-gray-500 mt-1">RMB</div>
          </div>
          <div className="bg-white/10 backdrop-blur-lg border border-white/20 rounded-xl p-6 text-center">
            <div className="text-sm text-gray-400 mb-1">累计消费</div>
            <div className="text-2xl font-bold text-red-400">{totalSpent.toFixed(2)}</div>
            <div className="text-xs text-gray-500 mt-1">RMB</div>
          </div>
        </div>

        {/* Deposit Info */}
        <div className="bg-white/10 backdrop-blur-lg border border-white/20 rounded-xl p-6 mb-10">
          <h2 className="text-lg font-semibold text-white mb-3">充值方式</h2>
          <div className="space-y-2 text-sm text-gray-300">
            <p>1. 银行转账 / 支付宝 / 微信转账到平台账户</p>
            <p>2. 将转账截图和您的用户ID发送给客服</p>
            <p>3. 管理员确认后自动到账（通常 1 小时内）</p>
          </div>
          <div className="mt-4 p-3 bg-blue-500/10 border border-blue-500/30 rounded-lg text-sm text-blue-300">
            大额充值 (10000+ RMB) 可享额外 5% 优惠。联系客服获取详情。
          </div>
        </div>

        {/* Transaction History */}
        <h2 className="text-lg font-semibold text-white mb-4">交易记录</h2>
        {transactions.length === 0 ? (
          <p className="text-gray-400 text-center py-8">暂无交易记录</p>
        ) : (
          <div className="space-y-2">
            {transactions.map(tx => (
              <div
                key={tx.id}
                className="bg-white/10 backdrop-blur-lg border border-white/20 rounded-lg p-4 flex items-center justify-between"
              >
                <div>
                  <span className={`text-sm font-medium ${typeColor(tx.type)}`}>
                    {typeLabel(tx.type)}
                  </span>
                  {tx.description && (
                    <span className="text-xs text-gray-500 ml-2">{tx.description}</span>
                  )}
                  <div className="text-xs text-gray-500 mt-0.5">
                    {tx.created_at?.split('T')[0]}
                  </div>
                </div>
                <div className="text-right">
                  <div className={`font-medium ${tx.amount > 0 ? 'text-green-400' : 'text-red-400'}`}>
                    {tx.amount > 0 ? '+' : ''}{tx.amount.toFixed(2)}
                  </div>
                  <div className="text-xs text-gray-500">余额: {tx.balance_after?.toFixed(2)}</div>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  )
}
