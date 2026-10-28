import { describe, it, expect } from 'vitest'
import { NAV_GROUPS, NAV_PATHS } from '../navConfig'

describe('navConfig (统一 IA · W-2)', () => {
  it('exposes 4 top-level groups', () => {
    expect(NAV_GROUPS).toHaveLength(4)
    const labels = NAV_GROUPS.map((g) => g.labelKey)
    expect(labels).toEqual([
      'groupPlatform',
      'groupAgents',
      'groupTasks',
      'groupResources',
    ])
  })

  it('surfaces the new 指挥中心 (/control) under the Platform group', () => {
    const platform = NAV_GROUPS.find((g) => g.labelKey === 'groupPlatform')
    expect(platform).toBeDefined()
    const control = platform!.items.find((i) => i.to === '/control')
    expect(control).toBeDefined()
    expect(control!.isNew).toBe(true)
  })

  it('surfaces the live system + proposals (2 月功能体现)', () => {
    expect(NAV_PATHS).toContain('/live')
    expect(NAV_PATHS).toContain('/platform/proposals')
  })

  it('every nav item has a labelKey and a route path', () => {
    for (const group of NAV_GROUPS) {
      for (const item of group.items) {
        expect(item.labelKey).toBeTruthy()
        expect(item.to.startsWith('/')).toBe(true)
      }
    }
  })

  it('NAV_PATHS only references routes that exist in App.tsx', () => {
    // routes registered in src/App.tsx (kept in sync — nav must not 404)
    const appRoutes = new Set([
      '/control', '/live', '/feed', '/platform', '/platform/proposals',
      '/agents', '/leaderboard', '/onboard',
      '/marketplace', '/tasks', '/academic', '/collaborate',
      '/skills', '/docs', '/api-docs', '/how-it-works',
    ])
    for (const p of NAV_PATHS) {
      expect(appRoutes.has(p)).toBe(true)
    }
  })
})
