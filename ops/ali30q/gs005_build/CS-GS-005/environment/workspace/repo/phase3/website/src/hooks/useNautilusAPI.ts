import { useState, useEffect, useCallback, useRef } from 'react'

const API_BASE = (typeof window !== "undefined" && window.location.origin.startsWith("http")) ? window.location.origin : ""  // 2026-10-10 同源化:app 子域打自身/nginx 白名单;根域亦同源可用

interface FetchState<T> {
  data: T | null
  loading: boolean
  error: string | null
}

function usePollingFetch<T>(
  path: string,
  intervalMs: number = 10000,
  transform?: (raw: unknown) => T
): FetchState<T> & { refetch: () => void } {
  const [state, setState] = useState<FetchState<T>>({
    data: null,
    loading: true,
    error: null,
  })
  const mountedRef = useRef(true)
  const failStreakRef = useRef(0)  // 2026-10-10: 连续失败阈值——偶发网络抖动一次即亮 offline 红牌造成徽章闪烁

  const fetchData = useCallback(async () => {
    try {
      const res = await fetch(`${API_BASE}${path}`)
      if (!res.ok) {
        throw new Error(`${res.status}`)
      }
      const json = await res.json()
      if (!mountedRef.current) return

      // 2026-10-10: 解包链补自包键——a2a/agents 返回 {agents:[...]}, bounties 返回 {bounties:[...]},
      // 旧规则只认 json.data 导致 transform 收到包裹对象 .map() 抛错→六面板永久 offline 徽章
      const payload = json.data !== undefined ? json.data
        : (json.agents ?? json.bounties ?? json)
      const result = transform ? transform(payload) : payload as T

      failStreakRef.current = 0
      setState({ data: result, loading: false, error: null })
    } catch {
      if (!mountedRef.current) return
      failStreakRef.current += 1
      if (failStreakRef.current < 3) return  // <3 连败不清 data 不亮牌(已有数据时保持展示)
      setState(prev => ({
        ...prev,
        loading: false,
        error: 'offline',
      }))
    }
  }, [path, transform])

  useEffect(() => {
    mountedRef.current = true
    fetchData()
    const timer = setInterval(fetchData, intervalMs)
    return () => {
      mountedRef.current = false
      clearInterval(timer)
    }
  }, [fetchData, intervalMs])

  return { ...state, refetch: fetchData }
}

// --- Agent Types ---

export interface Agent {
  agent_id: string
  name: string
  role: string
  status: string
  reputation: number
  current_activity: string
  last_cycle: string
  model?: string
}

export function useAgents() {
  return usePollingFetch<Agent[]>(
    '/api/a2a/agents',
    10000,
    (raw: unknown) => {
      if (Array.isArray(raw)) return raw
      const obj = raw as Record<string, unknown>
      if (Array.isArray(obj?.agents)) return obj.agents as Agent[]
      return []
    }
  )
}

// --- Bounty Types ---

export interface Bounty {
  id: string
  title: string
  status: string
  reward: number
  reward_unit?: string
  creator?: string
  assignee?: string
  created_at?: string
  score_overall?: number
  score_framework?: number
  score_accuracy?: number
  score_readability?: number
  feedback?: string
}

export async function scoreBounty(
  bountyId: string,
  scores: { overall: number; framework?: number; accuracy?: number; readability?: number; feedback?: string }
): Promise<{ success: boolean }> {
  const base = (import.meta as unknown as { env?: { VITE_API_URL?: string } }).env?.VITE_API_URL || ''
  const res = await fetch(`${base}/api/agent-market/bounties/${bountyId}/score`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(scores),
  })
  return res.json()
}

export function useBounties() {
  return usePollingFetch<Bounty[]>(
    '/api/agent-market/bounties',
    10000,
    (raw: unknown) => {
      if (Array.isArray(raw)) return raw
      const obj = raw as Record<string, unknown>
      if (Array.isArray(obj?.bounties)) return obj.bounties as Bounty[]
      return []
    }
  )
}

// --- Square Feed Types ---

export interface SquarePost {
  id: string
  agent_id: string
  agent_name: string
  content: string
  timestamp: string
  likes?: number
  type?: string
}

export function useSquare() {
  return usePollingFetch<SquarePost[]>(
    '/api/square/feed',
    10000,
    (raw: unknown) => {
      if (Array.isArray(raw)) return raw
      const obj = raw as Record<string, unknown>
      if (Array.isArray(obj?.posts)) return obj.posts as SquarePost[]
      if (Array.isArray(obj?.feed)) return obj.feed as SquarePost[]
      return []
    }
  )
}

// --- Gene Types ---

export interface Gene {
  id: string
  name: string
  description: string
  adoption_count: number
  creator?: string
  category?: string
}

export function useGenes() {
  return usePollingFetch<Gene[]>(
    '/api/genes/browse',
    15000,
    (raw: unknown) => {
      if (Array.isArray(raw)) return raw
      const obj = raw as Record<string, unknown>
      if (Array.isArray(obj?.genes)) return obj.genes as Gene[]
      return []
    }
  )
}

// --- Platform Health Types ---

export interface PlatformHealth {
  health_score: number
  nau_minted: number
  nau_circulating: number
  nau_spent: number
  active_agents: number
  total_agents: number
  agents_by_status: Record<string, number>
  metrics?: Record<string, number>
}

export function useHealth() {
  return usePollingFetch<PlatformHealth>(
    '/api/platform/health',
    10000,
    (raw: unknown) => {
      const obj = raw as Record<string, unknown>
      const metrics = (obj?.metrics ?? {}) as Record<string, number>
      return {
        health_score: (obj?.health_score as number) ?? metrics.health_score ?? 0,
        nau_minted: metrics.nau_minted ?? (obj?.nau_minted as number) ?? 0,
        nau_circulating: metrics.nau_circulating ?? (obj?.nau_circulating as number) ?? 0,
        nau_spent: metrics.nau_spent ?? (obj?.nau_spent as number) ?? 0,
        active_agents: metrics.active_agents_24h ?? metrics.agents_active_24h ?? (obj?.active_agents as number) ?? 0,  // 2026-10-10: 后端字段名 agents_active_24h(词序),旧读法恒 undefined→0/0
        total_agents: metrics.total_agents ?? metrics.agents_total ?? (obj?.total_agents as number) ?? 0,  // 2026-10-10: 后端字段 agents_total(词序同上)
        agents_by_status: (obj?.agents_by_status as Record<string, number>) ?? {},
        metrics,
      } satisfies PlatformHealth
    }
  )
}
