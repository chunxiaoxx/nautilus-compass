export default function CareersPage() {
  const positions = [
    {
      id: 1,
      title: '高级后端工程师',
      department: '工程',
      location: '远程',
      type: '全职',
      description: '负责Nautilus后端系统的开发和优化，包括API设计、数据库优化、性能调优等。',
      requirements: [
        '5年以上后端开发经验',
        '精通Python/FastAPI或Node.js',
        '熟悉PostgreSQL和Redis',
        '有区块链开发经验优先'
      ]
    },
    {
      id: 2,
      title: '前端工程师',
      department: '工程',
      location: '远程',
      type: '全职',
      description: '负责Nautilus前端界面的开发，打造流畅的用户体验。',
      requirements: [
        '3年以上前端开发经验',
        '精通React和TypeScript',
        '熟悉Web3.js和钱包集成',
        '有DApp开发经验优先'
      ]
    },
    {
      id: 3,
      title: '区块链工程师',
      department: '工程',
      location: '远程',
      type: '全职',
      description: '负责智能合约开发和区块链集成，确保系统的安全性和可靠性。',
      requirements: [
        '3年以上区块链开发经验',
        '精通Solidity和智能合约开发',
        '熟悉Base/Ethereum生态',
        '有DeFi项目经验优先'
      ]
    },
    {
      id: 4,
      title: 'AI研究员',
      department: '研究',
      location: '远程',
      type: '全职',
      description: '研究AI Agent的进化机制和学习算法，推动EvoMap系统的发展。',
      requirements: [
        '机器学习或AI相关博士学位',
        '有强化学习研究经验',
        '熟悉知识图谱和记忆系统',
        '有论文发表经验优先'
      ]
    },
    {
      id: 5,
      title: '产品经理',
      department: '产品',
      location: '远程',
      type: '全职',
      description: '负责产品规划和需求管理，推动产品迭代和优化。',
      requirements: [
        '3年以上产品经理经验',
        '有AI或区块链产品经验',
        '优秀的沟通和协调能力',
        '有创业公司经验优先'
      ]
    },
    {
      id: 6,
      title: '社区运营',
      department: '运营',
      location: '远程',
      type: '全职',
      description: '负责社区建设和用户运营，扩大Nautilus的影响力。',
      requirements: [
        '2年以上社区运营经验',
        '熟悉Discord、Twitter等平台',
        '有Web3社区运营经验',
        '英文流利优先'
      ]
    }
  ]

  return (
    <div className="max-w-7xl mx-auto px-4 py-16">
      <div className="text-center mb-16">
        <h1 className="text-4xl font-bold mb-4">加入我们</h1>
        <p className="text-xl text-gray-600 max-w-3xl mx-auto">
          一起构建AI Agent生态系统的未来
        </p>
      </div>

      {/* 为什么加入我们 */}
      <section className="mb-16">
        <h2 className="text-3xl font-bold mb-8 text-center">为什么加入Nautilus</h2>
        <div className="grid md:grid-cols-3 gap-8">
          <div className="bg-white p-6 rounded-lg shadow">
            <div className="w-12 h-12 bg-blue-100 rounded-lg flex items-center justify-center mb-4">
              <svg className="w-6 h-6 text-blue-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
              </svg>
            </div>
            <h3 className="text-xl font-bold mb-3">前沿技术</h3>
            <p className="text-gray-600">
              在AI和区块链的交叉领域探索创新，参与构建下一代AI生态系统。
            </p>
          </div>

          <div className="bg-white p-6 rounded-lg shadow">
            <div className="w-12 h-12 bg-purple-100 rounded-lg flex items-center justify-center mb-4">
              <svg className="w-6 h-6 text-purple-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0zm6 3a2 2 0 11-4 0 2 2 0 014 0zM7 10a2 2 0 11-4 0 2 2 0 014 0z" />
              </svg>
            </div>
            <h3 className="text-xl font-bold mb-3">优秀团队</h3>
            <p className="text-gray-600">
              与来自顶尖科技公司的工程师和研究员一起工作，共同成长。
            </p>
          </div>

          <div className="bg-white p-6 rounded-lg shadow">
            <div className="w-12 h-12 bg-pink-100 rounded-lg flex items-center justify-center mb-4">
              <svg className="w-6 h-6 text-pink-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3.055 11H5a2 2 0 012 2v1a2 2 0 002 2 2 2 0 012 2v2.945M8 3.935V5.5A2.5 2.5 0 0010.5 8h.5a2 2 0 012 2 2 2 0 104 0 2 2 0 012-2h1.064M15 20.488V18a2 2 0 012-2h3.064M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
            </div>
            <h3 className="text-xl font-bold mb-3">远程优先</h3>
            <p className="text-gray-600">
              灵活的工作方式，全球化的团队，平衡工作与生活。
            </p>
          </div>
        </div>
      </section>

      {/* 福利待遇 */}
      <section className="mb-16">
        <h2 className="text-3xl font-bold mb-8 text-center">福利待遇</h2>
        <div className="bg-gradient-to-br from-blue-500 to-purple-600 text-white p-8 rounded-lg">
          <div className="grid md:grid-cols-2 gap-6">
            <div className="flex items-start">
              <svg className="w-6 h-6 mr-3 flex-shrink-0 mt-1" fill="currentColor" viewBox="0 0 20 20">
                <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
              </svg>
              <div>
                <h4 className="font-bold mb-1">有竞争力的薪资</h4>
                <p className="text-sm opacity-90">行业领先的薪资水平和股权激励</p>
              </div>
            </div>

            <div className="flex items-start">
              <svg className="w-6 h-6 mr-3 flex-shrink-0 mt-1" fill="currentColor" viewBox="0 0 20 20">
                <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
              </svg>
              <div>
                <h4 className="font-bold mb-1">灵活工作时间</h4>
                <p className="text-sm opacity-90">自主安排工作时间，注重结果而非过程</p>
              </div>
            </div>

            <div className="flex items-start">
              <svg className="w-6 h-6 mr-3 flex-shrink-0 mt-1" fill="currentColor" viewBox="0 0 20 20">
                <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
              </svg>
              <div>
                <h4 className="font-bold mb-1">学习成长</h4>
                <p className="text-sm opacity-90">技术培训、会议参与、书籍报销</p>
              </div>
            </div>

            <div className="flex items-start">
              <svg className="w-6 h-6 mr-3 flex-shrink-0 mt-1" fill="currentColor" viewBox="0 0 20 20">
                <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
              </svg>
              <div>
                <h4 className="font-bold mb-1">健康保障</h4>
                <p className="text-sm opacity-90">完善的医疗保险和年度体检</p>
              </div>
            </div>

            <div className="flex items-start">
              <svg className="w-6 h-6 mr-3 flex-shrink-0 mt-1" fill="currentColor" viewBox="0 0 20 20">
                <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
              </svg>
              <div>
                <h4 className="font-bold mb-1">团队活动</h4>
                <p className="text-sm opacity-90">定期团建、年度旅游、节日福利</p>
              </div>
            </div>

            <div className="flex items-start">
              <svg className="w-6 h-6 mr-3 flex-shrink-0 mt-1" fill="currentColor" viewBox="0 0 20 20">
                <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
              </svg>
              <div>
                <h4 className="font-bold mb-1">设备支持</h4>
                <p className="text-sm opacity-90">提供高性能工作设备和办公用品</p>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* 职位列表 */}
      <section className="mb-16">
        <h2 className="text-3xl font-bold mb-8 text-center">开放职位</h2>
        <div className="space-y-6">
          {positions.map(position => (
            <div key={position.id} className="bg-white p-6 rounded-lg shadow hover:shadow-lg transition">
              <div className="flex items-start justify-between mb-4">
                <div>
                  <h3 className="text-2xl font-bold mb-2">{position.title}</h3>
                  <div className="flex gap-4 text-sm text-gray-600">
                    <span className="flex items-center">
                      <svg className="w-4 h-4 mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 21V5a2 2 0 00-2-2H7a2 2 0 00-2 2v16m14 0h2m-2 0h-5m-9 0H3m2 0h5M9 7h1m-1 4h1m4-4h1m-1 4h1m-5 10v-5a1 1 0 011-1h2a1 1 0 011 1v5m-4 0h4" />
                      </svg>
                      {position.department}
                    </span>
                    <span className="flex items-center">
                      <svg className="w-4 h-4 mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17.657 16.657L13.414 20.9a1.998 1.998 0 01-2.827 0l-4.244-4.243a8 8 0 1111.314 0z" />
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 11a3 3 0 11-6 0 3 3 0 016 0z" />
                      </svg>
                      {position.location}
                    </span>
                    <span className="flex items-center">
                      <svg className="w-4 h-4 mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
                      </svg>
                      {position.type}
                    </span>
                  </div>
                </div>
                <button className="bg-blue-500 text-white px-6 py-2 rounded-lg font-semibold hover:bg-blue-600 transition">
                  申请职位
                </button>
              </div>

              <p className="text-gray-600 mb-4">{position.description}</p>

              <div>
                <h4 className="font-semibold mb-2">任职要求：</h4>
                <ul className="space-y-1">
                  {position.requirements.map((req, index) => (
                    <li key={index} className="flex items-start text-gray-600">
                      <svg className="w-5 h-5 text-blue-500 mr-2 flex-shrink-0 mt-0.5" fill="currentColor" viewBox="0 0 20 20">
                        <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
                      </svg>
                      {req}
                    </li>
                  ))}
                </ul>
              </div>
            </div>
          ))}
        </div>
      </section>

      {/* CTA */}
      <div className="bg-gray-50 p-12 rounded-lg text-center">
        <h2 className="text-3xl font-bold mb-4">没有找到合适的职位？</h2>
        <p className="text-xl text-gray-600 mb-6">
          我们一直在寻找优秀的人才，欢迎发送简历到
        </p>
        <a href="mailto:chunxiaoxx@gmail.com" className="text-blue-600 font-semibold text-xl hover:text-blue-700">
          chunxiaoxx@gmail.com
        </a>
      </div>
    </div>
  )
}
