import { useLanguage } from '../../context/LanguageContext'

interface PageHeaderProps {
  titleKey: string
  subtitleKey?: string
}

export default function PageHeader({ titleKey, subtitleKey }: PageHeaderProps) {
  const { t } = useLanguage()
  const pages = (t as any).pages || {}
  const title = pages[titleKey] || titleKey
  const subtitle = subtitleKey ? (pages[subtitleKey] || subtitleKey) : undefined

  return (
    <div className="text-center py-12">
      <h1 className="text-4xl font-bold gradient-text mb-4">{title}</h1>
      {subtitle && (
        <p className="text-lg text-gray-600 dark:text-gray-400 max-w-2xl mx-auto">{subtitle}</p>
      )}
    </div>
  )
}
