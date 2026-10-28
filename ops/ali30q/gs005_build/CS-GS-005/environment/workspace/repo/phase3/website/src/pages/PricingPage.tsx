export default function PricingPage() {
  return (
    <div className="min-h-screen bg-linear-black">
      <div className="max-w-7xl mx-auto px-4 py-16">
        <div className="text-center mb-12">
          <h1 className="text-4xl font-bold mb-4 text-white">价格方案</h1>
          <p className="text-xl text-gray-200">灵活的定价，适合各种规模的需求</p>
        </div>

        <div className="grid md:grid-cols-3 gap-8">
          {/* 免费版 */}
          <div className="bg-white/10 backdrop-blur-lg p-8 rounded-lg shadow-xl border-2 border-white/20">
            <h3 className="text-2xl font-bold mb-4 text-white">免费版</h3>
            <div className="mb-6">
              <span className="text-4xl font-bold text-white">$0</span>
              <span className="text-gray-200">/月</span>
            </div>
            <ul className="space-y-3 mb-8">
              <li className="flex items-center text-gray-200">
                <svg className="w-5 h-5 text-green-400 mr-2" fill="currentColor" viewBox="0 0 20 20">
                  <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
                </svg>
                最多5个任务/月
              </li>
              <li className="flex items-center text-gray-200">
                <svg className="w-5 h-5 text-green-400 mr-2" fill="currentColor" viewBox="0 0 20 20">
                  <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
                </svg>
                基础Agent功能
              </li>
              <li className="flex items-center text-gray-200">
                <svg className="w-5 h-5 text-green-400 mr-2" fill="currentColor" viewBox="0 0 20 20">
                  <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
                </svg>
                社区支持
              </li>
            </ul>
            <button className="w-full bg-white/20 text-white py-3 rounded-lg font-semibold hover:bg-white/30 transition border border-white/30">
              开始使用
            </button>
          </div>

          {/* 专业版 */}
          <div className="bg-white/10 backdrop-blur-lg p-8 rounded-lg shadow-xl border-2 border-blue-400 relative">
            <div className="absolute top-0 right-0 bg-blue-500 text-white px-4 py-1 rounded-bl-lg rounded-tr-lg text-sm font-semibold">
              推荐
            </div>
            <h3 className="text-2xl font-bold mb-4 text-white">专业版</h3>
            <div className="mb-6">
              <span className="text-4xl font-bold text-white">$49</span>
              <span className="text-gray-200">/月</span>
            </div>
            <ul className="space-y-3 mb-8">
              <li className="flex items-center text-gray-200">
                <svg className="w-5 h-5 text-green-400 mr-2" fill="currentColor" viewBox="0 0 20 20">
                  <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
                </svg>
                无限任务
              </li>
              <li className="flex items-center text-gray-200">
                <svg className="w-5 h-5 text-green-400 mr-2" fill="currentColor" viewBox="0 0 20 20">
                  <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
                </svg>
                高级Agent功能
              </li>
              <li className="flex items-center text-gray-200">
                <svg className="w-5 h-5 text-green-400 mr-2" fill="currentColor" viewBox="0 0 20 20">
                  <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
                </svg>
                优先匹配
              </li>
              <li className="flex items-center text-gray-200">
                <svg className="w-5 h-5 text-green-400 mr-2" fill="currentColor" viewBox="0 0 20 20">
                  <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
                </svg>
                邮件支持
              </li>
            </ul>
            <button className="w-full bg-blue-500 text-white py-3 rounded-lg font-semibold hover:bg-blue-600 transition">
              立即订阅
            </button>
          </div>

          {/* 企业版 */}
          <div className="bg-white/10 backdrop-blur-lg p-8 rounded-lg shadow-xl border-2 border-white/20">
            <h3 className="text-2xl font-bold mb-4 text-white">企业版</h3>
            <div className="mb-6">
              <span className="text-4xl font-bold text-white">定制</span>
            </div>
            <ul className="space-y-3 mb-8">
              <li className="flex items-center text-gray-200">
                <svg className="w-5 h-5 text-green-400 mr-2" fill="currentColor" viewBox="0 0 20 20">
                  <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
                </svg>
                专业版所有功能
              </li>
              <li className="flex items-center text-gray-200">
                <svg className="w-5 h-5 text-green-400 mr-2" fill="currentColor" viewBox="0 0 20 20">
                  <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
                </svg>
                私有部署
              </li>
              <li className="flex items-center text-gray-200">
                <svg className="w-5 h-5 text-green-400 mr-2" fill="currentColor" viewBox="0 0 20 20">
                  <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
                </svg>
                专属客户经理
              </li>
              <li className="flex items-center text-gray-200">
                <svg className="w-5 h-5 text-green-400 mr-2" fill="currentColor" viewBox="0 0 20 20">
                  <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
                </svg>
                SLA保障
              </li>
            </ul>
            <button className="w-full bg-white text-gray-900 py-3 rounded-lg font-semibold hover:bg-gray-100 transition">
              联系销售
            </button>
          </div>
        </div>

        <div className="mt-16 text-center">
          <h2 className="text-2xl font-bold mb-4 text-white">常见问题</h2>
          <div className="max-w-3xl mx-auto text-left space-y-4">
            <div className="bg-white/10 backdrop-blur-lg p-6 rounded-lg shadow-xl border border-white/20">
              <h3 className="font-bold mb-2 text-white">如何支付？</h3>
              <p className="text-gray-200">支持USDC加密货币支付，基于Base链，安全快捷。</p>
            </div>
            <div className="bg-white/10 backdrop-blur-lg p-6 rounded-lg shadow-xl border border-white/20">
              <h3 className="font-bold mb-2 text-white">可以随时取消吗？</h3>
              <p className="text-gray-200">是的，您可以随时取消订阅，不收取任何额外费用。</p>
            </div>
            <div className="bg-white/10 backdrop-blur-lg p-6 rounded-lg shadow-xl border border-white/20">
              <h3 className="font-bold mb-2 text-white">有试用期吗？</h3>
              <p className="text-gray-200">专业版提供7天免费试用，无需信用卡。</p>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
