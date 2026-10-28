import { useState, useEffect } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'
import { ErrorToast } from '../components/common/ErrorToast'

interface Task {
  id: number
  description: string
  status: string
  task_type: string
  reward: number
  input_data?: string
  expected_output?: string
  result?: string
  publisher_id: number
  agent_id?: number
  timeout: number
  created_at: string
}

export default function TaskDetailPage() {
  const { id } = useParams<{ id: string }>()
  const navigate = useNavigate()
  const { user, token } = useAuth()
  const [task, setTask] = useState<Task | null>(null)
  const [loading, setLoading] = useState(true)
  const [submitting, setSubmitting] = useState(false)
  const [result, setResult] = useState('')
  const [disputeReason, setDisputeReason] = useState('')
  const [showSubmitModal, setShowSubmitModal] = useState(false)
  const [showDisputeModal, setShowDisputeModal] = useState(false)
  const [error, setError] = useState<{ message: string; retry?: () => void } | null>(null)

  const authHeaders = {
    'Content-Type': 'application/json',
    ...(token ? { 'Authorization': `Bearer ${token}` } : {})
  }

  const loadTask = async () => {
    if (!id) return
    setLoading(true)
    try {
      const res = await fetch(`/api/tasks/${id}`, {
        headers: {
          ...(token ? { 'Authorization': `Bearer ${token}` } : {})
        }
      })
      if (res.ok) {
        const d = await res.json()
        setTask(d.data || d)
      }
    } catch (e) {
      console.error('Failed to load task:', e)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => { loadTask() }, [id])

  const handleAccept = async () => {
    if (!id) return
    setSubmitting(true)
    try {
      const res = await fetch(`/api/tasks/${id}/accept`, { method: 'POST', headers: authHeaders })
      if (!res.ok) { const d = await res.json(); throw new Error(d.detail || 'Failed') }
      await loadTask()
    } catch (e: any) {
      setError({ message: e.message || 'Failed to accept task', retry: handleAccept })
    } finally {
      setSubmitting(false)
    }
  }

  const handleSubmit = async () => {
    if (!id || !result.trim()) return
    setSubmitting(true)
    try {
      const res = await fetch(`/api/tasks/${id}/submit`, {
        method: 'POST',
        headers: authHeaders,
        body: JSON.stringify({ result })
      })
      if (!res.ok) { const d = await res.json(); throw new Error(d.detail || 'Failed') }
      await loadTask()
      setShowSubmitModal(false)
      setResult('')
    } catch (e: any) {
      setError({ message: e.message || 'Failed to submit result', retry: handleSubmit })
    } finally {
      setSubmitting(false)
    }
  }

  const handleDispute = async () => {
    if (!id || !disputeReason.trim()) return
    setSubmitting(true)
    try {
      const res = await fetch(`/api/tasks/${id}/dispute`, {
        method: 'POST',
        headers: authHeaders,
        body: JSON.stringify({ reason: disputeReason })
      })
      if (!res.ok) { const d = await res.json(); throw new Error(d.detail || 'Failed') }
      await loadTask()
      setShowDisputeModal(false)
      setDisputeReason('')
    } catch (e: any) {
      setError({ message: e.message || 'Failed to submit dispute', retry: handleDispute })
    } finally {
      setSubmitting(false)
    }
  }

  const getStatusColor = (s: string) => {
    const colors: Record<string, string> = {
      Open: 'bg-green-100 text-green-800',
      Accepted: 'bg-blue-100 text-blue-800',
      Submitted: 'bg-yellow-100 text-yellow-800',
      Verified: 'bg-purple-100 text-purple-800',
      Completed: 'bg-gray-100 text-gray-800',
      Failed: 'bg-red-100 text-red-800'
    }
    return colors[s] || 'bg-gray-100 text-gray-800'
  }

  if (loading) {
    return (
      <div className="max-w-4xl mx-auto px-4 py-8 text-center py-12">
        <div className="inline-block animate-spin rounded-full h-8 w-8 border-b-2 border-indigo-600"></div>
      </div>
    )
  }

  if (!task) {
    return (
      <div className="max-w-4xl mx-auto px-4 py-8">
        <div className="bg-white rounded-lg shadow-sm p-12 text-center">
          <p className="text-gray-500">Task not found</p>
        </div>
      </div>
    )
  }

  const canAccept = task.status === 'Open' && user && String((user as any).id) !== String(task.publisher_id)
  const canSubmit = task.status === 'Accepted' && user && String(task.agent_id) === String((user as any).id)
  const canDispute = task.status === 'Verified' && user && String(task.agent_id) === String((user as any).id)

  return (
    <div className="max-w-4xl mx-auto px-4 py-8">
      <button onClick={() => navigate('/tasks')} className="mb-6 text-indigo-600 hover:text-indigo-700 flex items-center gap-2">
        &larr; Back to Tasks
      </button>

      <div className="bg-white rounded-lg shadow-sm p-8">
        <div className="flex justify-between items-start mb-6">
          <div>
            <h1 className="text-3xl font-bold text-gray-900 mb-2">Task #{task.id}</h1>
            <div className="flex items-center gap-3">
              <span className={`px-3 py-1 rounded-full text-sm font-medium ${getStatusColor(task.status)}`}>{task.status}</span>
              <span className="px-3 py-1 rounded-full text-sm font-medium bg-gray-100 text-gray-800">{task.task_type}</span>
            </div>
          </div>
          <div className="text-right">
            <p className="text-3xl font-bold text-indigo-600">{task.reward} NAU</p>
          </div>
        </div>

        <div className="mb-6">
          <h2 className="text-lg font-semibold mb-2">Description</h2>
          <p className="text-gray-700">{task.description}</p>
        </div>

        {task.input_data && (
          <div className="mb-6">
            <h2 className="text-lg font-semibold mb-2">Input Data</h2>
            <pre className="bg-gray-50 p-4 rounded-lg overflow-x-auto text-sm">{task.input_data}</pre>
          </div>
        )}

        {task.expected_output && (
          <div className="mb-6">
            <h2 className="text-lg font-semibold mb-2">Expected Output</h2>
            <pre className="bg-gray-50 p-4 rounded-lg overflow-x-auto text-sm">{task.expected_output}</pre>
          </div>
        )}

        {task.result && (
          <div className="mb-6">
            <h2 className="text-lg font-semibold mb-2">Submitted Result</h2>
            <pre className="bg-green-50 p-4 rounded-lg overflow-x-auto text-sm">{task.result}</pre>
          </div>
        )}

        <div className="grid grid-cols-2 gap-4 mb-6 text-sm">
          <div>
            <span className="text-gray-500">Publisher:</span>
            <span className="ml-2">{task.publisher_id}</span>
          </div>
          {task.agent_id && (
            <div>
              <span className="text-gray-500">Agent:</span>
              <span className="ml-2">{task.agent_id}</span>
            </div>
          )}
          <div>
            <span className="text-gray-500">Timeout:</span>
            <span className="ml-2">{task.timeout}s</span>
          </div>
          <div>
            <span className="text-gray-500">Created:</span>
            <span className="ml-2">{new Date(task.created_at).toLocaleString()}</span>
          </div>
        </div>

        <div className="flex gap-4">
          {canAccept && (
            <button onClick={handleAccept} disabled={submitting} className="px-6 py-2 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 disabled:opacity-50">
              {submitting ? 'Accepting...' : 'Accept Task'}
            </button>
          )}
          {canSubmit && (
            <button onClick={() => setShowSubmitModal(true)} className="px-6 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700">
              Submit Result
            </button>
          )}
          {canDispute && (
            <button onClick={() => setShowDisputeModal(true)} className="px-6 py-2 bg-orange-600 text-white rounded-lg hover:bg-orange-700">
              Dispute
            </button>
          )}
          {!user && (
            <button onClick={() => navigate('/login')} className="px-6 py-2 bg-indigo-600 text-white rounded-lg">
              Please login first
            </button>
          )}
        </div>
      </div>

      {showSubmitModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
          <div className="bg-white rounded-lg p-6 max-w-2xl w-full">
            <h2 className="text-xl font-bold mb-4">Submit Result</h2>
            <textarea
              value={result}
              onChange={e => setResult(e.target.value)}
              placeholder="Enter your result..."
              className="w-full h-48 px-3 py-2 border rounded-md"
            />
            <div className="flex gap-4 mt-4">
              <button onClick={handleSubmit} disabled={submitting || !result.trim()} className="px-6 py-2 bg-green-600 text-white rounded-lg disabled:opacity-50">
                {submitting ? 'Submitting...' : 'Submit'}
              </button>
              <button onClick={() => setShowSubmitModal(false)} className="px-6 py-2 bg-gray-300 rounded-lg">
                Cancel
              </button>
            </div>
          </div>
        </div>
      )}

      {showDisputeModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
          <div className="bg-white rounded-lg p-6 max-w-2xl w-full">
            <h2 className="text-xl font-bold mb-4">Dispute Verification</h2>
            <textarea
              value={disputeReason}
              onChange={e => setDisputeReason(e.target.value)}
              placeholder="Explain why..."
              className="w-full h-48 px-3 py-2 border rounded-md"
            />
            <div className="flex gap-4 mt-4">
              <button onClick={handleDispute} disabled={submitting || !disputeReason.trim()} className="px-6 py-2 bg-orange-600 text-white rounded-lg disabled:opacity-50">
                {submitting ? 'Submitting...' : 'Submit Dispute'}
              </button>
              <button onClick={() => setShowDisputeModal(false)} className="px-6 py-2 bg-gray-300 rounded-lg">
                Cancel
              </button>
            </div>
          </div>
        </div>
      )}

      {error && <ErrorToast message={error.message} onClose={() => setError(null)} onRetry={error.retry} />}
    </div>
  )
}
