import { useState } from 'react'

export default function ContactPage() {
  const [formData, setFormData] = useState({
    name: '',
    email: '',
    subject: '',
    message: ''
  })

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    // TODO: 实现表单提交逻辑
    alert('感谢您的留言！我们会尽快回复。')
  }

  const handleChange = (e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement | HTMLSelectElement>) => {
    setFormData({
      ...formData,
      [e.target.name]: e.target.value
    })
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-900 via-blue-900 to-purple-900">
      <div className="max-w-7xl mx-auto px-4 py-16">
        <div className="text-center mb-12">
          <h1 className="text-4xl font-bold mb-4 text-white">联系我们</h1>
          <p className="text-xl text-gray-200">有任何问题或建议？我们很乐意听到您的声音</p>
        </div>

        <div className="grid md:grid-cols-2 gap-12">
          {/* 联系表单 */}
          <div className="bg-white/10 backdrop-blur-lg border border-white/20 p-8 rounded-lg shadow-xl">
            <h2 className="text-2xl font-bold mb-6 text-white">发送消息</h2>
            <form onSubmit={handleSubmit} className="space-y-6">
              <div>
                <label className="block text-sm font-semibold mb-2 text-gray-200">姓名</label>
                <input
                  type="text"
                  name="name"
                  value={formData.name}
                  onChange={handleChange}
                  className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent text-gray-900"
                  required
                />
              </div>

              <div>
                <label className="block text-sm font-semibold mb-2 text-gray-200">邮箱</label>
                <input
                  type="email"
                  name="email"
                  value={formData.email}
                  onChange={handleChange}
                  className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent text-gray-900"
                  required
                />
              </div>

              <div>
                <label className="block text-sm font-semibold mb-2 text-gray-200">主题</label>
                <select
                  name="subject"
                  value={formData.subject}
                  onChange={handleChange}
                  className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent text-gray-900"
                  required
                >
                  <option value="">请选择</option>
                  <option value="general">一般咨询</option>
                  <option value="technical">技术支持</option>
                  <option value="partnership">合作洽谈</option>
                  <option value="feedback">产品反馈</option>
                  <option value="other">其他</option>
                </select>
              </div>

              <div>
                <label className="block text-sm font-semibold mb-2 text-gray-200">消息</label>
                <textarea
                  name="message"
                  value={formData.message}
                  onChange={handleChange}
                  rows={6}
                  className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent text-gray-900"
                  required
                />
              </div>

              <button
                type="submit"
                className="w-full bg-blue-500 text-white py-3 rounded-lg font-semibold hover:bg-blue-600 transition"
              >
                发送消息
              </button>
            </form>
          </div>

          {/* 联系信息 */}
          <div className="space-y-8">
            <div className="bg-white/10 backdrop-blur-lg border border-white/20 p-8 rounded-lg shadow-xl">
              <h2 className="text-2xl font-bold mb-6 text-white">联系方式</h2>

              <div className="space-y-6">
                <div className="flex items-start">
                  <div className="w-12 h-12 bg-blue-500/30 rounded-lg flex items-center justify-center flex-shrink-0 mr-4">
                    <svg className="w-6 h-6 text-blue-300" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 8l7.89 5.26a2 2 0 002.22 0L21 8M5 19h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z" />
                    </svg>
                  </div>
                  <div>
                    <h3 className="font-bold mb-1 text-white">邮箱</h3>
                    <p className="text-gray-200">contact@nautilus.social</p>
                  </div>
                </div>

                <div className="flex items-start">
                  <div className="w-12 h-12 bg-purple-500/30 rounded-lg flex items-center justify-center flex-shrink-0 mr-4">
                    <svg className="w-6 h-6 text-purple-300" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z" />
                    </svg>
                  </div>
                  <div>
                    <h3 className="font-bold mb-1 text-white">Discord</h3>
                    <p className="text-gray-200">discord.gg/nautilus</p>
                  </div>
                </div>

                <div className="flex items-start">
                  <div className="w-12 h-12 bg-pink-500/30 rounded-lg flex items-center justify-center flex-shrink-0 mr-4">
                    <svg className="w-6 h-6 text-pink-300" fill="currentColor" viewBox="0 0 24 24">
                      <path d="M8.29 20.251c7.547 0 11.675-6.253 11.675-11.675 0-.178 0-.355-.012-.53A8.348 8.348 0 0022 5.92a8.19 8.19 0 01-2.357.646 4.118 4.118 0 001.804-2.27 8.224 8.224 0 01-2.605.996 4.107 4.107 0 00-6.993 3.743 11.65 11.65 0 01-8.457-4.287 4.106 4.106 0 001.27 5.477A4.072 4.072 0 012.8 9.713v.052a4.105 4.105 0 003.292 4.022 4.095 4.095 0 01-1.853.07 4.108 4.108 0 003.834 2.85A8.233 8.233 0 012 18.407a11.616 11.616 0 006.29 1.84" />
                    </svg>
                  </div>
                  <div>
                    <h3 className="font-bold mb-1 text-white">Twitter</h3>
                    <p className="text-gray-200">@NautilusAI</p>
                  </div>
                </div>

                <div className="flex items-start">
                  <div className="w-12 h-12 bg-gray-500/30 rounded-lg flex items-center justify-center flex-shrink-0 mr-4">
                    <svg className="w-6 h-6 text-gray-300" fill="currentColor" viewBox="0 0 24 24">
                      <path fillRule="evenodd" d="M12 2C6.477 2 2 6.484 2 12.017c0 4.425 2.865 8.18 6.839 9.504.5.092.682-.217.682-.483 0-.237-.008-.868-.013-1.703-2.782.605-3.369-1.343-3.369-1.343-.454-1.158-1.11-1.466-1.11-1.466-.908-.62.069-.608.069-.608 1.003.07 1.531 1.032 1.531 1.032.892 1.53 2.341 1.088 2.91.832.092-.647.35-1.088.636-1.338-2.22-.253-4.555-1.113-4.555-4.951 0-1.093.39-1.988 1.029-2.688-.103-.253-.446-1.272.098-2.65 0 0 .84-.27 2.75 1.026A9.564 9.564 0 0112 6.844c.85.004 1.705.115 2.504.337 1.909-1.296 2.747-1.027 2.747-1.027.546 1.379.202 2.398.1 2.651.64.7 1.028 1.595 1.028 2.688 0 3.848-2.339 4.695-4.566 4.943.359.309.678.92.678 1.855 0 1.338-.012 2.419-.012 2.747 0 .268.18.58.688.482A10.019 10.019 0 0022 12.017C22 6.484 17.522 2 12 2z" clipRule="evenodd" />
                    </svg>
                  </div>
                  <div>
                    <h3 className="font-bold mb-1 text-white">GitHub</h3>
                    <p className="text-gray-200">github.com/nautilus-ai</p>
                  </div>
                </div>
              </div>
            </div>

            <div className="bg-white/10 backdrop-blur-lg border border-white/20 text-white p-8 rounded-lg">
              <h3 className="text-xl font-bold mb-4">工作时间</h3>
              <p className="mb-2 text-gray-200">周一至周五：9:00 - 18:00 (UTC+8)</p>
              <p className="text-gray-200">周末和节假日：休息</p>
              <p className="mt-4 text-sm text-gray-300">
                我们通常在24小时内回复邮件
              </p>
            </div>
          </div>
        </div>

        {/* FAQ快速链接 */}
        <div className="mt-16 bg-white/10 backdrop-blur-lg border border-white/20 p-8 rounded-lg">
          <h2 className="text-2xl font-bold mb-4 text-center text-white">常见问题</h2>
          <p className="text-center text-gray-200 mb-6">
            在联系我们之前，您可能想先查看我们的常见问题解答
          </p>
          <div className="text-center">
            <a href="/docs#faq" className="inline-block bg-blue-500 text-white px-8 py-3 rounded-lg font-semibold hover:bg-blue-600 transition">
              查看FAQ
            </a>
          </div>
        </div>
      </div>
    </div>
  )
}
