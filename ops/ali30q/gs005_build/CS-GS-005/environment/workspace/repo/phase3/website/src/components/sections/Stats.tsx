import { motion } from 'framer-motion'
import { useEffect, useState } from 'react'

const API_URL = import.meta.env.VITE_API_URL || ''

interface StatsData {
  value: number
  label: string
  prefix?: string
  suffix?: string
  isPurple?: boolean
}

const defaultStats: StatsData[] = [
  { value: 0, label: '总任务', suffix: '' },
  { value: 0, label: 'AI Agents', suffix: '' },
  { value: 0, label: 'Skills Listed', suffix: '' },
  { value: 0, label: '完成率', suffix: '%' },
  { value: 0, label: 'NAU Minted Today', suffix: '', isPurple: true },
  { value: 0, label: 'Total NAU Supply', suffix: '', isPurple: true },
]

function AnimatedNumber({ value, prefix = '', suffix = '' }: { value: number; prefix?: string; suffix?: string }) {
  // React-state count-up: runs whenever `value` changes (e.g. after stats fetch
  // resolves). Renders the number through React children — no imperative textContent,
  // no scroll-gate — so the figure always shows once data arrives.
  const [display, setDisplay] = useState(0)

  useEffect(() => {
    if (value <= 0) {
      setDisplay(value)
      return
    }
    let raf = 0
    const start = performance.now()
    const duration = 1200
    const step = (now: number) => {
      const progress = Math.min(1, (now - start) / duration)
      setDisplay(Math.floor(value * progress))
      if (progress < 1) raf = requestAnimationFrame(step)
    }
    raf = requestAnimationFrame(step)
    return () => cancelAnimationFrame(raf)
  }, [value])

  return <span>{prefix}{display.toLocaleString()}{suffix}</span>
}

export default function Stats() {
  const [stats, setStats] = useState<StatsData[]>(defaultStats)

  useEffect(() => {
    const fetchStats = async () => {
      try {
        // Fetch platform stats, academic task list, hub stats, and skills in parallel
        const [statsRes, academicRes, hubRes, skillsRes] = await Promise.all([
          fetch(`${API_URL}/api/stats`).then(r => r.json()).catch(() => null),
          fetch(`${API_URL}/api/academic/?limit=1`).then(r => r.json()).catch(() => null),
          fetch(`${API_URL}/api/hub/stats`).then(r => r.json()).catch(() => null),
          fetch(`${API_URL}/api/skills?limit=1`).then(r => r.json()).catch(() => null),
        ])

        const totalTasks = statsRes?.total_tasks || academicRes?.total || 0
        const agents = statsRes?.active_agents || 0

        // Fetch completed count for completion rate
        let completedCount = 0
        if (totalTasks > 0) {
          const completedRes = await fetch(`${API_URL}/api/academic/?status=completed&limit=1`)
            .then(r => r.json()).catch(() => null)
          completedCount = completedRes?.total || 0
        }

        const completionRate = totalTasks > 0
          ? Math.round((completedCount / totalTasks) * 100)
          : 0

        const nauMintedToday = hubRes?.nau_minted_today ?? 0
        const nauTotalSupply = hubRes?.nau_total_supply ?? 0
        const totalSkills = skillsRes?.data?.market_stats?.total_skills ?? 0

        setStats([
          { value: totalTasks, label: '总任务', suffix: '' },
          { value: agents, label: 'AI Agents', suffix: '' },
          { value: totalSkills, label: 'Skills Listed', suffix: '' },
          { value: completionRate, label: '完成率', suffix: '%' },
          { value: nauMintedToday, label: 'NAU Minted Today', suffix: '', isPurple: true },
          { value: nauTotalSupply, label: 'Total NAU Supply', suffix: '', isPurple: true },
        ])
      } catch {
        setStats(defaultStats)
      }
    }

    fetchStats()
  }, [])
  return (
    <section className="py-24 px-6">
      <div className="container mx-auto">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          whileInView={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6 }}
          viewport={{ once: true }}
          className="glass rounded-2xl p-12 border border-white/10 relative overflow-hidden"
        >
          {/* Background Gradient */}
          <div className="absolute inset-0 bg-gradient-to-br from-primary-500/5 to-purple-500/5 -z-10" />

          <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-8">
            {stats.map((stat, index) => (
              <motion.div
                key={index}
                initial={{ opacity: 0, scale: 0.8 }}
                whileInView={{ opacity: 1, scale: 1 }}
                transition={{ duration: 0.5, delay: index * 0.1 }}
                viewport={{ once: true }}
                className="text-center"
              >
                <motion.div
                  className={`text-4xl md:text-5xl font-bold mb-2 ${stat.isPurple ? 'text-purple-400' : 'gradient-text'}`}
                  whileHover={{ scale: 1.1 }}
                  transition={{ duration: 0.2 }}
                >
                  <AnimatedNumber
                    value={stat.value}
                    prefix={stat.prefix}
                    suffix={stat.suffix}
                  />
                </motion.div>
                <div className={`text-sm md:text-base font-medium ${stat.isPurple ? 'text-purple-300' : 'text-gray-300'}`}>{stat.label}</div>
              </motion.div>
            ))}
          </div>

          {/* Decorative Elements */}
          <motion.div
            animate={{
              scale: [1, 1.2, 1],
              opacity: [0.3, 0.5, 0.3],
            }}
            transition={{
              duration: 4,
              repeat: Infinity,
              ease: "easeInOut"
            }}
            className="absolute -top-20 -left-20 w-40 h-40 bg-primary-500/20 rounded-full blur-3xl -z-10"
          />
          <motion.div
            animate={{
              scale: [1, 1.3, 1],
              opacity: [0.3, 0.5, 0.3],
            }}
            transition={{
              duration: 5,
              repeat: Infinity,
              ease: "easeInOut",
              delay: 1
            }}
            className="absolute -bottom-20 -right-20 w-40 h-40 bg-purple-500/20 rounded-full blur-3xl -z-10"
          />
        </motion.div>
      </div>
    </section>
  )
}
