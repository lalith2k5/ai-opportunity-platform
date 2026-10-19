
import { Routes, Route, Navigate } from 'react-router-dom';
import { Loader2 } from 'lucide-react';
import Layout from './components/Layout';
import ProtectedRoute from './components/ProtectedRoute';
import Dashboard from './pages/Dashboard';
import Search from './pages/Search';
import Chat from './pages/Chat';
import Login from './pages/Login';
import Register from './pages/Register';
import OpportunityDetail from './pages/OpportunityDetail';
import Admin from './pages/Admin';
import ForgotPassword from './pages/ForgotPassword';
import ResetPassword from './pages/ResetPassword';
import Profile from './pages/Profile';
import Opportunities from './pages/Opportunities';
import Recommendations from './pages/Recommendations';
import KnowledgeGraph from './pages/KnowledgeGraph';
import EntranceDashboard from './pages/EntranceDashboard';
import Ideas from './pages/Ideas';
import IdeaDetail from './pages/IdeaDetail';
import Technologies from './pages/Technologies';
import TechnologyDetail from './pages/TechnologyDetail';
import Research from './pages/Research';
import ResearchDetail from './pages/ResearchDetail';
import RD from './pages/RD';
import RDProblemDetail from './pages/RDProblemDetail';
import { useAuth } from './context/AuthContext';

const wrap = (el: React.ReactNode) => (
  <ProtectedRoute><Layout>{el}</Layout></ProtectedRoute>
);

function LandingOrDashboard() {
  const { user, isLoading } = useAuth();
  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-screen bg-canvas">
        <Loader2 className="animate-spin text-accent" size={32} />
      </div>
    );
  }
  if (user) return <Navigate to="/dashboard" replace />;
  return <EntranceDashboard />;
}

export default function App() {
  return (
    <Routes>
      <Route path="/" element={<LandingOrDashboard />} />
      <Route path="/entrance" element={<Navigate to="/" replace />} />
      <Route path="/login" element={<Login />} />
      <Route path="/register" element={<Register />} />
      <Route path="/forgot-password" element={<ForgotPassword />} />
      <Route path="/reset-password" element={<ResetPassword />} />

      <Route path="/dashboard" element={wrap(<Dashboard />)} />
      <Route path="/search" element={wrap(<Search />)} />
      <Route path="/chat" element={wrap(<Chat />)} />
      <Route path="/reports" element={<Navigate to="/dashboard" replace />} />
      <Route path="/profile" element={wrap(<Profile />)} />
      <Route path="/admin" element={wrap(<Admin />)} />
      <Route path="/opportunities" element={wrap(<Opportunities />)} />
      <Route path="/recommendations" element={wrap(<Recommendations />)} />
      <Route path="/knowledge-graph" element={wrap(<KnowledgeGraph />)} />

      <Route path="/ideas" element={wrap(<Ideas />)} />
      <Route path="/ideas/:id" element={wrap(<IdeaDetail />)} />
      <Route path="/technologies" element={wrap(<Technologies />)} />
      <Route path="/technologies/:name" element={wrap(<TechnologyDetail />)} />
      <Route path="/research" element={wrap(<Research />)} />
      <Route path="/research/:arxiv_id" element={wrap(<ResearchDetail />)} />
      <Route path="/rd" element={wrap(<RD />)} />
      <Route path="/rd/:id" element={wrap(<RDProblemDetail />)} />
      <Route path="/opportunities/:id" element={wrap(<OpportunityDetail />)} />

      <Route path="/problems" element={<Navigate to="/ideas" replace />} />
      <Route path="/problem-profiles" element={<Navigate to="/rd" replace />} />
      <Route path="/workflows/student" element={<Navigate to="/opportunities" replace />} />
      <Route path="/workflows/researcher" element={<Navigate to="/research" replace />} />
      <Route path="/workflows/rd" element={<Navigate to="/rd" replace />} />
    </Routes>
  );
}
