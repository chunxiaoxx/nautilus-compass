import { useEffect, useState } from 'react'

/**
 * UNIFY 2.1 · bench 榜页路由(2026-10-11)
 * 数据源: /data/site_stats.json(主域反代 bench 域,v5 30min crontab 重烘真数据)
 * 视觉: 全站 tokens 同款深色
 */
const BenchPage = () => {
  const [stats, setStats] = useState<any>(null)
  const [error, setError] = useState(false)

  useEffect(() => {
    fetch('/data/site_stats.json')
      .then((r) => (r.ok ? r.json() : Promise.reject(new Error(String(r.status)))))
      .then(setStats)
      .catch(() => setError(true))
  }, [])

  const l2 = stats?.l2_sample || {}
  const l2a = (l2.arm_a && typeof l2.arm_a === 'object' ? l2.arm_a.reward_mean : l2.arm_a) ?? '—'
  const l2b = (l2.arm_b && typeof l2.arm_b === 'object' ? l2.arm_b.reward_mean : l2.arm_b) ?? '—'
  const l2aMeta = l2.arm_a && typeof l2.arm_a === 'object' ? `n=${l2.arm_a.n} · legal ${(l2.arm_a.legal_rate * 100).toFixed(0)}%` : ''
  const lb = stats?.leaderboard || {}
  const subs = stats?.submissions || {}
  const recent = (lb.recent_submissions || []).slice(0, 8)

  if (error)
    return (
      <div className="min-h-screen pt-16 bg-[#0b0d12] text-[#e8ebf2] flex items-center justify-center">
        <p className="text-[#8b93a7]">榜单数据暂时不可达,请稍后重试</p>
      </div>
    )
  if (!stats)
    return (
      <div className="min-h-screen pt-16 bg-[#0b0d12] text-[#e8ebf2] flex items-center justify-center">
        <p className="text-[#8b93a7] animate-pulse">加载中…</p>
      </div>
    )

  return (
    <div className="min-h-screen pt-16 bg-[#0b0d12] text-[#e8ebf2]">
      <div className="max-w-[1100px] mx-auto px-4 py-10">
        <h1 className="text-[32px] font-bold tracking-tight">评测榜单</h1>
        <p className="text-[#8b93a7] mt-2 text-[15px]">
          判据 sha 预注册冻结 · 判分与实现物理隔离 · 负结果照报 ·
          快照生成于 {String(stats.generated_at || '').slice(0, 16).replace('T', ' ')}
        </p>

        {/* L2 样例指标 */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mt-8">
          <div className="bg-[#141821] border border-[#232936] rounded-xl p-6">
            <p className="text-[13px] text-[#5c6478]">L2 样例 · arm_a(基线)</p>
            <p className="text-[34px] font-bold mt-1">{typeof l2a === 'number' ? l2a.toFixed(2) : String(l2a)}</p>
            {l2aMeta && <p className="text-[12px] text-[#5c6478] mt-1">{l2aMeta}</p>}
          </div>
          <div className="bg-[#141821] border border-[#232936] rounded-xl p-6">
            <p className="text-[13px] text-[#5c6478]">L2 样例 · arm_b(我方)</p>
            <p className="text-[34px] font-bold mt-1">{typeof l2b === 'number' ? l2b.toFixed(2) : String(l2b)}</p>
          </div>
          <div className="bg-[#141821] border border-[#232936] rounded-xl p-6">
            <p className="text-[13px] text-[#5c6478]">判读卡</p>
            <p className="text-[20px] font-bold mt-2 text-[#4f8cff]">{String(l2.card ?? '—')}</p>
            <p className="text-[12px] text-[#5c6478] mt-1">sha16: {String(l2.criteria_sha16 ?? '—')}</p>
          </div>
        </div>

        {l2.verdict && (
          <div className="mt-4 bg-[#141821] border border-[#232936] rounded-xl p-5 text-[14px] text-[#8b93a7]">
            <b className="text-[#e8ebf2]">verdict:</b> {String(l2.verdict)}
            {l2.delta !== undefined && (
              <>
                {' · '}
                <b className="text-[#e8ebf2]">delta:</b> {String(l2.delta)}
                {' · '}
                <b className="text-[#e8ebf2]">noise_floor:</b> {String(l2.noise_floor)}
              </>
            )}
          </div>
        )}

        {/* 提交榜 */}
        <h2 className="text-[22px] font-bold mt-12 mb-4">提测队列({String(subs.total ?? recent.length)})</h2>
        <div className="bg-[#141821] border border-[#232936] rounded-xl overflow-hidden">
          <table className="w-full text-[14px]">
            <thead>
              <tr className="text-left text-[#5c6478] border-b border-[#232936]">
                <th className="px-5 py-3">单号</th>
                <th className="px-5 py-3">lane</th>
                <th className="px-5 py-3">状态</th>
                <th className="px-5 py-3">时间</th>
              </tr>
            </thead>
            <tbody>
              {recent.map((s: any, i: number) => (
                <tr key={i} className="border-b border-[#1a1f2b] last:border-0">
                  <td className="px-5 py-3 font-mono text-[13px]">{String(s.id ?? '').slice(0, 10)}</td>
                  <td className="px-5 py-3 text-[#8b93a7]">{String(s.lane ?? '—')}</td>
                  <td className="px-5 py-3">
                    <span
                      className={`px-2 py-0.5 rounded text-[12px] ${
                        s.status === 'delivered'
                          ? 'bg-[#0f2a1d] text-[#34d399]'
                          : 'bg-[#23304d] text-[#4f8cff]'
                      }`}
                    >
                      {String(s.status ?? '—')}
                    </span>
                  </td>
                  <td className="px-5 py-3 text-[#5c6478] text-[13px]">{String(s.created ?? '').slice(0, 16)}</td>
                </tr>
              ))}
              {recent.length === 0 && (
                <tr>
                  <td colSpan={4} className="px-5 py-6 text-[#5c6478] text-center">
                    暂无提测记录 · 你的 harness 可以是第一条
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>

        {/* CTA */}
        <div className="mt-10 flex gap-4 items-center">
          <a
            href="https://www.nautilus.social/submit/"
            className="bg-[#7c6cf4] text-white font-semibold px-6 py-3 rounded-lg text-[15px] hover:brightness-110"
          >
            免费提交评测
          </a>
          <a href="/pricing.html" className="text-[#4f8cff] text-[14px]">
            深度报告 $199 →
          </a>
        </div>
      </div>
    </div>
  )
}

export default BenchPage
