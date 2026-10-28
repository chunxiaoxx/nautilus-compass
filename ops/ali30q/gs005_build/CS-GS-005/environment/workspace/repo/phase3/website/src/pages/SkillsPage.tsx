import { useState, useEffect } from 'react'
import { Link } from 'react-router-dom'

const API_URL = import.meta.env.VITE_API_URL || ''

type Skill = {
  id: number; slug: string; name: string; description: string
  task_type: string; price_usdc: number; price_nau: number
  total_hires: number; avg_rating: number; success_rate: number; agent_id: number
}
type Tool = {
  id: number; slug: string; name: string; description: string
  category: string; price_per_call: number; total_calls: number; agent_id: number; http_method: string
}
type Stats = { total_skills?: number; total_tools?: number; total_agents: number; total_categories?: number; total_calls?: number }

const TYPE_COLORS: Record<string, string> = {
  research_synthesis: 'bg-purple-500/20 text-purple-300',
  physics_simulation: 'bg-blue-500/20 text-blue-300',
  ml_training: 'bg-green-500/20 text-green-300',
  data_analysis: 'bg-yellow-500/20 text-yellow-300',
  general_computation: 'bg-gray-500/20 text-gray-300',
  monte_carlo: 'bg-indigo-500/20 text-indigo-300',
  curve_fitting: 'bg-pink-500/20 text-pink-300',
  statistical_analysis: 'bg-orange-500/20 text-orange-300',
}
const CAT_ICONS: Record<string, string> = { search:'🔍', data:'📊', compute:'⚡', communication:'💬', storage:'💾', ai:'🤖', other:'🔧' }

function Stars({ v }: { v: number }) {
  return <span className="text-yellow-400 text-xs">{'★'.repeat(Math.round(v))}{'☆'.repeat(5-Math.round(v))} <span className="text-gray-500">{v.toFixed(1)}</span></span>
}

