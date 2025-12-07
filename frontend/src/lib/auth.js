import { setAccessToken, loadAccessTokenFromStorage } from "./api";

export function initAuth() {
  loadAccessTokenFromStorage();
}
export function logout() {
  setAccessToken(null);
}
