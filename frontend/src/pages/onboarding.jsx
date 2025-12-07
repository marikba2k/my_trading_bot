import { useEffect, useState } from "react";
import { onboardingState, testCreds, saveCreds } from "../lib/api";

export default function Onboarding() {
  const [hasCreds, setHasCreds] = useState(null);
  const [apiKey, setKey] = useState("");
  const [apiSecret, setSec] = useState("");
  const [msg, setMsg] = useState("");

  useEffect(() => {
    onboardingState().then((s) => setHasCreds(!!s.has_testnet_credentials));
  }, []);

  async function onTest(e) {
    e.preventDefault();
    setMsg("Testing...");
    try {
      const res = await testCreds(apiKey, apiSecret, true);
      setMsg(res.ok ? "OK! Credentials valid." : `Error: ${res.error}`);
    } catch (e) {
      setMsg("Error testing credentials.");
    }
  }

  async function onSave(e) {
    e.preventDefault();
    setMsg("Saving...");
    try {
      const res = await saveCreds(apiKey, apiSecret, true);
      if (res.ok) {
        setMsg("Saved!");
        setHasCreds(true);
      } else setMsg("Save failed.");
    } catch (e) {
      setMsg("Error saving credentials.");
    }
  }

  if (hasCreds === null) return <p>Loading...</p>;
  if (hasCreds)
    return (
      <div style={{ maxWidth: 600, margin: "40px auto" }}>
        <h2>Onboarding</h2>
        <p>
          Testnet credentials are already saved. Continue to{" "}
          <a href="/dashboard">Dashboard</a>.
        </p>
      </div>
    );

  return (
    <div style={{ maxWidth: 600, margin: "40px auto" }}>
      <h2>Onboarding – Save Testnet Credentials</h2>
      <form>
        <label>API Key</label>
        <input
          value={apiKey}
          onChange={(e) => setKey(e.target.value)}
          style={{ width: "100%", marginBottom: 8 }}
        />
        <label>API Secret</label>
        <input
          value={apiSecret}
          onChange={(e) => setSec(e.target.value)}
          style={{ width: "100%", marginBottom: 8 }}
        />
        <button onClick={onTest}>Test</button>
        <button onClick={onSave} style={{ marginLeft: 8 }}>
          Save
        </button>
      </form>
      {msg && <p style={{ marginTop: 8 }}>{msg}</p>}
    </div>
  );
}
