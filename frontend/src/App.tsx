import { Routes, Route, Navigate } from 'react-router-dom'
import { useAuth } from '@/hooks/useAuth'
import LoginPage from '@/pages/LoginPage'
import DashboardLayout from '@/pages/DashboardLayout'
import TeacherDashboard from '@/pages/TeacherDashboard'
import GeneratePaper from '@/pages/GeneratePaper'
import MyPapers from '@/pages/MyPapers'
import PaperReview from '@/pages/PaperReview'
import QuestionBank from '@/pages/QuestionBank'
import InstituteAdmin from '@/pages/InstituteAdmin'

function RequireAuth({ children }: { children: React.ReactNode }) {
  const { user } = useAuth()
  if (!user) return <Navigate to="/login" replace />
  return <>{children}</>
}

export default function App() {
  return (
    <Routes>
      <Route path="/login" element={<LoginPage />} />
      <Route
        path="/"
        element={
          <RequireAuth>
            <DashboardLayout />
          </RequireAuth>
        }
      >
        <Route index element={<TeacherDashboard />} />
        <Route path="generate" element={<GeneratePaper />} />
        <Route path="papers" element={<MyPapers />} />
        <Route path="papers/:paperId/review" element={<PaperReview />} />
        <Route path="bank" element={<QuestionBank />} />
        <Route path="admin" element={<InstituteAdmin />} />
      </Route>
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  )
}
