import { Navigate, Route, Routes } from "react-router-dom";

import Login from "./pages/auth/Login";
import Register from "./pages/auth/Register";
import ForgotPassword from "./pages/auth/ForgotPassword";
import ResetPassword from "./pages/auth/ResetPassword";

import Dashboard from "./pages/dashboard/Dashboard";
import NewAnalysis from "./pages/analysis/NewAnalysis";
import History from "./pages/history/History";
import ComplianceResult from "./pages/analysis/ComplianceResult";

import ProtectedRoute from "./components/auth/ProtectedRoute";

export default function App() {
  return (
    <Routes>
      {/* ================================================== */}
      {/* AUTH */}
      {/* ================================================== */}

      <Route
        path="/login"
        element={<Login />}
      />

      <Route
        path="/register"
        element={<Register />}
      />

      <Route
        path="/forgot-password"
        element={<ForgotPassword />}
      />

      <Route
        path="/reset-password"
        element={<ResetPassword />}
      />

      {/* ================================================== */}
      {/* PROTECTED */}
      {/* ================================================== */}

      <Route element={<ProtectedRoute />}>
        <Route
          path="/dashboard"
          element={<Dashboard />}
        />

        <Route
          path="/analysis/new"
          element={<NewAnalysis />}
        />

        <Route
          path="/history"
          element={<History />}
        />

        <Route
          path="/analysis/:id"
          element={<ComplianceResult />}
        />
      </Route>

      {/* ================================================== */}
      {/* DEFAULT */}
      {/* ================================================== */}

      <Route
        path="/"
        element={
          <Navigate
            to="/login"
            replace
          />
        }
      />

      <Route
        path="*"
        element={
          <Navigate
            to="/login"
            replace
          />
        }
      />
    </Routes>
  );
}