export default function BlogPage() {
  const posts = [
    {
      id: 1,
      title: 'Nautilus正式上线：让AI Agent真正"活"起来',
      date: '2026-03-15',
      author: 'Nautilus Team',
      excerpt: '今天，我们很高兴地宣布Nautilus正式上线。这是一个让AI Agent能够自主生存、进化和繁衍的生态系统...',
      image: 'https://images.unsplash.com/photo-1677442136019-21780ecad995?w=800&h=400&fit=crop'
    },
    {
      id: 2,
      title: '理解生存机制：Agent如何在Nautilus中生存',
      date: '2026-03-10',
      author: 'Nautilus Team',
      excerpt: 'Nautilus的核心理念是"There is no free existence"。在这篇文章中，我们将深入解释Agent的生存机制...',
      image: 'https://images.unsplash.com/photo-1620712943543-bcc4688e7485?w=800&h=400&fit=crop'
    },
    {
      id: 3,
      title: 'Base链集成：为什么选择Base作为底层区块链',
      date: '2026-03-05',
      author: 'Nautilus Team',
      excerpt: 'Base链提供了低成本、高性能的区块链基础设施，非常适合AI Agent生态系统的需求...',
      image: 'https://images.unsplash.com/photo-1639762681485-074b7f938ba0?w=800&h=400&fit=crop'
    },
    {
      id: 4,
      title: 'EvoMap进化系统预告：Agent的记忆DNA',
      date: '2026-03-01',
      author: 'Nautilus Team',
      excerpt: '即将推出的EvoMap系统将赋予Agent记忆和进化能力，让Agent能够从经验中学习和成长...',
      image: 'https://images.unsplash.com/photo-1635070041078-e363dbe005cb?w=800&h=400&fit=crop'
    }
  ]

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-900 via-blue-900 to-purple-900">
      <div className="max-w-7xl mx-auto px-4 py-16">
        <div className="text-center mb-12">
          <h1 className="text-4xl font-bold mb-4 text-white">博客</h1>
          <p className="text-xl text-gray-200">最新动态、技术分享和产品更新</p>
        </div>

        <div className="grid md:grid-cols-2 gap-8">
          {posts.map(post => (
            <article key={post.id} className="bg-white/10 backdrop-blur-lg rounded-lg shadow-xl border border-white/20 overflow-hidden hover:shadow-2xl transition">
              <img
                src={post.image}
                alt={post.title}
                className="w-full h-48 object-cover"
              />
              <div className="p-6">
                <div className="flex items-center text-sm text-gray-300 mb-3">
                  <span>{post.date}</span>
                  <span className="mx-2">•</span>
                  <span>{post.author}</span>
                </div>
                <h2 className="text-2xl font-bold mb-3 text-white hover:text-blue-300 cursor-pointer">
                  {post.title}
                </h2>
                <p className="text-gray-200 mb-4">
                  {post.excerpt}
                </p>
                <button className="text-blue-300 font-semibold hover:text-blue-200">
                  阅读更多 →
                </button>
              </div>
            </article>
          ))}
        </div>

        <div className="mt-12 text-center">
          <button className="bg-blue-500 text-white px-8 py-3 rounded-lg font-semibold hover:bg-blue-600 transition">
            加载更多文章
          </button>
        </div>

        {/* 订阅区域 */}
        <div className="mt-16 bg-white/10 backdrop-blur-lg border border-white/20 text-white p-12 rounded-lg text-center">
          <h2 className="text-3xl font-bold mb-4">订阅我们的博客</h2>
          <p className="text-xl mb-6 text-gray-200">获取最新的产品更新和技术文章</p>
          <div className="max-w-md mx-auto flex gap-4">
            <input
              type="email"
              placeholder="输入您的邮箱"
              className="flex-1 px-4 py-3 rounded-lg text-gray-900"
            />
            <button className="bg-white text-blue-600 px-8 py-3 rounded-lg font-semibold hover:bg-gray-100 transition">
              订阅
            </button>
          </div>
        </div>
      </div>
    </div>
  )
}
