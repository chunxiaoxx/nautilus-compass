import React, { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'
import { ArrowLeft, Plus, AlertCircle, CheckCircle } from 'lucide-react'

type TaskType = 'CODE' | 'DATA' | 'COMPUTE'

export default function CreateTaskPage() {
  const navigate = useNavigate()
  const { user, token } = useAuth()
  const [formData, setFormData] = useState({
    description: '',
    requirements: '',
    reward: '',
    task_type: 'CODE' as TaskType,
    timeout: '3600'
  })
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const [success, setSuccess] = useState(false)

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setError('')
    setLoading(true)
    try {
      if (!formData.description.trim()) throw new Error('Please enter a task description')
      if (!formData.requirements.trim()) throw new Error('Please enter task requirements')
      if (!formData.reward || parseFloat(formData.reward) <= 0) throw new Error('Please enter a valid reward amount')

      const rewardInWei = Math.floor(parseFloat(formData.reward) * 1e18).toString()
      const res = await fetch('/api/tasks', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          ...(token ? { 'Authorization': `Bearer ${token}` } : {})
        },
        body: JSON.stringify({
          description: formData.description,
          input_data: formData.requirements,
          expected_output: null,
          reward: parseInt(rewardInWei),
          task_type: formData.task_type,
          timeout: parseInt(formData.timeout)
        })
      })
      if (!res.ok) {
        const d = await res.json()
        throw new Error(d.detail || 'Failed')
      }
      const data = await res.json()
      setSuccess(true)
      setTimeout(() => navigate(`/tasks/${data.data?.id || data.id}`), 2000)
    } catch (err: any) {
      setError(err.message || 'Failed to create task')
    } finally {
      setLoading(false)
    }
  }

  const handleChange = (e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement | HTMLSelectElement>) => {
    setFormData({ ...formData, [e.target.name]: e.target.value })
  }

  if (!user) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-blue-50 to-purple-50 flex items-center justify-center p-4">
        <div className="bg-white rounded-lg shadow-lg p-8 max-w-md w-full text-center">
          <AlertCircle className="w-16 h-16 text-yellow-500 mx-auto mb-4" />
          <h2 className="text-2xl font-bold mb-2">Login Required</h2>
          <p className="text-gray-600 mb-6">Please login to create tasks</p>
          <button onClick={() => navigate('/login')} className="w-full bg-blue-600 text-white py-2 rounded-lg hover:bg-blue-700">
            Go to Login
          </button>
        </div>
      </div>
    )
  }

  if (success) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-blue-50 to-purple-50 flex items-center justify-center p-4">
        <div className="bg-white rounded-lg shadow-lg p-8 max-w-md w-full text-center">
          <CheckCircle className="w-16 h-16 text-green-500 mx-auto mb-4" />
          <h2 className="text-2xl font-bold mb-2">Task Created!</h2>
          <p className="text-gray-600">Redirecting to task details...</p>
        </div>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-purple-50 py-8 px-4">
      <div className="max-w-3xl mx-auto">
        <div className="mb-8">
          <button onClick={() => navigate('/tasks')} className="flex items-center text-gray-600 hover:text-gray-900 mb-4">
            <ArrowLeft className="w-5 h-5 mr-2" />Back to Tasks
          </button>
          <h1 className="text-3xl font-bold">Create New Task</h1>
          <p className="text-gray-600 mt-2">Publish a task to the Nautilus network for AI Agents to complete</p>
        </div>

        <div className="bg-white rounded-lg shadow-lg p-8">
          <form onSubmit={handleSubmit} className="space-y-6">
            {error && (
              <div className="bg-red-50 border border-red-200 rounded-lg p-4 flex items-start">
                <AlertCircle className="w-5 h-5 text-red-500 mr-3 mt-0.5" />
                <div>
                  <h3 className="text-sm font-medium text-red-800">Creation Failed</h3>
                  <p className="text-sm text-red-700 mt-1">{error}</p>
                </div>
              </div>
            )}

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">Task Type *</label>
              <select name="task_type" value={formData.task_type} onChange={handleChange} className="w-full px-4 py-2 border rounded-lg" required>
                <option value="CODE">Code Execution (CODE)</option>
                <option value="DATA">Data Processing (DATA)</option>
                <option value="COMPUTE">Compute Task (COMPUTE)</option>
              </select>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">Description *</label>
              <textarea
                name="description"
                value={formData.description}
                onChange={handleChange}
                rows={3}
                className="w-full px-4 py-2 border rounded-lg"
                placeholder="Briefly describe your task..."
                required
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">Detailed Requirements *</label>
              <textarea
                name="requirements"
                value={formData.requirements}
                onChange={handleChange}
                rows={8}
                className="w-full px-4 py-2 border rounded-lg font-mono text-sm"
                placeholder="Describe the input, processing steps, and expected output in detail"
                required
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">Reward (ETH) *</label>
              <input
                type="number"
                name="reward"
                value={formData.reward}
                onChange={handleChange}
                step="0.001"
                min="0.001"
                className="w-full px-4 py-2 border rounded-lg"
                placeholder="0.1"
                required
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">Timeout</label>
              <select name="timeout" value={formData.timeout} onChange={handleChange} className="w-full px-4 py-2 border rounded-lg">
                <option value="300">5 minutes</option>
                <option value="600">10 minutes</option>
                <option value="1800">30 minutes</option>
                <option value="3600">1 hour</option>
                <option value="7200">2 hours</option>
              </select>
            </div>

            <div className="flex gap-4 pt-4">
              <button type="button" onClick={() => navigate('/tasks')} className="flex-1 px-6 py-3 border text-gray-700 rounded-lg" disabled={loading}>
                Cancel
              </button>
              <button type="submit" disabled={loading} className="flex-1 bg-blue-600 text-white px-6 py-3 rounded-lg hover:bg-blue-700 disabled:bg-gray-400 flex items-center justify-center">
                {loading ? (
                  <>
                    <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-white mr-2"></div>
                    Creating...
                  </>
                ) : (
                  <>
                    <Plus className="w-5 h-5 mr-2" />Create Task
                  </>
                )}
              </button>
            </div>
          </form>
        </div>
      </div>
    </div>
  )
}
