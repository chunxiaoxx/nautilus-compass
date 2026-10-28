import { Link } from 'react-router-dom'
import { NAV_GROUPS } from './navConfig'
import { useLanguage } from '../../context/LanguageContext'

// 营销 / 公司页(不在运营导航组里 · 但 sitemap 必须兜底,保证无孤儿页)
const PRODUCT_LINKS = [
  { to: '/features', zh: '功能特性', en: 'Features' },
  { to: '/pricing', zh: '价格方案', en: 'Pricing' },
  { to: '/roadmap', zh: '产品路线图', en: 'Roadmap' },
  { to: '/blog', zh: '博客', en: 'Blog' },
]
const COMPANY_LINKS = [
  { to: '/about', zh: '关于我们', en: 'About' },
  { to: '/partners', zh: '合作伙伴', en: 'Partners' },
  { to: '/contact', zh: '联系我们', en: 'Contact' },
  { to: '/careers', zh: '加入我们', en: 'Careers' },
]

export default function Footer() {
  const { t, language } = useLanguage()
  const nav = t.nav as Record<string, string>
  const tr = (key: string) => nav[key] ?? key
  const L = (item: { zh: string; en: string }) => (language === 'zh' ? item.zh : item.en)

  return (
    <footer className="bg-dark-800 border-t border-dark-700">
      <div className="container mx-auto px-6 py-12">
        <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-8">
          {/* Brand */}
          <div className="col-span-2 md:col-span-3 lg:col-span-1">
            <h3 className="text-xl font-bold gradient-text mb-4">Nautilus</h3>
            <p className="text-dark-400 text-sm">
              {language === 'zh' ? '多智能体任务协作平台' : 'Multi-agent task collaboration platform'}
              <br />
              {language === 'zh' ? '区块链驱动的去中心化任务市场' : 'Blockchain-powered decentralized task market'}
            </p>
          </div>

          {/* 全站 sitemap · 复用 navConfig(单一数据源 · nav 变这里自动同步)*/}
          {NAV_GROUPS.map((group) => (
            <div key={group.labelKey}>
              <h4 className="font-semibold mb-4">{tr(group.labelKey)}</h4>
              <ul className="space-y-2 text-sm text-dark-400">
                {group.items.map((item) => (
                  <li key={item.to}>
                    <Link to={item.to} className="hover:text-primary-400 transition">
                      {tr(item.labelKey)}
                    </Link>
                  </li>
                ))}
              </ul>
            </div>
          ))}

          {/* 产品 + 公司(营销页兜底)*/}
          <div>
            <h4 className="font-semibold mb-4">{language === 'zh' ? '产品' : 'Product'}</h4>
            <ul className="space-y-2 text-sm text-dark-400">
              {PRODUCT_LINKS.map((item) => (
                <li key={item.to}>
                  <Link to={item.to} className="hover:text-primary-400 transition">{L(item)}</Link>
                </li>
              ))}
            </ul>
            <h4 className="font-semibold mb-4 mt-6">{language === 'zh' ? '公司' : 'Company'}</h4>
            <ul className="space-y-2 text-sm text-dark-400">
              {COMPANY_LINKS.map((item) => (
                <li key={item.to}>
                  <Link to={item.to} className="hover:text-primary-400 transition">{L(item)}</Link>
                </li>
              ))}
            </ul>
          </div>
        </div>

        <div className="mt-12 pt-8 border-t border-dark-700 text-center text-sm text-dark-400">
          <p>&copy; 2026 Nautilus. All rights reserved.</p>
        </div>
      </div>
    </footer>
  )
}
