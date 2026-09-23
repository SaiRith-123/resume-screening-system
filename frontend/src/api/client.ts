import axios, { AxiosError } from "axios";
import { getOpenAIKey } from "./openaiKey";

const BASE_URL = import.meta.env.VITE_API_BASE_URL ?? "http://localhost:8000/api";

function needsOpenAIKey(url?: string, method?: string, data?: unknown) {
  if (!url) return false;
  if (url.includes("/explanation") || url.includes("/interview-questions")) return true;
  if (url.includes("/resumes")) return url.includes("use_llm=true");
  if (url.endsWith("/jobs") && method?.toLowerCase() === "post") {
    return typeof data === "object" && data !== null &&
      (data as { parse_with_llm?: boolean }).parse_with_llm === true;
  }
  return false;
}

export const api = axios.create({ baseURL: BASE_URL, timeout: 60000, withCredentials: true });

api.interceptors.request.use((config) => {
  const accessToken = sessionStorage.getItem("rss_access_token");
if (accessToken) {
  config.headers = config.headers ?? {};
  config.headers.Authorization = `Bearer ${accessToken}`;
}
  const openAIKey = getOpenAIKey();
  if (openAIKey && needsOpenAIKey(config.url, config.method, config.data)) {
    config.headers = config.headers ?? {};
    config.headers["X-OpenAI-API-Key"] = openAIKey;
  }
  return config;
});

api.interceptors.response.use(
  (r) => r,
  (error: AxiosError<{ error?: { message?: string; code?: string } }>) => {
    if (error.response?.status === 401) {
      if (!window.location.pathname.startsWith("/login")) {
        window.location.href = "/login";
      }
    }
    const message =
      error.response?.data?.error?.message ??
      error.message ??
      "Something went wrong. Please try again.";
    return Promise.reject(new Error(message));
  }
);

export default api;
