import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom";
import useAuthStore from "./stores/authStore";

import AuthPage         from "./pages/AuthPage";
import Dashboard        from "./pages/Dashboard";
import UploadPage       from "./pages/UploadPage";
import AnalyzingPage    from "./pages/AnalyzingPage";
import ResultPage       from "./pages/ResultPage";
import ResultDetailPage from "./pages/ResultDetailPage";
import HistoryPage      from "./pages/HistoryPage";
import MyPage           from "./pages/MyPage";

const PrivateRoute = ({ children }) => {
  const { isAuthenticated } = useAuthStore();
  return isAuthenticated ? children : <Navigate to="/" replace />;
};

const PublicRoute = ({ children }) => {
  const { isAuthenticated } = useAuthStore();
  return !isAuthenticated ? children : <Navigate to="/dashboard" replace />;
};

export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<PublicRoute><AuthPage /></PublicRoute>} />
        <Route path="/dashboard" element={<PrivateRoute><Dashboard /></PrivateRoute>} />
        <Route path="/upload" element={<PrivateRoute><UploadPage /></PrivateRoute>} />
        <Route path="/analyzing/:jobId" element={<PrivateRoute><AnalyzingPage /></PrivateRoute>} />
        <Route path="/result/:jobId" element={<PrivateRoute><ResultPage /></PrivateRoute>} />
        <Route path="/result/:jobId/detail" element={<PrivateRoute><ResultDetailPage /></PrivateRoute>} />
        <Route path="/history" element={<PrivateRoute><HistoryPage /></PrivateRoute>} />
        <Route path="/mypage" element={<PrivateRoute><MyPage /></PrivateRoute>} />
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </BrowserRouter>
  );
}