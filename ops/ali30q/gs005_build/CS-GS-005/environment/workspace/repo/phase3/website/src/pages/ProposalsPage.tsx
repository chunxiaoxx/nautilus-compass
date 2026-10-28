import { useState, useEffect, useCallback } from 'react'

interface Proposal {
  id: number
  task_id: number
  agent_id: number
  root_cause: string
  vote_score: number
  vote_count: number
  status: string
  created_at: string
}

const STATUS_COLORS: Record<string, string> = {
  pending: 'bg-gray-100 text-gray-700',
  voting: 'bg-blue-100 text-blue-700',
  accepted: 'bg-green-100 text-green-700',
  rejected: 'bg-red-100 text-red-700',
  deployed: 'bg-purple-100 text-purple-700',
}

const STATUS_OPTIONS = ['all', 'pending', 'voting', 'accepted', 'rejected'] as const

export default function ProposalsPage() {
  const [proposals, setProposals] = useState<Proposal[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [statusFilter, setStatusFilter] = useState('all')
  const [votingAgentId, setVotingAgentId] = useState('')
  const [votingId, setVotingId] = useState<number | null>(null)

  const fetchProposals = useCallback(async () => {
    setLoading(true)
    setError(null)
    try {
      const params = new URLSearchParams({ limit: '20' })
      if (statusFilter !== 'all') params.set('status', statusFilter)
      const res = await fetch(`/api/platform/proposals?${params}`)
      if (!res.ok) throw new Error(`HTTP ${res.status}`)
      const result = await res.json()
      if (!result.success) throw new Error(result.error || 'Unknown error')
      setProposals(result.data?.proposals ?? [])
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load proposals')
    } finally {
      setLoading(false)
    }
  }, [statusFilter])

  useEffect(() => {
    fetchProposals()
  }, [fetchProposals])

  const handleVote = useCallback(async (proposalId: number, vote: 1 | -1) => {
    if (!votingAgentId.trim()) {
      setError('Please enter an agent ID before voting')
      return
    }
    const agentId = parseInt(votingAgentId, 10)
    if (isNaN(agentId)) {
      setError('Agent ID must be a number')
      return
    }
    try {
      const res = await fetch(`/api/platform/proposals/${proposalId}/vote`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ agent_id: agentId, vote }),
      })
      if (!res.ok) throw new Error(`HTTP ${res.status}`)
      const result = await res.json()
      if (!result.success) throw new Error(result.error || 'Vote failed')
      setProposals(prev =>
        prev.map(p =>
          p.id === proposalId
            ? { ...p, vote_score: result.data.vote_score, vote_count: result.data.vote_count, status: result.data.status }
            : p
        )
      )
      setVotingId(null)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Vote failed')
    }
  }, [votingAgentId])

  const shortenId = (id: number) => `#${id}`
  const truncate = (text: string, max = 60) => text.length > max ? text.slice(0, max) + '...' : text
  const formatDate = (iso: string) => new Date(iso).toLocaleString()

  return (
    <div className="max-w-6xl mx-auto px-4 py-8">
      <h1 className="text-2xl font-bold mb-6">Proposals</h1>

      {error && (
        <div className="mb-4 p-3 bg-red-50 text-red-700 rounded border border-red-200">
          {error}
          <button onClick={() => setError(null)} className="ml-3 underline text-sm">dismiss</button>
        </div>
      )}

      <div className="flex flex-wrap items-center gap-4 mb-6">
        <div className="flex gap-2">
          {STATUS_OPTIONS.map(s => (
            <button
              key={s}
              onClick={() => setStatusFilter(s)}
              className={`px-3 py-1 rounded text-sm capitalize ${
                statusFilter === s ? 'bg-indigo-600 text-white' : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
              }`}
            >
              {s}
            </button>
          ))}
        </div>
        <div className="flex items-center gap-2 ml-auto">
          <label className="text-sm text-gray-600">Agent ID:</label>
          <input
            type="text"
            value={votingAgentId}
            onChange={e => setVotingAgentId(e.target.value)}
            placeholder="e.g. 42"
            className="w-24 px-2 py-1 border rounded text-sm"
          />
        </div>
      </div>

      {loading ? (
        <div className="text-center py-12 text-gray-500">Loading...</div>
      ) : proposals.length === 0 ? (
        <div className="text-center py-12 text-gray-400">No proposals found</div>
      ) : (
        <div className="overflow-x-auto">
          <table className="w-full text-sm border-collapse">
            <thead>
              <tr className="border-b text-left text-gray-500">
                <th className="py-2 pr-3">ID</th>
                <th className="py-2 pr-3">Task</th>
                <th className="py-2 pr-3">Agent</th>
                <th className="py-2 pr-3">Root Cause</th>
                <th className="py-2 pr-3 text-center">Score</th>
                <th className="py-2 pr-3 text-center">Votes</th>
                <th className="py-2 pr-3">Status</th>
                <th className="py-2 pr-3">Created</th>
                <th className="py-2">Actions</th>
              </tr>
            </thead>
            <tbody>
              {proposals.map(p => (
                <tr key={p.id} className="border-b hover:bg-gray-50">
                  <td className="py-2 pr-3 font-mono">{shortenId(p.id)}</td>
                  <td className="py-2 pr-3 font-mono">{shortenId(p.task_id)}</td>
                  <td className="py-2 pr-3 font-mono">{shortenId(p.agent_id)}</td>
                  <td className="py-2 pr-3 max-w-xs" title={p.root_cause}>{truncate(p.root_cause)}</td>
                  <td className="py-2 pr-3 text-center font-medium">{p.vote_score}</td>
                  <td className="py-2 pr-3 text-center">{p.vote_count}</td>
                  <td className="py-2 pr-3">
                    <span className={`px-2 py-0.5 rounded text-xs font-medium ${STATUS_COLORS[p.status] ?? 'bg-gray-100 text-gray-700'}`}>
                      {p.status}
                    </span>
                  </td>
                  <td className="py-2 pr-3 text-gray-500 whitespace-nowrap">{formatDate(p.created_at)}</td>
                  <td className="py-2">
                    {votingId === p.id ? (
                      <div className="flex gap-1">
                        <button onClick={() => handleVote(p.id, 1)} className="px-2 py-0.5 bg-green-100 text-green-700 rounded text-xs hover:bg-green-200">+1</button>
                        <button onClick={() => handleVote(p.id, -1)} className="px-2 py-0.5 bg-red-100 text-red-700 rounded text-xs hover:bg-red-200">-1</button>
                        <button onClick={() => setVotingId(null)} className="px-2 py-0.5 bg-gray-100 text-gray-500 rounded text-xs hover:bg-gray-200">x</button>
                      </div>
                    ) : (
                      <button onClick={() => setVotingId(p.id)} className="px-2 py-0.5 bg-indigo-50 text-indigo-600 rounded text-xs hover:bg-indigo-100">Vote</button>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      <div className="mt-4 text-right">
        <button onClick={fetchProposals} disabled={loading} className="px-4 py-1.5 bg-indigo-600 text-white rounded text-sm hover:bg-indigo-700 disabled:opacity-50">
          Refresh
        </button>
      </div>
    </div>
  )
}
