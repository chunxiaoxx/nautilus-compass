import { lazy, Suspense } from 'react'
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom'
import { AuthProvider } from './context/AuthContext'
import { LanguageProvider } from './context/LanguageContext'
import { ThemeProvider } from './context/ThemeContext'
import Layout from './components/layout/Layout'
import ProtectedRoute from './components/auth/ProtectedRoute'

const Home = lazy(() => import('./pages/Home'))
const Login = lazy(() => import('./pages/Login'))
const Register = lazy(() => import('./pages/Register'))
const DashboardPage = lazy(() => import('./pages/DashboardPage'))
const ControlCenterPage = lazy(() => import('./pages/ControlCenterPage'))
const UserCenterPage = lazy(() => import('./pages/UserCenterPage'))
const AgentRegisterPageV2 = lazy(() => import('./pages/AgentRegisterPageV2'))
const AgentLoginPageV2 = lazy(() => import('./pages/AgentLoginPageV2'))
const CreateWalletPage = lazy(() => import('./pages/CreateWalletPage'))
const FeaturesPage = lazy(() => import('./pages/FeaturesPage'))
const PricingPage = lazy(() => import('./pages/PricingPage'))
const DocumentationPage = lazy(() => import('./pages/DocumentationPage'))
const APIReferencePage = lazy(() => import('./pages/APIReferencePage'))
const AboutPage = lazy(() => import('./pages/AboutPage'))
const BlogPage = lazy(() => import('./pages/BlogPage'))
const RoadmapPage = lazy(() => import('./pages/RoadmapPage'))
const CareersPage = lazy(() => import('./pages/CareersPage'))
const ContactPage = lazy(() => import('./pages/ContactPage'))
const TaskSubmit = lazy(() => import('./pages/TaskSubmit'))
const TaskDetail = lazy(() => import('./pages/TaskDetail'))
const OAuthCallback = lazy(() => import('./pages/OAuthCallback'))
const AcademicTaskPage = lazy(() => import('./pages/AcademicTaskPage'))
const BenchPage = lazy(() => import('./pages/BenchPage'))
const AgentsPage = lazy(() => import('./pages/AgentsPage'))
const AgentDetailPage = lazy(() => import('./pages/AgentDetailPage'))
const LeaderboardPage = lazy(() => import('./pages/LeaderboardPage'))
const TasksPage = lazy(() => import('./pages/TasksPage'))
const TaskDetailPage = lazy(() => import('./pages/TaskDetailPage'))
const CreateTaskPage = lazy(() => import('./pages/CreateTaskPage'))
const AgentSurvivalPage = lazy(() => import('./pages/AgentSurvivalPage'))
const HowItWorksPage = lazy(() => import('./pages/HowItWorksPage'))
const MarketplacePage = lazy(() => import('./pages/MarketplacePage'))
const PlatformDashboardPage = lazy(() => import('./pages/PlatformDashboardPage'))
const LiveDashboardPage = lazy(() => import('./pages/PlatformDashboardPage'))
const ProposalsPage = lazy(() => import('./pages/ProposalsPage'))
const FeedPage = lazy(() => import('./pages/FeedPage'))
const SkillsPage = lazy(() => import('./pages/SkillsPage'))
const CollaboratePage = lazy(() => import('./pages/CollaboratePage'))
const AgentOnboardPage = lazy(() => import('./pages/AgentOnboardPage'))
const BillingPage = lazy(() => import('./pages/BillingPage'))
const PartnerPage = lazy(() => import('./pages/PartnerPage'))
const FDEPhase3GuidePage = lazy(() => import('./pages/FDEPhase3GuidePage'))

function App() {
  return (
    <ThemeProvider>
      <LanguageProvider>
        <AuthProvider>
          <Router>
            <Layout>
              <Suspense fallback={<div className="flex items-center justify-center min-h-screen">Loading...</div>}>
                <Routes>
                  <Route path="/" element={<Home />} />
                  <Route path="/marketplace" element={<MarketplacePage />} />
                  <Route path="/login" element={<Login />} />
                  <Route path="/register" element={<Register />} />
                  <Route path="/agent/register" element={<AgentRegisterPageV2 />} />
                  <Route path="/agent/login" element={<AgentLoginPageV2 />} />
                  <Route path="/create-wallet" element={<CreateWalletPage />} />
                  <Route path="/features" element={<FeaturesPage />} />
                  <Route path="/pricing" element={<PricingPage />} />
                  <Route path="/docs" element={<DocumentationPage />} />
                  <Route path="/api-docs" element={<APIReferencePage />} />
                  <Route path="/docs/fde" element={<Navigate to="/docs/fde-phase3" replace />} />
                  <Route path="/docs/fde-phase3" element={<FDEPhase3GuidePage />} />
                  <Route path="/fde-phase3" element={<Navigate to="/docs/fde-phase3" replace />} />
                  <Route path="/about" element={<AboutPage />} />
                  <Route path="/blog" element={<BlogPage />} />
                  <Route path="/roadmap" element={<RoadmapPage />} />
                  <Route path="/careers" element={<CareersPage />} />
                  <Route path="/contact" element={<ContactPage />} />
                  <Route path="/marketplace/submit" element={<TaskSubmit />} />
                  <Route path="/marketplace/task/:taskId" element={<TaskDetail />} />
                  <Route path="/auth/callback" element={<OAuthCallback />} />
                  <Route path="/academic" element={<AcademicTaskPage />} />
                  <Route path="/agents" element={<AgentsPage />} />
                  <Route path="/bench" element={<BenchPage />} />
                  <Route path="/agents/:id" element={<AgentDetailPage />} />
                  <Route path="/agents/:id/survival" element={<AgentSurvivalPage />} />
                  <Route path="/leaderboard" element={<LeaderboardPage />} />
                  <Route path="/tasks" element={<TasksPage />} />
                  <Route path="/tasks/:id" element={<TaskDetailPage />} />
                  <Route path="/tasks/create" element={<ProtectedRoute><CreateTaskPage /></ProtectedRoute>} />
                  <Route path="/rehoboam" element={<DashboardPage />} />
                  <Route path="/profile" element={<ProtectedRoute><UserCenterPage /></ProtectedRoute>} />
                  <Route path="/dashboard" element={<ProtectedRoute><DashboardPage /></ProtectedRoute>} />
                  <Route path="/control" element={<ProtectedRoute><ControlCenterPage /></ProtectedRoute>} />
                  <Route path="/how-it-works" element={<HowItWorksPage />} />
                  <Route path="/platform" element={<PlatformDashboardPage />} />
                  <Route path="/live" element={<LiveDashboardPage />} />
                  <Route path="/platform/proposals" element={<ProposalsPage />} />
                  <Route path="/feed" element={<FeedPage />} />
                  <Route path="/feed/agent/:agent_id" element={<FeedPage />} />
                  <Route path="/skills" element={<SkillsPage />} />
                  <Route path="/tools" element={<SkillsPage />} />
                  <Route path="/collaborate" element={<CollaboratePage />} />
                  <Route path="/onboard" element={<AgentOnboardPage />} />
                  <Route path="/partners" element={<PartnerPage />} />
                  <Route path="/billing" element={<ProtectedRoute><BillingPage /></ProtectedRoute>} />
                </Routes>
              </Suspense>
            </Layout>
          </Router>
        </AuthProvider>
      </LanguageProvider>
    </ThemeProvider>
  )
}

export default App
