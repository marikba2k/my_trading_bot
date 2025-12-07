import { useState } from "react";
import { login } from "../lib/api";
import { setAccessToken } from "../lib/api";

export default function Login() {
  const [username, setU] = useState("");
  const [password, setP] = useState("");
  const [error, setError] = useState("");

  async function onSubmit(e) {
    e.preventDefault();
    setError("");
    try {
      const data = await login(username, password);
      setAccessToken(data.access);
      window.location.href = "/onboarding";
    } catch (err) {
      setError("Login failed. Check credentials.");
    }
  }

  return (
    <div
      style={{ maxWidth: 360, margin: "80px auto", fontFamily: "system-ui" }}
    >
      <h1>Trade Bot – Login</h1>
      <form onSubmit={onSubmit}>
        <label>Username</label>
        <input
          value={username}
          onChange={(e) => setU(e.target.value)}
          required
          style={{ width: "100%", marginBottom: 8 }}
        />
        <label>Password</label>
        <input
          type="password"
          value={password}
          onChange={(e) => setP(e.target.value)}
          required
          style={{ width: "100%", marginBottom: 8 }}
        />
        <button type="submit">Login</button>
      </form>
      {error && <p style={{ color: "crimson" }}>{error}</p>}
      <p style={{ marginTop: 12 }}>
        No account? Use Postman/PowerShell to POST{" "}
        <code>/api/auth/register</code> (we can add a register form later).
      </p>
    </div>
  );
}
