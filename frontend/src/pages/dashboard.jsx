import { useQuery } from "@tanstack/react-query";
import { keyInfo, balances, openOrders } from "../lib/api";
import { useState } from "react";

export default function Dashboard() {
  const [accountType, setAcc] = useState("UNIFIED");
  const [symbol, setSym] = useState("BTCUSDT");
  const [category, setCat] = useState("linear");

  const qKeyInfo = useQuery({ queryKey: ["keyinfo"], queryFn: keyInfo });
  const qBalance = useQuery({
    queryKey: ["balances", accountType],
    queryFn: () => balances(accountType),
  });
  const qOrders = useQuery({
    queryKey: ["orders", category, symbol],
    queryFn: () => openOrders(symbol, category),
  });

  return (
    <div
      style={{ maxWidth: 900, margin: "20px auto", fontFamily: "system-ui" }}
    >
      <h2>Dashboard</h2>

      <div style={{ display: "flex", gap: 16 }}>
        <div>
          <label>AccountType:</label>
          <select value={accountType} onChange={(e) => setAcc(e.target.value)}>
            <option>UNIFIED</option>
            <option>SPOT</option>
            <option>CONTRACT</option>
          </select>
        </div>
        <div>
          <label>Symbol:</label>
          <input value={symbol} onChange={(e) => setSym(e.target.value)} />
        </div>
        <div>
          <label>Category:</label>
          <select value={category} onChange={(e) => setCat(e.target.value)}>
            <option>linear</option>
            <option>spot</option>
            <option>inverse</option>
          </select>
        </div>
      </div>

      <section>
        <h3>API Key Info</h3>
        <pre>{JSON.stringify(qKeyInfo.data, null, 2)}</pre>
      </section>

      <section>
        <h3>Balances ({accountType})</h3>
        <pre>{JSON.stringify(qBalance.data, null, 2)}</pre>
      </section>

      <section>
        <h3>
          Open Orders ({category} / {symbol})
        </h3>
        <pre>{JSON.stringify(qOrders.data, null, 2)}</pre>
      </section>
    </div>
  );
}
