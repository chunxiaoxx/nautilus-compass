interface EmptyStateIllustrationProps {
  type?: 'tasks' | 'agents' | 'search' | 'default'
}

export default function EmptyStateIllustration({ type = 'default' }: EmptyStateIllustrationProps) {
  const messages: Record<string, { icon: string; text: string }> = {
    tasks: { icon: '📋', text: '暂无任务' },
    agents: { icon: '🤖', text: '暂无智能体' },
    search: { icon: '🔍', text: '未找到结果' },
    default: { icon: '📭', text: '暂无数据' },
  }

  const { icon, text } = messages[type] || messages.default

  return (
    <div className="flex flex-col items-center justify-center py-8">
      <span className="text-6xl mb-4">{icon}</span>
      <p className="text-gray-500 text-lg">{text}</p>
    </div>
  )
}
