import { useState } from 'react'
import { Link } from 'react-router-dom'

const API_URL = import.meta.env.VITE_API_URL || ''

const TASK_TYPES = [
  { type: 'jc_constitutive', name: 'J-C 本构模型拟合', market: 3000, our: 450, desc: 'Johnson-Cook 本构参数反求，输出 A/B/C/n/m + R²' },
  { type: 'thmc_coupling', name: 'THMC 多场耦合', market: 5000, our: 750, desc: '热-水-力-化学多场耦合仿真' },
  { type: 'curve_fitting', name: '曲线拟合 / 回归', market: 1500, our: 150, desc: '多项式/指数/自定义函数拟合' },
  { type: 'ode_simulation', name: 'ODE 系统仿真', market: 2000, our: 240, desc: '常微分方程组数值求解' },
  { type: 'pde_simulation', name: 'PDE 数值解', market: 2500, our: 300, desc: '偏微分方程有限差分/有限元' },
  { type: 'ml_training', name: '机器学习训练', market: 3000, our: 360, desc: '模型训练+评估+可视化' },
  { type: 'monte_carlo', name: 'Monte Carlo 仿真', market: 1500, our: 150, desc: '随机模拟/风险分析' },
  { type: 'physics_simulation', name: '物理仿真', market: 2500, our: 300, desc: '力学/流体/电磁仿真' },
  { type: 'statistical_analysis', name: '统计分析', market: 1500, our: 150, desc: '假设检验/回归分析/方差分析' },
]

const STEPS = [
  {
    num: '01',
    title: '签约开户',
    desc: '签订合作协议，我们为您创建专属 API 账户，分配独立的 API Key。',
  },
  {
    num: '02',
    title: '预充值',
    desc: '通过银行转账/支付宝预充值到账户余额。大额充值享额外折扣。',
  },
  {
    num: '03',
    title: 'API 对接',
    desc: '将我们的 API 集成到您的系统中。提供 Python SDK 和完整接口文档，对接通常 1-2 天。',
  },
  {
    num: '04',
    title: '提交任务',
    desc: '通过 API 提交计算任务，自动执行并返回结果。支持单个和批量提交（最多 50 个/批）。',
  },
  {
    num: '05',
    title: '结果交付',
    desc: '任务完成后通过 Webhook 实时通知，或主动轮询获取结果。包含代码、数据和图表。',
  },
  {
    num: '06',
    title: '对账结算',
    desc: '实时查看余额和消费明细。失败任务自动退款。月度对账报表。',
  },
]

const CODE_EXAMPLE = `from partner_sdk import ComputeClient

client = ComputeClient(
    api_key="your_api_key",
    base_url="https://api.your-domain.cn"
)

# 提交 J-C 本构拟合任务
task = client.submit(
    task_type="jc_constitutive",
    title="TC4 钛合金 J-C 参数拟合",
    description="根据实验数据拟合 Johnson-Cook 本构模型参数",
    input_data="strain_rate,temperature,stress\\n0.001,293,450\\n..."
)

# 等待结果（自动轮询，最长 5 分钟）
result = client.wait_for_result(task["task_id"])

print(result["result"]["output"])
# → A=792.3 MPa, B=510.2 MPa, C=0.014, n=0.26, m=1.03, R²=0.956`

const API_ENDPOINTS = [
  { method: 'POST', path: '/api/v1/tasks', desc: '提交计算任务' },
  { method: 'POST', path: '/api/v1/tasks/batch', desc: '批量提交（最多 50 个）' },
  { method: 'GET', path: '/api/v1/tasks/{id}', desc: '查询任务状态和结果' },
  { method: 'GET', path: '/api/v1/tasks', desc: '任务列表（支持筛选）' },
  { method: 'GET', path: '/api/v1/balance', desc: '查询账户余额' },
  { method: 'GET', path: '/api/v1/prices', desc: '查询价格表' },
  { method: 'GET', path: '/api/v1/stats', desc: '用量统计' },
]