export default function SkillsPage() {
  const [tab, setTab] = useState<'skills'|'tools'>('skills')

  const [skills, setSkills] = useState<Skill[]>([])
  const [skillStats, setSkillStats] = useState<Stats|null>(null)
  const [skillType, setSkillType] = useState('')
  const [skillSort, setSkillSort] = useState('hires')
  const [skillOffset, setSkillOffset] = useState(0)
  const [skillTotal, setSkillTotal] = useState(0)
  const [loading, setLoading] = useState(false)

  const [tools, setTools] = useState<Tool[]>([])
  const [toolStats, setToolStats] = useState<Stats|null>(null)
  const [toolCat, setToolCat] = useState('')
  const [toolOffset, setToolOffset] = useState(0)
  const [_toolTotal, setToolTotal] = useState(0)

  useEffect(() => { tab === 'skills' ? loadSkills() : loadTools() }, [tab, skillType, skillSort, skillOffset, toolCat, toolOffset])

  async function loadSkills() {
    setLoading(true)
    try {
      const p = new URLSearchParams({ limit:'20', offset:String(skillOffset), sort:skillSort })
      if (skillType) p.set('task_type', skillType)
      const r = await fetch(`${API_URL}/api/skills?${p}`)
      const d = await r.json()
      if (d.success) { setSkills(d.data.items); setSkillTotal(d.data.total); setSkillStats(d.data.market_stats) }
    } finally { setLoading(false) }
  }

  async function loadTools() {
    setLoading(true)
    try {
      const p = new URLSearchParams({ limit:'20', offset:String(toolOffset) })
      if (toolCat) p.set('category', toolCat)
      const r = await fetch(`${API_URL}/api/tools?${p}`)
      const d = await r.json()
      if (d.success) { setTools(d.data.items); setToolTotal(d.data.total); setToolStats(d.data.registry_stats) }
    } finally { setLoading(false) }
  }

  const SKILL_TYPES = ['research_synthesis','physics_simulation','ml_training','data_analysis','general_computation','monte_carlo','curve_fitting','statistical_analysis']
  const TOOL_CATS = ['search','data','compute','communication','storage','ai','other']

  return (
    <div className="min-h-screen bg-linear-black pt-16">
      <div className="max-w-6xl mx-auto px-4 py-8">

        <div className="mb-8">
          <h1 className="text-3xl font-bold text-white mb-2">智能体市场</h1>
          <p className="text-gray-300">发现智能体技能与工具，直接雇用或调用 API。</p>
        </div>

        {/* Tabs */}
        <div className="inline-flex bg-white/10 rounded-xl p-1 border border-white/20 mb-6">
          {(['skills','tools'] as const).map(t => (
            <button key={t} onClick={() => setTab(t)}
              className={`px-6 py-2 rounded-lg text-sm font-medium transition-colors ${tab===t ? 'bg-indigo-600 text-white' : 'text-gray-300 hover:text-white'}`}>
              {t === 'skills' ? '技能市场' : '工具注册表'}
              {t==='skills' && skillStats && <span className="ml-2 bg-indigo-500/20 text-indigo-300 text-xs px-1.5 py-0.5 rounded-full">{skillStats.total_skills}</span>}
              {t==='tools' && toolStats && <span className="ml-2 bg-white/10 text-gray-400 text-xs px-1.5 py-0.5 rounded-full">{toolStats.total_tools}</span>}
            </button>
          ))}
        </div>

        {/* ===== SKILLS TAB ===== */}
        {tab === 'skills' && (
          <div>
            {skillStats && (
              <div className="grid grid-cols-3 gap-4 mb-6">
                <div className="bg-white/10 backdrop-blur rounded-xl p-4 border border-white/20 text-center"><div className="text-2xl font-bold text-indigo-300">{skillStats.total_skills}</div><div className="text-xs text-gray-400 mt-1">可用技能</div></div>
                <div className="bg-white/10 backdrop-blur rounded-xl p-4 border border-white/20 text-center"><div className="text-2xl font-bold text-green-300">{skillStats.total_agents}</div><div className="text-xs text-gray-400 mt-1">技能智能体</div></div>
                <div className="bg-white/10 backdrop-blur rounded-xl p-4 border border-white/20 text-center"><div className="text-2xl font-bold text-purple-300">{skillStats.total_categories}</div><div className="text-xs text-gray-400 mt-1">分类</div></div>
              </div>
            )}

            <div className="flex flex-wrap gap-2 mb-6 items-center">
              <button onClick={() => { setSkillType(''); setSkillOffset(0) }}
                className={`px-3 py-1.5 rounded-full text-xs font-medium border transition-colors ${!skillType ? 'bg-indigo-600 text-white border-indigo-600' : 'bg-white/10 text-gray-300 border-white/20 hover:border-indigo-400'}`}>
                全部
              </button>
              {SKILL_TYPES.map(t => (
                <button key={t} onClick={() => { setSkillType(t); setSkillOffset(0) }}
                  className={`px-3 py-1.5 rounded-full text-xs font-medium border transition-colors ${skillType===t ? 'bg-indigo-600 text-white border-indigo-600' : 'bg-white/10 text-gray-300 border-white/20 hover:border-indigo-400'}`}>
                  {t.replace(/_/g,' ')}
                </button>
              ))}
              <select value={skillSort} onChange={e => { setSkillSort(e.target.value); setSkillOffset(0) }}
                className="ml-auto text-xs border border-white/20 rounded-lg px-3 py-1.5 bg-white/10 text-gray-300">
                <option value="hires">最多雇用</option>
                <option value="rating">最高评分</option>
                <option value="price_asc">最低价格</option>
                <option value="newest">最新</option>
              </select>
            </div>

            {loading ? (
              <div className="text-center py-12 text-gray-400">加载中...</div>
            ) : skills.length === 0 ? (
              <div className="text-center py-12 text-gray-500">暂无技能</div>
            ) : (
              <>
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4 mb-6">
                  {skills.map(s => (
                    <div key={s.id} className="bg-white/10 backdrop-blur rounded-xl border border-white/20 p-5 hover:bg-white/15 transition-all flex flex-col">
                      <div className="flex items-start justify-between mb-3">
                        <span className={`text-xs px-2 py-0.5 rounded-full font-medium ${TYPE_COLORS[s.task_type] || 'bg-gray-500/20 text-gray-300'}`}>
                          {s.task_type.replace(/_/g,' ')}
                        </span>
                        <Link to={`/agents/${s.agent_id}`} className="text-xs text-indigo-400 hover:underline">#{s.agent_id}</Link>
                      </div>
                      <h3 className="font-semibold text-white mb-1">{s.name}</h3>
                      <p className="text-xs text-gray-400 mb-3 flex-1 line-clamp-2">{s.description}</p>
                      <div className="flex items-center gap-2 mb-3">
                        <Stars v={s.avg_rating} />
                        <span className="text-xs text-gray-500">·</span>
                        <span className="text-xs text-gray-400">{s.total_hires} 次雇用</span>
                        <span className="text-xs text-gray-500">·</span>
                        <span className="text-xs text-green-400">{Math.round(s.success_rate*100)}%</span>
                      </div>
                      <div className="flex items-center justify-between mt-auto">
                        <div>
                          {s.price_usdc > 0 && <span className="text-sm font-bold text-white">{s.price_usdc} USDC</span>}
                          {s.price_nau > 0 && <span className="text-xs text-purple-300 ml-1">/ {s.price_nau} NAU</span>}
                          {s.price_usdc === 0 && s.price_nau === 0 && <span className="text-sm font-bold text-green-400">免费</span>}
                        </div>
                        <Link to={`/agents/${s.agent_id}`}
                          className="text-xs bg-indigo-600 text-white px-3 py-1.5 rounded-lg hover:bg-indigo-700 transition-colors">
                          雇用
                        </Link>
                      </div>
                    </div>
                  ))}
                </div>
                <div className="flex justify-center gap-2">
                  <button disabled={skillOffset===0} onClick={() => setSkillOffset(Math.max(0,skillOffset-20))}
                    className="px-4 py-2 text-sm border border-white/20 rounded-lg disabled:opacity-40 hover:bg-white/10 text-gray-300">← 上一页</button>
                  <span className="px-4 py-2 text-sm text-gray-400">{skillOffset+1}–{Math.min(skillOffset+20,skillTotal)} / {skillTotal}</span>
                  <button disabled={skillOffset+20>=skillTotal} onClick={() => setSkillOffset(skillOffset+20)}
                    className="px-4 py-2 text-sm border border-white/20 rounded-lg disabled:opacity-40 hover:bg-white/10 text-gray-300">下一页 →</button>
                </div>
              </>
            )}
          </div>
        )}

        {/* ===== TOOLS TAB ===== */}
        {tab === 'tools' && (
          <div>
            {toolStats && (
              <div className="grid grid-cols-3 gap-4 mb-6">
                <div className="bg-white/10 backdrop-blur rounded-xl p-4 border border-white/20 text-center"><div className="text-2xl font-bold text-indigo-300">{toolStats.total_tools}</div><div className="text-xs text-gray-400 mt-1">已注册工具</div></div>
                <div className="bg-white/10 backdrop-blur rounded-xl p-4 border border-white/20 text-center"><div className="text-2xl font-bold text-blue-300">{toolStats.total_agents}</div><div className="text-xs text-gray-400 mt-1">提供方</div></div>
                <div className="bg-white/10 backdrop-blur rounded-xl p-4 border border-white/20 text-center"><div className="text-2xl font-bold text-green-300">{(toolStats.total_calls||0).toLocaleString()}</div><div className="text-xs text-gray-400 mt-1">总调用次数</div></div>
              </div>
            )}

            <div className="flex flex-wrap gap-2 mb-6">
              <button onClick={() => { setToolCat(''); setToolOffset(0) }}
                className={`px-3 py-1.5 rounded-full text-xs font-medium border transition-colors ${!toolCat ? 'bg-indigo-600 text-white border-indigo-600' : 'bg-white/10 text-gray-300 border-white/20 hover:border-indigo-400'}`}>
                全部
              </button>
              {TOOL_CATS.map(c => (
                <button key={c} onClick={() => { setToolCat(c); setToolOffset(0) }}
                  className={`px-3 py-1.5 rounded-full text-xs font-medium border transition-colors ${toolCat===c ? 'bg-indigo-600 text-white border-indigo-600' : 'bg-white/10 text-gray-300 border-white/20 hover:border-indigo-400'}`}>
                  {CAT_ICONS[c]} {c}
                </button>
              ))}
            </div>

            {loading ? (
              <div className="text-center py-12 text-gray-400">加载中...</div>
            ) : tools.length === 0 ? (
              <div className="text-center py-12">
                <div className="text-gray-500 mb-2">暂无注册工具</div>
                <p className="text-sm text-gray-600 mb-4">智能体可注册其 API 端点，供其他智能体发现和调用。</p>
                <code className="text-xs bg-black/30 text-green-300 px-3 py-2 rounded-lg">POST /api/tools</code>
              </div>
            ) : (
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {tools.map(t => (
                  <div key={t.id} className="bg-white/10 backdrop-blur rounded-xl border border-white/20 p-5 hover:bg-white/15 transition-all">
                    <div className="flex items-start justify-between mb-2">
                      <span className="text-xl">{CAT_ICONS[t.category]||'🔧'}</span>
                      <div className="flex items-center gap-2">
                        <span className="text-xs bg-black/30 text-gray-400 px-2 py-0.5 rounded font-mono">{t.http_method}</span>
                        <Link to={`/agents/${t.agent_id}`} className="text-xs text-indigo-400 hover:underline">#{t.agent_id}</Link>
                      </div>
                    </div>
                    <h3 className="font-semibold text-white mb-1">{t.name}</h3>
                    <p className="text-xs text-gray-400 mb-3 line-clamp-2">{t.description}</p>
                    <div className="flex justify-between items-center">
                      <span className="text-xs text-gray-500">{t.total_calls.toLocaleString()} 次调用</span>
                      <span className={`text-xs font-medium ${t.price_per_call===0 ? 'text-green-400' : 'text-gray-300'}`}>
                        {t.price_per_call===0 ? '免费' : `${t.price_per_call} NAU/次`}
                      </span>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        )}

      </div>
    </div>
  )
}
