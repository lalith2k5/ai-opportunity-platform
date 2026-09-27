import { Routes, Route } from 'react-router-dom';
import Layout from './components/Layout';
import ProtectedRoute from './components/ProtectedRoute';
import Dashboard from './pages/Dashboard';
import Search from './pages/Search';
import Chat from './pages/Chat';
import Reports from './pages/Reports';
import Login from './pages/Login';
import Register from './pages/Register';
import OpportunityDetail from './pages/OpportunityDetail';
import Admin from './pages/Admin';
import ForgotPassword from './pages/ForgotPassword';
import ResetPassword from './pages/ResetPassword';
import Profile from './pages/Profile';
import Problems from './pages/Problems';
import Opportunities from './pages/Opportunities';
import Recommendations from './pages/Recommendations';
import Analytics from './pages/Analytics';
import KnowledgeGraph from './pages/KnowledgeGraph';

const wrap = (el: React.ReactNode) => (
  <ProtectedRoute><Layout>{el}</Layout></ProtectedRoute>
);

export default function App() {
  return (
    <Routes>
      <Route path="/login" element={<Login />} />
      <Route path="/register" element={<Register />} />
      <Route path="/forgot-password" element={<ForgotPassword />} />
      <Route path="/reset-password" element={<ResetPassword />} />
      <Route path="/" element={wrap(<Dashboard />)} />
      <Route path="/search" element={wrap(<Search />)} />
      <Route path="/chat" element={wrap(<Chat />)} />
      <Route path="/reports" element={wrap(<Reports />)} />
      <Route path="/profile" element={wrap(<Profile />)} />
      <Route path="/admin" element={wrap(<Admin />)} />
      <Route path="/problems" element={wrap(<Problems />)} />
      <Route path="/opportunities" element={wrap(<Opportunities />)} />
      <Route path="/recommendations" element={wrap(<Recommendations />)} />
      <Route path="/analytics" element={wrap(<Analytics />)} />
      <Route path="/knowledge-graph" element={wrap(<KnowledgeGraph />)} />
      <Route path="/opportunities/:id" element={wrap(<OpportunityDetail />)} />
    </Routes>
  );
}
