import { Navigate, Route, Routes } from "react-router-dom";
import AppLayout from "./layouts/AppLayout";
import AuthLayout from "./layouts/AuthLayout";
import { useAuth } from "./hooks/useAuth";
import LoadingSpinner from "./components/LoadingSpinner";
import ErrorBoundary from "./components/ErrorBoundary";
import Login from "./pages/Login";
import Register from "./pages/Register";
import Dashboard from "./pages/Dashboard";
import JobList from "./pages/JobList";
import JobCreate from "./pages/JobCreate";
import JobDetail from "./pages/JobDetail";
import Ranking from "./pages/Ranking";
import CandidateDetail from "./pages/CandidateDetail";
import Search from "./pages/Search";
import NotFound from "./pages/NotFound";
import OpenAIKeyPrompt from "./components/OpenAIKeyPrompt";
import Legal from "./pages/Legal";
import DataDeletion from "./pages/DataDeletion";

function RequireAuth({ children }: { children: JSX.Element }) {
  const { user, loading } = useAuth();
  if (loading) return <LoadingSpinner />;
  return user ? children : <Navigate to="/login" replace />;
}

export default function App() {
  return (
    <ErrorBoundary>
      <Routes>
      <Route element={<AuthLayout />}>
        <Route path="/login" element={<Login />} />
        <Route path="/register" element={<Register />} />
        <Route path="/privacy" element={<Legal />} />
        <Route path="/terms" element={<Legal />} />
        <Route path="/cookies" element={<Legal />} />
      </Route>

      <Route
        element={
          <RequireAuth>
            <><AppLayout /><OpenAIKeyPrompt /></>
          </RequireAuth>
        }
      >
        <Route path="/" element={<Dashboard />} />
        <Route path="/jobs" element={<JobList />} />
        <Route path="/jobs/new" element={<JobCreate />} />
        <Route path="/jobs/:jobId" element={<JobDetail />} />
        <Route path="/jobs/:jobId/ranking" element={<Ranking />} />
        <Route path="/candidates/:candidateId" element={<CandidateDetail />} />
        <Route path="/search" element={<Search />} />
        <Route path="/account/delete" element={<DataDeletion />} />
      </Route>

      <Route path="*" element={<NotFound />} />
      </Routes>
    </ErrorBoundary>
  );
}
