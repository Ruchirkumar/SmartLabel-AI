import axios from "axios";

const API_BASE_URL =
  import.meta.env.VITE_API_BASE_URL || "http://127.0.0.1:8000/api";

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    "Content-Type": "application/json",
  },
  timeout: 30000,
});

// Attach JWT automatically
api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem("smartlabel_token");

    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }

    return config;
  },
  (error) => Promise.reject(error),
);

// Handle expired/invalid authentication
api.interceptors.response.use(
  (response) => response,
  (error) => {
    const status = error.response?.status;

    // Don't redirect while already on authentication pages.
    const authPaths = [
      "/login",
      "/register",
      "/forgot-password",
      "/reset-password",
    ];

    const isAuthPage = authPaths.includes(window.location.pathname);

    if (status === 401 && !isAuthPage) {
      localStorage.removeItem("smartlabel_token");
      localStorage.removeItem("smartlabel_user");
      localStorage.removeItem("smartlabel_remember");

      window.location.href = "/login";
    }

    return Promise.reject(error);
  },
);

export default api;