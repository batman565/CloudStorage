import { makeAutoObservable } from "mobx";
import axios from "axios";

class AuthStore {
  token = null;
  tokenExpiration = null;
  isLoading = false;
  error = null;

  constructor() {
    makeAutoObservable(this);
    this.loadTokenFromStorage();
    this.setupAxiosInterceptors();
  }

  get isAuthenticated() {
    if (!this.token || !this.tokenExpiration) return false;
    const now = new Date();
    const expirationDate = new Date(this.tokenExpiration);
    return expirationDate > now;
  }

  loadTokenFromStorage() {
    const authDataJson = localStorage.getItem("authData");
    if (!authDataJson) return;

    try {
      const authData = JSON.parse(authDataJson);
      const expirationDate = new Date(authData.tokenExpiration);

      if (expirationDate > new Date()) {
        this.token = authData.token;
        this.tokenExpiration = authData.tokenExpiration;
        axios.defaults.headers.common[
          "Authorization"
        ] = `Bearer ${authData.token}`;
      } else {
        this.clearToken();
      }
    } catch (error) {
      console.error("Error loading auth data:", error);
      this.clearToken();
    }
  }

  setupAxiosInterceptors = () => {
    axios.interceptors.response.use(
      (response) => response,
      (error) => {
        if (error.response?.status === 401 && this.isAuthenticated) {
          this.logout();
        }
        return Promise.reject(error);
      }
    );
  };

  setAuthData(token, expiration) {
    this.token = token;
    this.tokenExpiration = expiration;

    const authData = { token, tokenExpiration: expiration };
    localStorage.setItem("authData", JSON.stringify(authData));

    axios.defaults.headers.common["Authorization"] = `Bearer ${token}`;
  }

  clearToken() {
    this.token = null;
    this.tokenExpiration = null;
    localStorage.removeItem("authData");
    delete axios.defaults.headers.common["Authorization"];
  }

  async login(username, password) {
    this.isLoading = true;
    this.error = null;

    try {
      const params = new URLSearchParams();
      params.append("username", username);
      params.append("password", password);
      params.append("grant_type", "password");

      const response = await axios.post("/api/token/", params.toString(), {
        headers: {
          "Content-Type": "application/x-www-form-urlencoded",
        },
      });

      this.setAuthData(response.data.access_token, response.data.expired);
    } catch (error) {
      this.error = error.response?.data?.detail || "Login failed";
      throw error;
    } finally {
      this.isLoading = false;
    }
  }

  logout() {
    this.clearToken();
  }
}

export default AuthStore;
