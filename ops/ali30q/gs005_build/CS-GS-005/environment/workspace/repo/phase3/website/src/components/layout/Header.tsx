import { Link, useNavigate } from 'react-router-dom'
import { useState } from 'react'
import { useAuthCheck, useLogout } from '../../hooks/useAuth'
import { useLanguage } from '../../context/LanguageContext'
import { useTheme } from '../../context/ThemeContext'
import { NAV_GROUPS } from './navConfig'

export default function Header() {
  const [isMenuOpen, setIsMenuOpen] = useState(false)
  const [isUserMenuOpen, setIsUserMenuOpen] = useState(false)
  const [openGroup, setOpenGroup] = useState<string | null>(null)
  const [mobileGroup, setMobileGroup] = useState<string | null>(null)
  const { isAuthenticated, user } = useAuthCheck()
  const { logout } = useLogout()
  const navigate = useNavigate()
  const { language, toggleLanguage, t } = useLanguage()
  const { toggleTheme, isDark } = useTheme()

  // dynamic i18n lookup (nav keys are added in i18n/*.json)
  const nav = t.nav as Record<string, string>
  const tr = (key: string) => nav[key] ?? key

  const handleLogout = () => {
    logout()
    navigate('/login')
    setIsUserMenuOpen(false)
  }

  const closeAll = () => {
    setOpenGroup(null)
    setIsMenuOpen(false)
    setMobileGroup(null)
  }

  return (
    <header className="fixed top-0 left-0 right-0 z-50 glass">
      <nav className="container mx-auto px-6 py-4">
        <div className="flex items-center justify-between">
          {/* Logo */}
          <Link to="/" className="text-2xl font-bold gradient-text" onClick={closeAll}>
            Nautilus
          </Link>

          {/* click-outside backdrop to close any open dropdown */}
          {openGroup && (
            <div className="fixed inset-0 z-40" onClick={() => setOpenGroup(null)} aria-hidden="true" />
          )}

          {/* Desktop Navigation — grouped dropdowns */}
          <div className="hidden md:flex items-center space-x-1">
            {NAV_GROUPS.map((group) => (
              <div key={group.labelKey} className="relative">
                <button
                  type="button"
                  className="flex items-center gap-1 px-3 py-2 rounded-lg text-sm font-medium text-dark-200 hover:text-white hover:bg-white/5 transition"
                  onClick={() =>
                    setOpenGroup((g) => (g === group.labelKey ? null : group.labelKey))
                  }
                  aria-expanded={openGroup === group.labelKey}
                >
                  {tr(group.labelKey)}
                  <svg className="w-3.5 h-3.5 opacity-60" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
                  </svg>
                </button>

                {openGroup === group.labelKey && (
                  <div className="absolute left-0 mt-1 w-72 rounded-xl glass border border-white/10 shadow-2xl p-2 z-50">
                    {group.items.map((item) => (
                      <Link
                        key={item.to}
                        to={item.to}
                        onClick={closeAll}
                        className="flex items-start gap-3 px-3 py-2.5 rounded-lg hover:bg-white/5 transition group"
                      >
                        <div className="flex-1 min-w-0">
                          <div className="flex items-center gap-2">
                            <span className="text-sm font-medium text-dark-100 group-hover:text-white">
                              {tr(item.labelKey)}
                            </span>
                            {item.isNew && (
                              <span className="px-1.5 py-0.5 text-[10px] font-semibold rounded bg-linear-brand/20 text-linear-hover border border-linear-brand/30">
                                NEW
                              </span>
                            )}
                          </div>
                          {item.descKey && (
                            <p className="text-xs text-dark-400 mt-0.5 truncate">{tr(item.descKey)}</p>
                          )}
                        </div>
                      </Link>
                    ))}
                  </div>
                )}
              </div>
            ))}

            {/* Language Toggle */}
            <button
              onClick={toggleLanguage}
              className="ml-2 px-2 py-1 text-sm font-medium border border-dark-600 rounded hover:border-primary-400 hover:text-primary-400 transition"
              title={language === 'zh' ? 'Switch to English' : '切换到中文'}
            >
              {language === 'zh' ? 'EN' : '中'}
            </button>

            {/* Theme Toggle */}
            <button
              onClick={toggleTheme}
              className="p-2 rounded hover:bg-dark-700 transition text-lg leading-none"
              title={isDark ? 'Switch to light mode' : 'Switch to dark mode'}
            >
              {isDark ? '☀️' : '🌙'}
            </button>

            {isAuthenticated ? (
              <div className="relative">
                <button
                  onClick={() => setIsUserMenuOpen(!isUserMenuOpen)}
                  className="flex items-center space-x-2 hover:text-primary-400 transition"
                >
                  <div className="w-8 h-8 rounded-full bg-gradient-to-r from-blue-500 to-purple-500 flex items-center justify-center text-white font-semibold">
                    {user?.email?.charAt(0).toUpperCase()}
                  </div>
                  <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
                  </svg>
                </button>

                {isUserMenuOpen && (
                  <div className="absolute right-0 mt-2 w-48 bg-white dark:bg-dark-800 rounded-lg shadow-lg py-2 border border-gray-200 dark:border-dark-600">
                    <Link
                      to="/control"
                      className="block px-4 py-2 text-gray-800 dark:text-dark-100 hover:bg-gray-100 dark:hover:bg-dark-700"
                      onClick={() => setIsUserMenuOpen(false)}
                    >
                      {tr('control')}
                    </Link>
                    <Link
                      to="/dashboard"
                      className="block px-4 py-2 text-gray-800 dark:text-dark-100 hover:bg-gray-100 dark:hover:bg-dark-700"
                      onClick={() => setIsUserMenuOpen(false)}
                    >
                      {nav.console ?? 'Console'}
                    </Link>
                    <Link
                      to="/billing"
                      className="block px-4 py-2 text-gray-800 dark:text-dark-100 hover:bg-gray-100 dark:hover:bg-dark-700"
                      onClick={() => setIsUserMenuOpen(false)}
                    >
                      {nav.billing ?? 'Billing'}
                    </Link>
                    <Link
                      to="/profile"
                      className="block px-4 py-2 text-gray-800 dark:text-dark-100 hover:bg-gray-100 dark:hover:bg-dark-700"
                      onClick={() => setIsUserMenuOpen(false)}
                    >
                      {nav.profile ?? 'Profile'}
                    </Link>
                    <button
                      onClick={handleLogout}
                      className="block w-full text-left px-4 py-2 text-gray-800 dark:text-dark-100 hover:bg-gray-100 dark:hover:bg-dark-700"
                    >
                      {nav.logout ?? 'Logout'}
                    </button>
                  </div>
                )}
              </div>
            ) : (
              <Link
                to="/login"
                className="px-5 py-2 gradient-primary rounded-lg hover:opacity-90 transition text-white text-sm font-medium"
              >
                {nav.login ?? 'Login'}
              </Link>
            )}
          </div>

          {/* Mobile Menu Button */}
          <div className="md:hidden flex items-center space-x-2">
            <button
              onClick={toggleLanguage}
              className="px-2 py-1 text-sm font-medium border border-dark-600 rounded hover:border-primary-400 transition"
            >
              {language === 'zh' ? 'EN' : '中'}
            </button>
            <button
              onClick={toggleTheme}
              className="p-1.5 rounded hover:bg-dark-700 transition text-lg leading-none"
            >
              {isDark ? '☀️' : '🌙'}
            </button>
            <button onClick={() => setIsMenuOpen(!isMenuOpen)} aria-label="menu">
              <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                {isMenuOpen ? (
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                ) : (
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 6h16M4 12h16M4 18h16" />
                )}
              </svg>
            </button>
          </div>
        </div>

        {/* Mobile Menu — accordion groups */}
        {isMenuOpen && (
          <div className="md:hidden mt-4 pb-4 space-y-1 max-h-[70vh] overflow-y-auto">
            {NAV_GROUPS.map((group) => (
              <div key={group.labelKey} className="border-b border-white/5">
                <button
                  type="button"
                  className="flex items-center justify-between w-full py-3 text-sm font-semibold text-dark-100"
                  onClick={() =>
                    setMobileGroup((g) => (g === group.labelKey ? null : group.labelKey))
                  }
                >
                  {tr(group.labelKey)}
                  <svg
                    className={`w-4 h-4 transition-transform ${mobileGroup === group.labelKey ? 'rotate-180' : ''}`}
                    fill="none" stroke="currentColor" viewBox="0 0 24 24"
                  >
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
                  </svg>
                </button>
                {mobileGroup === group.labelKey && (
                  <div className="pb-2 pl-3 space-y-1">
                    {group.items.map((item) => (
                      <Link
                        key={item.to}
                        to={item.to}
                        onClick={closeAll}
                        className="flex items-center gap-2 py-2 text-sm text-dark-300 hover:text-white transition"
                      >
                        {tr(item.labelKey)}
                        {item.isNew && (
                          <span className="px-1.5 py-0.5 text-[10px] font-semibold rounded bg-linear-brand/20 text-linear-hover">
                            NEW
                          </span>
                        )}
                      </Link>
                    ))}
                  </div>
                )}
              </div>
            ))}

            <div className="pt-3">
              {isAuthenticated ? (
                <>
                  <Link to="/control" onClick={closeAll} className="block py-2 text-sm hover:text-primary-400">
                    {tr('control')}
                  </Link>
                  <Link to="/profile" onClick={closeAll} className="block py-2 text-sm hover:text-primary-400">
                    {nav.profile ?? 'Profile'}
                  </Link>
                  <button onClick={handleLogout} className="block w-full text-left py-2 text-sm hover:text-primary-400">
                    {nav.logout ?? 'Logout'}
                  </button>
                </>
              ) : (
                <Link
                  to="/login"
                  onClick={closeAll}
                  className="block w-full px-6 py-2 gradient-primary rounded-lg hover:opacity-90 transition text-center text-white"
                >
                  {nav.login ?? 'Login'}
                </Link>
              )}
            </div>
          </div>
        )}
      </nav>
    </header>
  )
}