export default function PartnerPage() {
  const [activeTab, setActiveTab] = useState<'pricing' | 'api' | 'faq'>('pricing')

  return (
    <div className="min-h-screen bg-linear-black">
      <div className="max-w-6xl mx-auto px-4 py-16">

        {/* Hero */}
        <div className="text-center mb-16">
          <h1 className="text-4xl md:text-5xl font-bold text-white mb-4">
            AI 科学计算 API
          </h1>
          <p className="text-xl text-gray-300 mb-2">
            为您的业务提供强大的学术仿真和数据分析能力
          </p>
          <p className="text-gray-400 max-w-2xl mx-auto">
            白标 API 接入，您的客户只看到您的品牌。涵盖 J-C 本构、THMC 耦合、曲线拟合、
            ODE/PDE 仿真、机器学习等 11 种任务类型。
          </p>
          <div className="flex justify-center gap-6 mt-8">
            <div className="text-center">
              <div className="text-3xl font-bold text-blue-400">70%</div>
              <div className="text-xs text-gray-400">成本节省</div>
            </div>
            <div className="text-center">
              <div className="text-3xl font-bold text-green-400">90%+</div>
              <div className="text-xs text-gray-400">任务成功率</div>
            </div>
            <div className="text-center">
              <div className="text-3xl font-bold text-purple-400">30s</div>
              <div className="text-xs text-gray-400">平均排队时间</div>
            </div>
            <div className="text-center">
              <div className="text-3xl font-bold text-yellow-400">24/7</div>
              <div className="text-xs text-gray-400">全天候服务</div>
            </div>
          </div>
        </div>

        {/* How It Works */}
        <div className="mb-16">
          <h2 className="text-2xl font-bold text-white text-center mb-8">合作流程</h2>
          <div className="grid md:grid-cols-3 gap-6">
            {STEPS.map(s => (
              <div key={s.num} className="bg-white/5 backdrop-blur-lg border border-white/10 rounded-xl p-6">
                <div className="text-3xl font-bold text-blue-500/50 mb-2">{s.num}</div>
                <h3 className="text-lg font-semibold text-white mb-2">{s.title}</h3>
                <p className="text-sm text-gray-400">{s.desc}</p>
              </div>
            ))}
          </div>
        </div>

        {/* Tabs */}
        <div className="flex justify-center mb-8">
          <div className="flex bg-white/10 rounded-lg p-1">
            {[
              { key: 'pricing' as const, label: '价格表' },
              { key: 'api' as const, label: 'API 接口' },
              { key: 'faq' as const, label: '常见问题' },
            ].map(t => (
              <button
                key={t.key}
                onClick={() => setActiveTab(t.key)}
                className={`px-6 py-2 rounded-md text-sm font-medium transition-colors ${
                  activeTab === t.key ? 'bg-white text-gray-900 shadow' : 'text-gray-300 hover:text-white'
                }`}
              >
                {t.label}
              </button>
            ))}
          </div>
        </div>

        {/* Pricing Tab */}
        {activeTab === 'pricing' && (
          <div className="mb-16">
            <p className="text-center text-gray-400 text-sm mb-6">
              以下为合作伙伴专享批发价（零售价的 30%）。实际折扣率可协商。
            </p>
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b border-white/20">
                    <th className="text-left py-3 px-4 text-gray-400 font-medium">任务类型</th>
                    <th className="text-right py-3 px-4 text-gray-400 font-medium">市场价</th>
                    <th className="text-right py-3 px-4 text-gray-400 font-medium">您的成本</th>
                    <th className="text-right py-3 px-4 text-gray-400 font-medium">您的利润空间</th>
                    <th className="text-left py-3 px-4 text-gray-400 font-medium">说明</th>
                  </tr>
                </thead>
                <tbody>
                  {TASK_TYPES.map(t => (
                    <tr key={t.type} className="border-b border-white/10 hover:bg-white/5">
                      <td className="py-3 px-4 text-white font-medium">{t.name}</td>
                      <td className="py-3 px-4 text-right text-gray-400">{t.market.toLocaleString()}</td>
                      <td className="py-3 px-4 text-right text-green-400 font-semibold">{t.our.toLocaleString()}</td>
                      <td className="py-3 px-4 text-right text-yellow-400">
                        {(t.market - t.our).toLocaleString()}
                        <span className="text-xs text-gray-500 ml-1">
                          ({Math.round((t.market - t.our) / t.market * 100)}%)
                        </span>
                      </td>
                      <td className="py-3 px-4 text-gray-500 text-xs">{t.desc}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
            <div className="mt-6 p-4 bg-blue-500/10 border border-blue-500/30 rounded-lg text-sm text-blue-300">
              大额预充值优惠：5 万+ 享 25% 折扣率，10 万+ 享 20% 折扣率。失败任务全额退款。
            </div>
          </div>
        )}

        {/* API Tab */}
        {activeTab === 'api' && (
          <div className="mb-16 space-y-8">
            {/* Endpoints */}
            <div>
              <h3 className="text-lg font-semibold text-white mb-4">API 端点</h3>
              <div className="space-y-2">
                {API_ENDPOINTS.map((ep, i) => (
                  <div key={i} className="flex items-center gap-4 bg-white/5 rounded-lg px-4 py-3">
                    <span className={`px-2 py-0.5 rounded text-xs font-mono font-bold ${
                      ep.method === 'POST' ? 'bg-green-500/20 text-green-300' : 'bg-blue-500/20 text-blue-300'
                    }`}>
                      {ep.method}
                    </span>
                    <code className="text-gray-300 text-sm font-mono flex-1">{ep.path}</code>
                    <span className="text-gray-500 text-sm">{ep.desc}</span>
                  </div>
                ))}
              </div>
              <p className="text-xs text-gray-500 mt-2">
                所有请求需携带 <code className="text-gray-400">X-API-Key</code> 请求头。完整文档随 API Key 一同提供。
              </p>
            </div>

            {/* Code Example */}
            <div>
              <h3 className="text-lg font-semibold text-white mb-4">Python SDK 示例</h3>
              <pre className="bg-black/50 rounded-xl p-6 text-sm text-green-300 font-mono overflow-x-auto whitespace-pre">
                {CODE_EXAMPLE}
              </pre>
              <p className="text-xs text-gray-500 mt-2">
                提供完整 Python SDK，开箱即用。也支持任何语言通过 HTTP 直接调用。
              </p>
            </div>

            {/* Webhook */}
            <div>
              <h3 className="text-lg font-semibold text-white mb-4">Webhook 回调</h3>
              <div className="bg-white/5 rounded-xl p-6 text-sm text-gray-300">
                <p className="mb-3">任务完成/失败后，我们会向您注册的 Webhook URL 发送 POST 请求：</p>
                <pre className="bg-black/30 rounded-lg p-4 text-xs text-blue-300 font-mono overflow-x-auto">{`{
  "event": "task.completed",
  "task_id": "acad_xxx",
  "external_ref": "your-tracking-id",
  "status": "completed",
  "result": {
    "output": "A=792.3, B=510.2, C=0.014...",
    "execution_time": 21.5
  }
}`}</pre>
                <p className="mt-3 text-xs text-gray-500">10 秒超时，最多重试 3 次。您的端点返回 2xx 即视为成功。</p>
              </div>
            </div>
          </div>
        )}

        {/* FAQ Tab */}
        {activeTab === 'faq' && (
          <div className="mb-16 space-y-4">
            {[
              {
                q: '对接需要多长时间？',
                a: '提供 Python SDK 和完整 API 文档，技术对接通常 1-2 天即可完成。我们提供全程技术支持。',
              },
              {
                q: '我的客户能看到你们的平台吗？',
                a: '不能。API 响应完全品牌中立，不包含任何平台信息。您可以部署到自己的域名下，客户只会看到您的品牌。',
              },
              {
                q: '任务失败怎么办？',
                a: '任务失败会自动全额退款到您的账户余额。当前任务成功率 90% 以上，持续优化中。',
              },
              {
                q: '支持哪些任务类型？',
                a: '目前支持 11 种学术计算任务（J-C 本构、THMC 耦合、曲线拟合、ODE/PDE 仿真、机器学习等），数据标注和仿真模拟即将上线。',
              },
              {
                q: '如何充值？',
                a: '支持银行转账、支付宝、微信转账。转账后联系我们确认，通常 1 小时内到账。大额充值享额外折扣。',
              },
              {
                q: '有没有最低充值要求？',
                a: '无最低充值要求。建议首次充值 5000 元起步，可覆盖约 10-30 个任务。',
              },
              {
                q: '数据安全如何保障？',
                a: '所有数据传输使用 HTTPS 加密。任务数据存储在隔离环境中，不同合作伙伴之间完全隔离。任务完成后可选择自动清理。',
              },
              {
                q: '能同时提交多个任务吗？',
                a: '支持批量提交，单次最多 50 个任务。系统会并行执行（最多 3 个同时运行），大幅提升效率。',
              },
            ].map((item, i) => (
              <details key={i} className="bg-white/5 rounded-xl border border-white/10 overflow-hidden group">
                <summary className="px-6 py-4 text-white font-medium cursor-pointer hover:bg-white/5 transition">
                  {item.q}
                </summary>
                <div className="px-6 pb-4 text-sm text-gray-400">{item.a}</div>
              </details>
            ))}
          </div>
        )}

        {/* CTA */}
        <div className="text-center bg-white/5 backdrop-blur-lg border border-white/10 rounded-2xl p-10">
          <h2 className="text-2xl font-bold text-white mb-3">开始合作</h2>
          <p className="text-gray-400 mb-6">
            联系我们获取 API Key，最快当天完成对接
          </p>
          <div className="flex justify-center gap-4">
            <Link
              to="/contact"
              className="px-8 py-3 bg-blue-600 hover:bg-blue-700 text-white rounded-lg font-medium transition"
            >
              联系商务
            </Link>
            <a
              href={`${API_URL}/docs`}
              target="_blank"
              rel="noopener noreferrer"
              className="px-8 py-3 bg-white/10 hover:bg-white/20 text-white rounded-lg font-medium transition"
            >
              API 文档
            </a>
          </div>
        </div>

      </div>
    </div>
  )
}
