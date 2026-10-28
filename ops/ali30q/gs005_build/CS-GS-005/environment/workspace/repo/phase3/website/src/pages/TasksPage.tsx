import { useState, useEffect, useMemo } from 'react'
import { Link } from 'react-router-dom'
import { Search, X, Filter, ChevronDown, Sparkles } from 'lucide-react'
import { useAuth } from '../context/AuthContext'

interface Task {
  id: number
  description: string
  status: string
  task_type: string
  reward: number
  publisher_id: number
  agent_id?: number
  created_at: string
}

export default function TasksPage() {
  const { token } = useAuth()
  const [searchQuery, setSearchQuery] = useState('')
  const [debouncedSearch, setDebouncedSearch] = useState('')
  const [showAdvancedFilters, setShowAdvancedFilters] = useState(false)
  const [filters, setFilters] = useState({ status: '', task_type: '', minReward: 0, maxReward: 10000 })
  const [page, setPage] = useState(0)
  const [tasks, setTasks] = useState<Task[]>([])
  const [loading, setLoading] = useState(true)
  const limit = 12

  useEffect(() => {
    const fetchTasks = async () => {
      setLoading(true)
      try {
        const params = new URLSearchParams()
        if (filters.status) params.append('status', filters.status)
        if (filters.task_type) params.append('task_type', filters.task_type)
        params.append('skip', String(page * limit))
        params.append('limit', String(limit))
        const response = await fetch(`/api/tasks?${params}`, {
          headers: {
            ...(token ? { 'Authorization': `Bearer ${token}` } : {})
          }
        })
        const data = await response.json()
        setTasks(Array.isArray(data) ? data : (data.data || []))
      } catch (error) {
        console.error('Failed to load tasks:', error)
      } finally {
        setLoading(false)
      }
    }
    fetchTasks()
  }, [page, filters.status, filters.task_type, token])

  useEffect(() => {
    const timer = setTimeout(() => setDebouncedSearch(searchQuery), 300)
    return () => clearTimeout(timer)
  }, [searchQuery])

  const filteredTasks = useMemo(() => {
    let result = tasks
    if (debouncedSearch.trim()) {
      const q = debouncedSearch.toLowerCase()
      result = result.filter(t => t.description.toLowerCase().includes(q) || t.task_type.toLowerCase().includes(q))
    }
    result = result.filter(t => t.reward >= filters.minReward && t.reward <= filters.maxReward)
    return result
  }, [tasks, debouncedSearch, filters.minReward, filters.maxReward])

  const getStatusColor = (status: string) => {
    const colors: Record<string, string> = {
      Open: 'bg-green-500 text-white', Accepted: 'bg-blue-500 text-white', Submitted: 'bg-yellow-500 text-white',
      Verified: 'bg-purple-500 text-white', Completed: 'bg-gray-500 text-white', Failed: 'bg-red-500 text-white',
    }
    return colors[status] || 'bg-gray-500 text-white'
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 via-blue-50 to-indigo-50 relative">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 relative z-10">
        <div className="flex justify-between items-center mb-8">
          <div>
            <h1 className="text-4xl font-bold bg-gradient-to-r from-indigo-600 to-purple-600 bg-clip-text text-transparent">Task Marketplace</h1>
            <p className="text-gray-600 mt-2">Discover and accept high-value tasks</p>
          </div>
          <Link to="/tasks/create" className="px-6 py-3 bg-gradient-to-r from-indigo-600 to-purple-600 text-white rounded-xl hover:shadow-lg transition-all flex items-center gap-2">
            <Sparkles size={20} /> Create Task
          </Link>
        </div>

        <div className="backdrop-blur-xl bg-white/70 rounded-2xl shadow-xl border border-white/20 p-6 mb-6">
          <div className="relative mb-4">
            <Search size={24} className="absolute left-4 top-1/2 -translate-y-1/2 text-indigo-400" />
            <input value={searchQuery} onChange={e => setSearchQuery(e.target.value)} placeholder="Search task descriptions, types..." className="w-full pl-14 pr-14 py-4 text-lg border-2 border-indigo-100 rounded-xl focus:outline-none focus:ring-2 focus:ring-indigo-500 bg-white/50" />
            {searchQuery && <button onClick={() => { setSearchQuery(''); setDebouncedSearch('') }} className="absolute right-4 top-1/2 -translate-y-1/2"><X size={24} className="text-gray-400" /></button>}
          </div>
          <button onClick={() => setShowAdvancedFilters(!showAdvancedFilters)} className="flex items-center gap-2 text-indigo-600 font-medium">
            <Filter size={18} /> Advanced Filters <ChevronDown size={18} className={`transition-transform ${showAdvancedFilters ? 'rotate-180' : ''}`} />
          </button>
          {showAdvancedFilters && (
            <div className="grid grid-cols-2 gap-4 mt-4 pt-4 border-t border-indigo-100">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">Status</label>
                <select value={filters.status} onChange={e => setFilters({ ...filters, status: e.target.value })} className="w-full px-4 py-2 border border-indigo-100 rounded-lg">
                  <option value="">All Statuses</option>
                  {['Open','Accepted','Submitted','Verified','Completed','Failed'].map(s => <option key={s} value={s}>{s}</option>)}
                </select>
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">Task Type</label>
                <select value={filters.task_type} onChange={e => setFilters({ ...filters, task_type: e.target.value })} className="w-full px-4 py-2 border border-indigo-100 rounded-lg">
                  <option value="">All Types</option>
                  {['CODE','DATA','COMPUTE','RESEARCH','DESIGN','WRITING','OTHER'].map(t => <option key={t} value={t}>{t}</option>)}
                </select>
              </div>
            </div>
          )}
        </div>

        {loading ? (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            {[...Array(6)].map((_, i) => (
              <div key={i} className="bg-white/70 rounded-2xl shadow-xl p-6 animate-pulse">
                <div className="h-4 bg-gray-300 rounded w-3/4 mb-4"></div>
                <div className="h-20 bg-gray-300 rounded mb-4"></div>
                <div className="h-8 bg-gray-300 rounded w-24"></div>
              </div>
            ))}
          </div>
        ) : filteredTasks.length === 0 ? (
          <div className="bg-white/70 rounded-2xl shadow-xl p-12 text-center">
            <div className="w-24 h-24 mx-auto mb-4 bg-gray-100 rounded-full flex items-center justify-center">
              <Search size={40} className="text-gray-400" />
            </div>
            <p className="text-gray-600 mt-4">{debouncedSearch ? 'No matching tasks found' : 'No tasks available'}</p>
          </div>
        ) : (
          <>
            {debouncedSearch && <div className="mb-4 text-sm text-gray-600">Found <span className="font-semibold text-indigo-600">{filteredTasks.length}</span> matching tasks</div>}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              {filteredTasks.map(task => (
                <Link key={task.id} to={`/tasks/${task.id}`} className="group bg-white/70 rounded-2xl shadow-xl border-2 border-transparent hover:border-indigo-300 p-6 hover:shadow-2xl transition-all block">
                  <div className="flex items-center gap-2 mb-3">
                    <span className={`px-3 py-1 rounded-full text-xs font-bold ${getStatusColor(task.status)}`}>{task.status}</span>
                    <span className="px-3 py-1 rounded-full text-xs font-medium bg-gray-100 text-gray-700">{task.task_type}</span>
                  </div>
                  <p className="text-gray-900 font-medium line-clamp-3 mb-4">{task.description}</p>
                  <div className="flex justify-between items-end pt-4 border-t border-gray-200">
                    <div>
                      <p className="text-xs text-gray-500">Reward</p>
                      <p className="text-2xl font-bold text-indigo-600">{task.reward} <span className="text-xs text-gray-500">NAU</span></p>
                    </div>
                    <div className="text-right text-xs text-gray-400">
                      <p>Task #{task.id}</p>
                      <p>{new Date(task.created_at).toLocaleDateString()}</p>
                    </div>
                  </div>
                </Link>
              ))}
            </div>
          </>
        )}

        {!loading && filteredTasks.length > 0 && (
          <div className="mt-8 flex justify-center gap-2">
            <button onClick={() => setPage(Math.max(0, page - 1))} disabled={page === 0} className="px-6 py-3 bg-white border border-indigo-100 rounded-xl disabled:opacity-50 font-medium">Previous</button>
            <span className="px-6 py-3 bg-white border border-indigo-200 rounded-xl font-medium">Page {page + 1}</span>
            <button onClick={() => setPage(page + 1)} disabled={tasks.length < limit} className="px-6 py-3 bg-white border border-indigo-100 rounded-xl disabled:opacity-50 font-medium">Next</button>
          </div>
        )}
      </div>
    </div>
  )
}
