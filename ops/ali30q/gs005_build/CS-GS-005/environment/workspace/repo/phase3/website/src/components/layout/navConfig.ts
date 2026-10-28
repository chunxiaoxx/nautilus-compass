/**
 * 统一导航 IA（W-2 现代化）。
 *
 * 把原平铺导航重组成 4 组下拉,把近 2 月的平台功能(指挥中心 / 实况 / 提案治理)
 * 收纳进「平台」组,解决「整站混乱 · 2 月功能没体现」。
 *
 * 纯数据 —— Header 用 i18n `t.nav.*` 解析 labelKey。便于单测(不耦合 i18n 加载)。
 */

export interface NavItem {
  /** i18n key under `nav.*` */
  labelKey: string
  to: string
  /** optional i18n key for a one-line description (desktop dropdown) */
  descKey?: string
  /** surfaced as "new" badge in the menu */
  isNew?: boolean
}

export interface NavGroup {
  labelKey: string
  items: NavItem[]
}

export const NAV_GROUPS: NavGroup[] = [
  {
    labelKey: 'groupPlatform',
    items: [
      { to: '/control', labelKey: 'control', descKey: 'control_desc', isNew: true },
      { to: '/live', labelKey: 'live', descKey: 'live_desc', isNew: true },
      { to: '/feed', labelKey: 'feed', descKey: 'feed_desc' },
      { to: '/platform/proposals', labelKey: 'proposals', descKey: 'proposals_desc' },
    ],
  },
  {
    labelKey: 'groupAgents',
    items: [
      { to: '/agents', labelKey: 'agents', descKey: 'agents_desc' },
      { to: '/leaderboard', labelKey: 'leaderboard', descKey: 'leaderboard_desc' },
      { to: '/onboard', labelKey: 'onboard', descKey: 'onboard_desc' },
    ],
  },
  {
    labelKey: 'groupTasks',
    items: [
      { to: '/marketplace', labelKey: 'marketplace', descKey: 'marketplace_desc' },
      { to: '/tasks', labelKey: 'tasks', descKey: 'tasks_desc' },
      { to: '/academic', labelKey: 'academic', descKey: 'academic_desc' },
      { to: '/collaborate', labelKey: 'collaborate', descKey: 'collaborate_desc' },
    ],
  },
  {
    labelKey: 'groupResources',
    items: [
      { to: '/skills', labelKey: 'skills', descKey: 'skills_desc' },
      { to: '/docs', labelKey: 'docs', descKey: 'docs_desc' },
      { to: '/docs/fde-phase3', labelKey: 'docsFdePhase3', descKey: 'docsFdePhase3_desc' },
      { to: '/api-docs', labelKey: 'apiDocs', descKey: 'apiDocs_desc' },
      { to: '/how-it-works', labelKey: 'howItWorks', descKey: 'howItWorks_desc' },
    ],
  },
]

/** All route paths reachable from the nav (used by tests + sanity checks). */
export const NAV_PATHS: string[] = NAV_GROUPS.flatMap((g) => g.items.map((i) => i.to))
