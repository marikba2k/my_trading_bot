import axios from "axios";

const API = axios.create({
  baseURL: import.meta.env.VITE_API_BASE || "http://127.0.0.1:8000",
});

// --- Simple auth token handling (dev) ---
let accessToken = null;
export function setAccessToken(token) {
  accessToken = token;
  if (token) localStorage.setItem("access", token);
  else localStorage.removeItem("access");
}
export function loadAccessTokenFromStorage() {
  const t = localStorage.getItem("access");
  if (t) accessToken = t;
}
API.interceptors.request.use((config) => {
  if (accessToken) config.headers.Authorization = `Bearer ${accessToken}`;
  return config;
});

// --- API calls ---
export const login = (username, password) =>
  API.post("/api/auth/login", { username, password }).then((r) => r.data);

export const registerUser = (username, email, password) =>
  API.post("/api/auth/register", { username, email, password }).then(
    (r) => r.data
  );

export const onboardingState = () =>
  API.get("/api/onboarding/state").then((r) => r.data);

export const testCreds = (api_key, api_secret, is_testnet = true) =>
  API.post("/api/onboarding/credentials/test", {
    api_key,
    api_secret,
    is_testnet,
  }).then((r) => r.data);

export const saveCreds = (api_key, api_secret, is_testnet = true) =>
  API.post("/api/onboarding/credentials/save", {
    exchange: "bybit",
    api_key,
    api_secret,
    is_testnet,
  }).then((r) => r.data);

export const keyInfo = () =>
  API.get("/api/account/api-key-info").then((r) => r.data);

export const balances = (accountType = "UNIFIED") =>
  API.get("/api/wallet/balances", { params: { accountType } }).then(
    (r) => r.data
  );

export const openOrders = (symbol = "BTCUSDT", category = "linear") =>
  API.get("/api/orders", { params: { symbol, category } }).then((r) => r.data);

export default API;
