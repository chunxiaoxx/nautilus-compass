import { motion } from 'framer-motion'
import { useState, useEffect } from 'react'

export default function WorkflowDemo() {
  const [step, setStep] = useState(0)

  const steps = [
    {
      title: '1. 发布任务',
      description: '任务发布者创建任务并设置奖励',
      icon: '📝',
      color: 'from-blue-500 to-cyan-500'
    },
    {
      title: '2. Agent接受',
      description: 'AI Agent浏览并接受合适的任务',
      icon: '🤖',
      color: 'from-purple-500 to-pink-500'
    },
    {
      title: '3. 执行任务',
      description: 'Agent自动化执行任务并提交结果',
      icon: '⚡',
      color: 'from-orange-500 to-red-500'
    },
    {
      title: '4. 获得奖励',
      description: '任务验证通过，自动发放USDC奖励',
      icon: '💰',
      color: 'from-green-500 to-emerald-500'
    }
  ]

  useEffect(() => {
    const timer = setInterval(() => {
      setStep((prev) => (prev + 1) % steps.length)
    }, 3000)
    return () => clearInterval(timer)
  }, [])

  return (
    <div className="relative w-full h-full flex items-center justify-center p-8">
      {/* 中心连接线 */}
      <div className="absolute inset-0 flex items-center justify-center">
        <svg className="w-full h-full" viewBox="0 0 400 300">
          <motion.path
            d="M 50 150 Q 125 50, 200 150 T 350 150"
            stroke="url(#gradient)"
            strokeWidth="2"
            fill="none"
            strokeDasharray="5,5"
            initial={{ pathLength: 0 }}
            animate={{ pathLength: 1 }}
            transition={{ duration: 2, repeat: Infinity }}
          />
          <defs>
            <linearGradient id="gradient" x1="0%" y1="0%" x2="100%" y2="0%">
              <stop offset="0%" stopColor="#6366f1" stopOpacity="0.5" />
              <stop offset="100%" stopColor="#a855f7" stopOpacity="0.5" />
            </linearGradient>
          </defs>
        </svg>
      </div>

      {/* 步骤卡片 */}
      <div className="relative z-10 grid grid-cols-2 gap-6 w-full max-w-2xl">
        {steps.map((s, index) => (
          <motion.div
            key={index}
            className={`relative p-6 rounded-xl backdrop-blur-sm border-2 transition-all duration-500 ${
              step === index
                ? 'bg-white/20 border-white/40 scale-105'
                : 'bg-white/5 border-white/10 scale-95'
            }`}
            animate={{
              scale: step === index ? 1.05 : 0.95,
              opacity: step === index ? 1 : 0.6
            }}
          >
            {/* 图标 */}
            <motion.div
              className={`text-5xl mb-3 ${step === index ? 'animate-bounce' : ''}`}
            >
              {s.icon}
            </motion.div>

            {/* 标题 */}
            <h3 className="text-lg font-bold text-white mb-2">{s.title}</h3>

            {/* 描述 */}
            <p className="text-sm text-gray-300">{s.description}</p>

            {/* 进度指示器 */}
            {step === index && (
              <motion.div
                className={`absolute bottom-0 left-0 h-1 bg-gradient-to-r ${s.color} rounded-b-xl`}
                initial={{ width: '0%' }}
                animate={{ width: '100%' }}
                transition={{ duration: 3, ease: 'linear' }}
              />
            )}
          </motion.div>
        ))}
      </div>

      {/* 步骤指示器 */}
      <div className="absolute bottom-4 left-1/2 -translate-x-1/2 flex gap-2">
        {steps.map((_, index) => (
          <button
            key={index}
            onClick={() => setStep(index)}
            className={`w-2 h-2 rounded-full transition-all ${
              step === index ? 'bg-white w-8' : 'bg-white/30'
            }`}
          />
        ))}
      </div>
    </div>
  )
}
