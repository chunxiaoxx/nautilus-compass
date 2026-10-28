#!/usr/bin/env python3
"""Fix App.tsx to add missing routes"""

with open("phase3/frontend/src/App.tsx", "r") as f:
    content = f.read()

# 1. Add lazy imports after RegisterPage
old_reg = """const RegisterPage = lazy(() => import('./pages/RegisterPage').catch(err => {
  handleChunkError(err)
  throw err
}))"""

addition = """

const AuthCallbackPage = lazy(() => import('./pages/AuthCallbackPage').catch(err => {
  handleChunkError(err)
  throw err
}))

const AgentSurvivalPage = lazy(() => import('./pages/AgentSurvivalPage').catch(err => {
  handleChunkError(err)
  throw err
}))

const LeaderboardPage = lazy(() => import('./pages/LeaderboardPage').catch(err => {
  handleChunkError(err)
  throw err
}))

const BootstrapPage = lazy(() => import('./pages/BootstrapPage').catch(err => {
  handleChunkError(err)
  throw err
}))"""

content = content.replace(old_reg, old_reg + addition)

# 2. Add WalletAuth import
content = content.replace(
    "import { ProtectedRoute } from './components/ProtectedRoute'",
    "import { ProtectedRoute } from './components/ProtectedRoute'\nimport { WalletAuth } from './components/WalletAuth'"
)

# 3. Add auth callback and wallet-auth routes
content = content.replace(
    '          <Route path="/register" element={<RegisterPage />} />\n          <Route path="/" element={<Layout />}>',
    '          <Route path="/register" element={<RegisterPage />} />\n          <Route path="/wallet-auth" element={<WalletAuth />} />\n          <Route path="/auth/callback" element={<AuthCallbackPage />} />\n          <Route path="/" element={<Layout />}>'
)

# 4. Add inner routes (survival, leaderboard, bootstrap)
content = content.replace(
    '            <Route path="agents/:id" element={<AgentDetailPage />} />\n            <Route path="dashboard"',
    '            <Route path="agents/:id" element={<AgentDetailPage />} />\n            <Route path="agents/:id/survival" element={<AgentSurvivalPage />} />\n            <Route path="leaderboard" element={<LeaderboardPage />} />\n            <Route path="bootstrap" element={<BootstrapPage />} />\n            <Route path="dashboard"'
)

# 5. Wrap dashboard, profile, tasks/create with ProtectedRoute
content = content.replace(
    'element={<DashboardPage />}',
    'element={<ProtectedRoute><DashboardPage /></ProtectedRoute>}'
)
content = content.replace(
    'element={<UserCenterPage />}',
    'element={<ProtectedRoute><UserCenterPage /></ProtectedRoute>}'
)
content = content.replace(
    'element={<CreateTaskPage />}',
    'element={<ProtectedRoute><CreateTaskPage /></ProtectedRoute>}'
)

with open("phase3/frontend/src/App.tsx", "w") as f:
    f.write(content)

print("App.tsx updated with all routes!")
