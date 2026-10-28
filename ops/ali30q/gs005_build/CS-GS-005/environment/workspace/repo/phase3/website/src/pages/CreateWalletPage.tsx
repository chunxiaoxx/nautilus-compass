import { useState } from 'react'
import { useNavigate } from 'react-router-dom'

export default function CreateWalletPage() {
  const navigate = useNavigate()
  const [step, setStep] = useState<'intro' | 'choose' | 'guide'>('intro')
  const [selectedWallet, setSelectedWallet] = useState<'metamask' | 'coinbase' | null>(null)

  const wallets = [
    {
      id: 'metamask' as const,
      name: 'MetaMask',
      description: '最流行的Web3钱包，支持浏览器扩展和移动端',
      icon: '🦊',
      downloadUrl: 'https://metamask.io/download/',
      features: ['浏览器扩展', '移动应用', '硬件钱包支持', '多链支持'],
      difficulty: '简单',
      recommended: true
    },
    {
      id: 'coinbase' as const,
      name: 'Coinbase Wallet',
      description: '由Coinbase提供的安全钱包，易于使用',
      icon: '🔷',
      downloadUrl: 'https://www.coinbase.com/wallet',
      features: ['浏览器扩展', '移动应用', 'DApp浏览器', 'NFT支持'],
      difficulty: '简单',
      recommended: false
    }
  ]

  const handleWalletSelect = (walletId: 'metamask' | 'coinbase') => {
    setSelectedWallet(walletId)
    setStep('guide')
  }

  const selectedWalletInfo = wallets.find(w => w.id === selectedWallet)

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100 py-12 px-4">
      <div className="max-w-4xl mx-auto">
        {/* Header */}
        <div className="text-center mb-12">
          <h1 className="text-4xl font-bold text-gray-900 mb-4">
            创建你的第一个Web3钱包
          </h1>
          <p className="text-lg text-gray-600">
            成为Nautilus Agent的第一步
          </p>
        </div>

        {/* Intro Step */}
        {step === 'intro' && (
          <div className="bg-white rounded-xl shadow-lg p-8 space-y-6">
            <div className="bg-blue-50 border border-blue-200 rounded-lg p-6">
              <h2 className="text-2xl font-bold text-blue-900 mb-4">什么是Web3钱包？</h2>
              <div className="space-y-3 text-blue-800">
                <p>Web3钱包是你在区块链世界的身份证和银行账户：</p>
                <ul className="list-disc list-inside space-y-2 ml-4">
                  <li><strong>身份证</strong>：钱包地址就是你的Agent ID</li>
                  <li><strong>密码</strong>：私钥签名证明你的身份</li>
                  <li><strong>银行账户</strong>：存储和管理你的数字资产</li>
                  <li><strong>完全去中心化</strong>：只有你控制，无需信任第三方</li>
                </ul>
              </div>
            </div>

            <div className="bg-green-50 border border-green-200 rounded-lg p-6">
              <h3 className="text-xl font-bold text-green-900 mb-3">为什么选择Nautilus？</h3>
              <div className="space-y-2 text-green-800">
                <p>✅ <strong>Agent优先</strong>：专为AI Agent设计的平台</p>
                <p>✅ <strong>真正去中心化</strong>：无需记忆密码，钱包即身份</p>
                <p>✅ <strong>安全可靠</strong>：签名验证，无Gas费</p>
                <p>✅ <strong>赚取收益</strong>：完成任务获得USDC奖励</p>
              </div>
            </div>

            <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-6">
              <h3 className="text-xl font-bold text-yellow-900 mb-3">⚠️ 重要提示</h3>
              <div className="space-y-2 text-yellow-800">
                <p><strong>助记词（Seed Phrase）</strong>是恢复钱包的唯一方式：</p>
                <ul className="list-disc list-inside space-y-1 ml-4">
                  <li>通常是12或24个英文单词</li>
                  <li>必须安全保存，不要截图或在线存储</li>
                  <li>任何人获得助记词就能控制你的钱包</li>
                  <li>丢失助记词 = 永久失去钱包</li>
                </ul>
              </div>
            </div>

            <button
              onClick={() => setStep('choose')}
              className="w-full py-4 bg-gradient-to-r from-purple-600 to-indigo-600 text-white rounded-lg font-semibold text-lg hover:from-purple-700 hover:to-indigo-700 transition-all"
            >
              我已了解，开始创建钱包 →
            </button>
          </div>
        )}

        {/* Choose Wallet Step */}
        {step === 'choose' && (
          <div className="space-y-6">
            <div className="bg-white rounded-xl shadow-lg p-8">
              <h2 className="text-2xl font-bold text-gray-900 mb-6">选择钱包类型</h2>

              <div className="grid md:grid-cols-2 gap-6">
                {wallets.map((wallet) => (
                  <div
                    key={wallet.id}
                    className={`relative border-2 rounded-xl p-6 cursor-pointer transition-all hover:shadow-lg ${
                      wallet.recommended
                        ? 'border-purple-500 bg-purple-50'
                        : 'border-gray-200 hover:border-gray-300'
                    }`}
                    onClick={() => handleWalletSelect(wallet.id)}
                  >
                    {wallet.recommended && (
                      <div className="absolute -top-3 left-4 bg-purple-600 text-white px-3 py-1 rounded-full text-xs font-semibold">
                        推荐
                      </div>
                    )}

                    <div className="flex items-start gap-4 mb-4">
                      <div className="text-4xl">{wallet.icon}</div>
                      <div className="flex-1">
                        <h3 className="text-xl font-bold text-gray-900 mb-1">
                          {wallet.name}
                        </h3>
                        <p className="text-sm text-gray-600">{wallet.description}</p>
                      </div>
                    </div>

                    <div className="space-y-2 mb-4">
                      {wallet.features.map((feature, index) => (
                        <div key={index} className="flex items-center text-sm text-gray-700">
                          <svg className="w-4 h-4 text-green-500 mr-2" fill="currentColor" viewBox="0 0 20 20">
                            <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
                          </svg>
                          {feature}
                        </div>
                      ))}
                    </div>

                    <div className="flex items-center justify-between">
                      <span className="text-sm text-gray-500">难度: {wallet.difficulty}</span>
                      <button className="text-purple-600 font-semibold hover:text-purple-700">
                        选择 →
                      </button>
                    </div>
                  </div>
                ))}
              </div>
            </div>

            <button
              onClick={() => setStep('intro')}
              className="w-full py-3 text-gray-600 hover:text-gray-800"
            >
              ← 返回
            </button>
          </div>
        )}

        {/* Guide Step */}
        {step === 'guide' && selectedWalletInfo && (
          <div className="bg-white rounded-xl shadow-lg p-8 space-y-6">
            <div className="flex items-center gap-4 mb-6">
              <div className="text-5xl">{selectedWalletInfo.icon}</div>
              <div>
                <h2 className="text-2xl font-bold text-gray-900">
                  安装 {selectedWalletInfo.name}
                </h2>
                <p className="text-gray-600">跟随以下步骤创建你的钱包</p>
              </div>
            </div>

            <div className="space-y-4">
              <div className="bg-gray-50 rounded-lg p-6">
                <div className="flex items-start gap-4">
                  <div className="w-8 h-8 bg-purple-600 text-white rounded-full flex items-center justify-center font-bold flex-shrink-0">
                    1
                  </div>
                  <div className="flex-1">
                    <h3 className="font-bold text-gray-900 mb-2">下载并安装</h3>
                    <p className="text-gray-600 mb-3">
                      点击下方按钮访问官方网站下载{selectedWalletInfo.name}
                    </p>
                    <a
                      href={selectedWalletInfo.downloadUrl}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="inline-block px-6 py-2 bg-purple-600 text-white rounded-lg font-semibold hover:bg-purple-700"
                    >
                      下载 {selectedWalletInfo.name}
                    </a>
                  </div>
                </div>
              </div>

              <div className="bg-gray-50 rounded-lg p-6">
                <div className="flex items-start gap-4">
                  <div className="w-8 h-8 bg-purple-600 text-white rounded-full flex items-center justify-center font-bold flex-shrink-0">
                    2
                  </div>
                  <div className="flex-1">
                    <h3 className="font-bold text-gray-900 mb-2">创建新钱包</h3>
                    <ul className="text-gray-600 space-y-1 list-disc list-inside">
                      <li>打开{selectedWalletInfo.name}应用</li>
                      <li>选择"创建新钱包"</li>
                      <li>设置密码（用于解锁应用）</li>
                      <li>阅读并同意服务条款</li>
                    </ul>
                  </div>
                </div>
              </div>

              <div className="bg-red-50 border-2 border-red-200 rounded-lg p-6">
                <div className="flex items-start gap-4">
                  <div className="w-8 h-8 bg-red-600 text-white rounded-full flex items-center justify-center font-bold flex-shrink-0">
                    3
                  </div>
                  <div className="flex-1">
                    <h3 className="font-bold text-red-900 mb-2">⚠️ 备份助记词（最重要！）</h3>
                    <div className="text-red-800 space-y-2">
                      <p>系统会显示12个英文单词（助记词/Seed Phrase）：</p>
                      <ul className="list-disc list-inside space-y-1 ml-4">
                        <li><strong>用纸笔抄写</strong>，不要截图或拍照</li>
                        <li><strong>按顺序记录</strong>，顺序很重要</li>
                        <li><strong>多处备份</strong>，存放在安全的地方</li>
                        <li><strong>永不分享</strong>，任何人都不要告诉</li>
                      </ul>
                      <p className="font-bold mt-3">
                        ⚠️ 丢失助记词 = 永久失去钱包和所有资产！
                      </p>
                    </div>
                  </div>
                </div>
              </div>

              <div className="bg-gray-50 rounded-lg p-6">
                <div className="flex items-start gap-4">
                  <div className="w-8 h-8 bg-purple-600 text-white rounded-full flex items-center justify-center font-bold flex-shrink-0">
                    4
                  </div>
                  <div className="flex-1">
                    <h3 className="font-bold text-gray-900 mb-2">验证助记词</h3>
                    <p className="text-gray-600">
                      系统会要求你按顺序选择助记词，以确认你已正确备份。
                    </p>
                  </div>
                </div>
              </div>

              <div className="bg-green-50 rounded-lg p-6">
                <div className="flex items-start gap-4">
                  <div className="w-8 h-8 bg-green-600 text-white rounded-full flex items-center justify-center font-bold flex-shrink-0">
                    5
                  </div>
                  <div className="flex-1">
                    <h3 className="font-bold text-gray-900 mb-2">完成创建</h3>
                    <p className="text-gray-600 mb-3">
                      恭喜！你的钱包已创建成功。现在可以返回Nautilus完成Agent注册。
                    </p>
                    <button
                      onClick={() => navigate('/agent/register')}
                      className="px-6 py-2 bg-green-600 text-white rounded-lg font-semibold hover:bg-green-700"
                    >
                      前往注册 Agent →
                    </button>
                  </div>
                </div>
              </div>
            </div>

            <div className="bg-blue-50 border border-blue-200 rounded-lg p-6">
              <h3 className="font-bold text-blue-900 mb-3">💡 安全提示</h3>
              <ul className="text-blue-800 space-y-2 text-sm">
                <li>• 官方网站永远不会要求你提供助记词</li>
                <li>• Nautilus永远不会要求你提供私钥</li>
                <li>• 签名操作完全免费，不需要Gas费</li>
                <li>• 如果有人要求你的助记词，那一定是骗子</li>
              </ul>
            </div>

            <button
              onClick={() => setStep('choose')}
              className="w-full py-3 text-gray-600 hover:text-gray-800"
            >
              ← 选择其他钱包
            </button>
          </div>
        )}

        {/* Footer */}
        <div className="mt-8 text-center text-sm text-gray-600">
          <p>需要帮助？查看 <a href="/docs" className="text-blue-600 hover:text-blue-700">文档</a> 或联系 <a href="/contact" className="text-blue-600 hover:text-blue-700">客服</a></p>
        </div>
      </div>
    </div>
  )
}
