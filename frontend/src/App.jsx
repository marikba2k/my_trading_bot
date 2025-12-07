import { Routes, Route, Navigate, Link } from "react-router-dom";
import Login from "./pages/Login";
import Onboarding from "./pages/Onboarding";
import Dashboard from "./pages/Dashboard";
import Protected from "./components/Protected";

export default function App() {
  return (
    <>
      <nav style={{ padding: 12, borderBottom: "1px solid #ddd" }}>
        <Link to="/dashboard">Dashboard</Link> |{" "}
        <Link to="/onboarding">Onboarding</Link> |{" "}
        <Link to="/login">Login</Link>
      </nav>
      <Routes>
        <Route path="/" element={<Navigate to="/dashboard" />} />
        <Route path="/login" element={<Login />} />
        <Route
          path="/onboarding"
          element={
            <Protected>
              <Onboarding />
            </Protected>
          }
        />
        <Route
          path="/dashboard"
          element={
            <Protected>
              <Dashboard />
            </Protected>
          }
        />
        <Route path="*" element={<p>Not Found</p>} />
      </Routes>
    </>
  );
}
