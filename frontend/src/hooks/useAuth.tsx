import { createContext, useContext, useEffect, useState, ReactNode } from "react";
import api from "../api/client";
import type { AuthUser, Token } from "../types";
import { clearOpenAIKey } from "../api/openaiKey";
import { firebaseConfigured, registerWithEmail, signInWithEmail, signInWithGoogle } from "../api/firebase";

interface AuthContextValue {
  user: AuthUser | null;
  loading: boolean;
  login: (email: string, password: string) => Promise<void>;
  loginWithGoogle: (acceptTerms: boolean, acceptPrivacy: boolean) => Promise<void>;
  register: (email: string, fullName: string, password: string, acceptTerms: boolean, acceptPrivacy: boolean) => Promise<void>;
  logout: () => void;
}

const AuthContext = createContext<AuthContextValue | undefined>(undefined);

const USER_KEY = "rss_user";

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<AuthUser | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const raw = sessionStorage.getItem(USER_KEY);
    if (raw) {
      try {
        setUser(JSON.parse(raw) as AuthUser);
      } catch {
        sessionStorage.removeItem(USER_KEY);
      }
    }
    setLoading(false);
  }, []);

  function persist(token: Token) {
    sessionStorage.setItem(USER_KEY, JSON.stringify(token.user));
    setUser(token.user);
  }

  async function login(email: string, password: string) {
    if (firebaseConfigured) {
      const idToken = await signInWithEmail(email, password);
      const { data } = await api.post<Token>("/auth/firebase", {
        id_token: idToken, accept_terms: true, accept_privacy: true,
      });
      persist(data);
      return;
    }
    const { data } = await api.post<Token>("/auth/login", { email, password });
    persist(data);
  }

  async function loginWithGoogle(acceptTerms: boolean, acceptPrivacy: boolean) {
    const idToken = await signInWithGoogle();
    const { data } = await api.post<Token>("/auth/firebase", {
      id_token: idToken,
      accept_terms: acceptTerms,
      accept_privacy: acceptPrivacy,
    });
    persist(data);
  }

  async function register(email: string, fullName: string, password: string, acceptTerms: boolean, acceptPrivacy: boolean) {
    if (firebaseConfigured) {
      if (!acceptTerms || !acceptPrivacy) throw new Error("Terms and privacy consent are required.");
      const idToken = await registerWithEmail(email, password);
      const { data } = await api.post<Token>("/auth/firebase", {
        id_token: idToken, accept_terms: acceptTerms, accept_privacy: acceptPrivacy,
      });
      persist(data);
      return;
    }
    const { data } = await api.post<Token>("/auth/register", {
      email,
      full_name: fullName,
      password,
      accept_terms: acceptTerms,
      accept_privacy: acceptPrivacy,
    });
    persist(data);
  }

  function logout() {
    void api.post("/auth/logout").catch(() => undefined);
    clearOpenAIKey();
    sessionStorage.removeItem(USER_KEY);
    setUser(null);
  }

  return (
    <AuthContext.Provider value={{ user, loading, login, loginWithGoogle, register, logout }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error("useAuth must be used within AuthProvider");
  return ctx;
}
