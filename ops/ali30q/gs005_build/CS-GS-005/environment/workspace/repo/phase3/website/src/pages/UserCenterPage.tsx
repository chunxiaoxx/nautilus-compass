import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'
import { User, Wallet, Mail, TrendingUp, Clock, Award, Activity, LogOut, Edit2, Save, X } from 'lucide-react'

interface UserStats {
  total_tasks: number
  completed_tasks: number
  failed_tasks: number
  total_earnings: number
  total_spent: number
  reputation: number
}

interface Task {
  id: number
  description: string
  status: string
  task_type: string
  reward: number
  publisher?: string
  agent?: string
  created_at: string
}

export default function UserCenterPage() {
  const navigate = useNavigate()
  const { user, token, logout } = useAuth()
  const [stats, setStats] = useState<UserStats>({
    total_tasks: 0,
    completed_tasks: 0,
    failed_tasks: 0,
    total_earnings: 0,
    total_spent: 0,
    reputation: 100
  })
  const [recentTasks, setRecentTasks] = useState<Task[]>([])
  const [loading, setLoading] = useState(true)
  const [editMode, setEditMode] = useState(false)
  const [walletAddress, setWalletAddress] = useState((user as any)?.wallet_address || '')
  const [saving, setSaving] = useState(false)
  const [message, setMessage] = useState('')

  useEffect(() => {
    if (!user) { navigate('/login'); return }
    const load = async () => {
      setLoading(true)
      try {
        const res = await fetch('/api/tasks', {
          headers: {
            ...(token ? { 'Authorization': `Bearer ${token}` } : {})
          }
        })
        if (!res.ok) throw new Error('Failed')
        const data = await res.json()
        const tasks: Task[] = Array.isArray(data) ? data : (data.data || [])
        setRecentTasks(tasks.slice(0, 5))
        const completed = tasks.filter(t => t.status === 'Completed').length
        const failed = tasks.filter(t => t.status === 'Failed').length
        setStats({
          total_tasks: tasks.length,
          completed_tasks: completed,
          failed_tasks: failed,
          total_earnings: 0,
          total_spent: 0,
          reputation: 100 + completed * 10 - failed * 5
        })
      } catch (e) {
        console.error('Failed to load:', e)
      } finally {
        setLoading(false)
      }
    }
    load()
  }, [user, token])

  const handleSaveWallet = async () => {
    setSaving(true)
    setMessage('')
    try {
      const res = await fetch('/api/auth/me/wallet', {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
          ...(token ? { 'Authorization': `Bearer ${token}` } : {})
        },
        body: JSON.stringify({ wallet_address: walletAddress })
      })
      if (res.ok) {
        setMessage('Wallet address saved')
        setEditMode(false)
        setTimeout(() => setMessage(''), 3000)
      } else {
        throw new Error('Failed')
      }
    } catch (e: any) {
      setMessage('Save failed: ' + e.message)
    } finally {
      setSaving(false)
    }
  }

  const handleLogout = () => {
    logout()
    navigate('/login')
  }

  const getStatusColor = (s: string) => {
    const colors: Record<string, string> = {
      Open: 'bg-green-100 text-green-800',
      Accepted: 'bg-blue-100 text-blue-800',
      Submitted: 'bg-yellow-100 text-yellow-800',
      Completed: 'bg-gray-100 text-gray-800',
      Failed: 'bg-red-100 text-red-800'
    }
    return colors[s] || 'bg-gray-100 text-gray-800'
  }

  const formatEth = (wei: number) => (wei / 1e18).toFixed(4)

  if (!user) return null

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-purple-50 py-8 px-4">
      <div className="max-w-7xl mx-auto">
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-gray-900">User Center</h1>
          <p className="text-gray-600 mt-2">Manage your account and tasks</p>
        </div>

        {message && (
          <div className={`mb-6 p-4 rounded-lg ${message.includes('failed') || message.includes('Failed') ? 'bg-red-50 text-red-800 border border-red-200' : 'bg-green-50 text-green-800 border border-green-200'}`}>
            {message}
          </div>
        )}

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          <div className="lg:col-span-1 space-y-6">
            <div className="bg-white rounded-lg shadow-lg p-6">
              <div className="flex items-center justify-between mb-6">
                <h2 className="text-xl font-bold">Profile</h2>
                <button onClick={handleLogout} className="text-red-600 hover:text-red-700 flex items-center text-sm">
                  <LogOut className="w-4 h-4 mr-1" />Logout
                </button>
              </div>
              <div className="space-y-4">
                <div className="flex justify-center">
                  <div className="w-24 h-24 bg-gradient-to-br from-blue-500 to-purple-500 rounded-full flex items-center justify-center">
                    <User className="w-12 h-12 text-white" />
                  </div>
                </div>
                <div className="text-center">
                  <h3 className="text-xl font-bold">{(user as any).username || (user as any).email}</h3>
                  <p className="text-sm text-gray-500">ID: {(user as any).id}</p>
                </div>
                {(user as any).email && (
                  <div className="flex items-center text-gray-600">
                    <Mail className="w-5 h-5 mr-3 text-gray-400" />
                    <span className="text-sm">{(user as any).email}</span>
                  </div>
                )}

                <div className="pt-4 border-t">
                  <div className="flex items-center justify-between mb-2">
                    <label className="text-sm font-medium text-gray-700 flex items-center">
                      <Wallet className="w-4 h-4 mr-2" />Wallet Address
                    </label>
                    {!editMode && (
                      <button onClick={() => setEditMode(true)} className="text-blue-600 text-sm flex items-center">
                        <Edit2 className="w-3 h-3 mr-1" />Edit
                      </button>
                    )}
                  </div>
                  {editMode ? (
                    <div className="space-y-2">
                      <input
                        type="text"
                        value={walletAddress}
                        onChange={e => setWalletAddress(e.target.value)}
                        className="w-full px-3 py-2 border rounded-lg text-sm"
                        placeholder="0x..."
                      />
                      <div className="flex gap-2">
                        <button
                          onClick={handleSaveWallet}
                          disabled={saving}
                          className="flex-1 bg-blue-600 text-white py-2 rounded-lg text-sm disabled:bg-gray-400 flex items-center justify-center"
                        >
                          <Save className="w-4 h-4 mr-1" />Save
                        </button>
                        <button
                          onClick={() => { setEditMode(false); setWalletAddress((user as any).wallet_address || '') }}
                          className="flex-1 border text-gray-700 py-2 rounded-lg text-sm flex items-center justify-center"
                        >
                          <X className="w-4 h-4 mr-1" />Cancel
                        </button>
                      </div>
                    </div>
                  ) : (
                    <p className="text-sm text-gray-600 break-all">{(user as any).wallet_address || 'Not set'}</p>
                  )}
                </div>

                <div className="pt-4 border-t">
                  <div className="flex items-center justify-between">
                    <span className="text-sm font-medium flex items-center">
                      <Award className="w-4 h-4 mr-2" />Reputation
                    </span>
                    <span className="text-lg font-bold text-blue-600">{stats.reputation}</span>
                  </div>
                  <div className="mt-2 bg-gray-200 rounded-full h-2">
                    <div
                      className="bg-gradient-to-r from-blue-500 to-purple-500 h-2 rounded-full"
                      style={{ width: `${Math.min(stats.reputation, 100)}%` }}
                    ></div>
                  </div>
                </div>
              </div>
            </div>

            <div className="bg-white rounded-lg shadow-lg p-6">
              <h2 className="text-lg font-bold mb-4">Quick Actions</h2>
              <div className="space-y-2">
                <button onClick={() => navigate('/tasks/create')} className="w-full bg-blue-600 text-white py-3 rounded-lg hover:bg-blue-700 flex items-center justify-center">
                  <Activity className="w-5 h-5 mr-2" />Create New Task
                </button>
                <button onClick={() => navigate('/tasks')} className="w-full border text-gray-700 py-3 rounded-lg hover:bg-gray-50 flex items-center justify-center">
                  <TrendingUp className="w-5 h-5 mr-2" />Browse Marketplace
                </button>
              </div>
            </div>
          </div>

          <div className="lg:col-span-2 space-y-6">
            <div className="grid grid-cols-2 gap-4">
              <div className="bg-white rounded-lg shadow-lg p-6">
                <p className="text-sm text-gray-600">Total Tasks</p>
                <p className="text-3xl font-bold mt-1">{stats.total_tasks}</p>
              </div>
              <div className="bg-white rounded-lg shadow-lg p-6">
                <p className="text-sm text-gray-600">Completed</p>
                <p className="text-3xl font-bold text-green-600 mt-1">{stats.completed_tasks}</p>
              </div>
              <div className="bg-white rounded-lg shadow-lg p-6">
                <p className="text-sm text-gray-600">Total Earnings</p>
                <p className="text-2xl font-bold text-purple-600 mt-1">{formatEth(stats.total_earnings)} ETH</p>
              </div>
              <div className="bg-white rounded-lg shadow-lg p-6">
                <p className="text-sm text-gray-600">Total Spent</p>
                <p className="text-2xl font-bold text-orange-600 mt-1">{formatEth(stats.total_spent)} ETH</p>
              </div>
            </div>

            <div className="bg-white rounded-lg shadow-lg p-6">
              <div className="flex items-center justify-between mb-6">
                <h2 className="text-xl font-bold">Recent Tasks</h2>
                <button onClick={() => navigate('/tasks')} className="text-blue-600 text-sm">View all &rarr;</button>
              </div>
              {loading ? (
                <div className="flex justify-center py-8">
                  <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
                </div>
              ) : recentTasks.length === 0 ? (
                <div className="text-center py-8 text-gray-500">
                  <Clock className="w-12 h-12 mx-auto mb-3 text-gray-400" />
                  <p>No tasks yet</p>
                </div>
              ) : (
                <div className="space-y-3">
                  {recentTasks.map(task => (
                    <div
                      key={task.id}
                      onClick={() => navigate(`/tasks/${task.id}`)}
                      className="border rounded-lg p-4 hover:border-blue-300 hover:shadow-md cursor-pointer transition-all"
                    >
                      <div className="flex justify-between">
                        <div>
                          <div className="flex items-center gap-2 mb-2">
                            <span className={`px-2 py-1 rounded text-xs font-medium ${getStatusColor(task.status)}`}>{task.status}</span>
                            <span className="px-2 py-1 bg-gray-100 rounded text-xs">{task.task_type}</span>
                          </div>
                          <p className="text-sm font-medium">{task.description}</p>
                          <p className="text-xs text-gray-500 mt-1">{new Date(task.created_at).toLocaleString()}</p>
                        </div>
                        <p className="text-sm font-bold text-blue-600">{formatEth(task.reward)} ETH</p>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
