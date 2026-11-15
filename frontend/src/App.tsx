import { BrowserRouter, Route, Routes } from "react-router-dom";
import { AppLayout } from "./components/layout/AppLayout";
import { RequireAdmin, RequireAuth } from "./components/layout/RouteGuards";
import { Spinner } from "./components/ui/PageLoader";
import { AuthProvider, useAuth } from "./context/AuthContext";
import { AchievementsPage } from "./pages/AchievementsPage";
import { AdminChallengeNewPage } from "./pages/admin/AdminChallengeNewPage";
import { AdminChallengesPage } from "./pages/admin/AdminChallengesPage";
import { AdminOverviewPage } from "./pages/admin/AdminOverviewPage";
import { ForgotPage } from "./pages/auth/ForgotPage";
import { LoginPage } from "./pages/auth/LoginPage";
import { RegisterPage } from "./pages/auth/RegisterPage";
import { ResetPage } from "./pages/auth/ResetPage";
import { ChallengePlayPage } from "./pages/ChallengePlayPage";
import { ChallengesPage } from "./pages/ChallengesPage";
import { DashboardPage } from "./pages/DashboardPage";
import { DocsPage } from "./pages/DocsPage";
import { LandingPage } from "./pages/Landing";
import { LeaderboardPage } from "./pages/LeaderboardPage";
import { NotFoundPage } from "./pages/NotFoundPage";
import { PathsPage } from "./pages/PathsPage";
import { ProfilePage } from "./pages/ProfilePage";

/** Waits for the first /api/session answer so signed-in users never see a login flash. */
function AppRoutes() {
  const { status } = useAuth();
  if (status === "loading") {
    return (
      <div className="flex min-h-screen items-center justify-center bg-gray-950">
        <Spinner />
      </div>
    );
  }

  return (
    <Routes>
      <Route path="/" element={<LandingPage />} />
      <Route path="/login" element={<LoginPage />} />
      <Route path="/register" element={<RegisterPage />} />
      <Route path="/forgot" element={<ForgotPage />} />
      <Route path="/reset/:token" element={<ResetPage />} />

      <Route element={<AppLayout />}>
        <Route path="/docs" element={<DocsPage />} />

        <Route element={<RequireAuth />}>
          <Route path="/dashboard" element={<DashboardPage />} />
          <Route path="/challenges" element={<ChallengesPage />} />
          <Route path="/challenges/:slug" element={<ChallengePlayPage />} />
          <Route path="/leaderboard" element={<LeaderboardPage />} />
          <Route path="/profile" element={<ProfilePage />} />
          <Route path="/paths" element={<PathsPage />} />
          <Route path="/achievements" element={<AchievementsPage />} />

          <Route element={<RequireAdmin />}>
            <Route path="/admin" element={<AdminOverviewPage />} />
            <Route path="/admin/challenges" element={<AdminChallengesPage />} />
            <Route path="/admin/challenges/new" element={<AdminChallengeNewPage />} />
          </Route>
        </Route>

        <Route path="*" element={<NotFoundPage />} />
      </Route>
    </Routes>
  );
}

export function App() {
  return (
    <BrowserRouter>
      <AuthProvider>
        <AppRoutes />
      </AuthProvider>
    </BrowserRouter>
  );
}
