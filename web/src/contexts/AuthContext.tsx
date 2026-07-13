"use client";

import {
  createContext,
  useContext,
  useState,
  useEffect,
  useCallback,
  type ReactNode,
} from "react";
import {
  authApi,
  setToken,
  clearToken,
  getToken,
  type User,
  type ApiError,
} from "@/lib/api";

interface AuthContextValue {
  user: User | null;
  loading: boolean;
  isAuthenticated: boolean;
  login: (email: string, password: string) => Promise<void>;
  register: (data: {
    email: string;
    password: string;
    full_name?: string;
    phone?: string;
  }) => Promise<void>;
  logout: () => void;
  loginWithToken: (token: string) => Promise<void>;
}

const AuthContext = createContext<AuthContextValue | undefined>(undefined);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);

  // On mount: check for existing token and fetch user
  useEffect(() => {
    const token = getToken();
    if (!token) {
      setLoading(false);
      return;
    }

    authApi
      .me()
      .then((u) => setUser(u))
      .catch(() => {
        // Token is invalid/expired — clear it
        clearToken();
      })
      .finally(() => setLoading(false));
  }, []);

  const login = useCallback(async (email: string, password: string) => {
    const res = await authApi.login({ email, password });
    setToken(res.access_token);
    setUser(res.user);
  }, []);

  const register = useCallback(
    async (data: {
      email: string;
      password: string;
      full_name?: string;
      phone?: string;
    }) => {
      const res = await authApi.register(data);
      setToken(res.access_token);
      setUser(res.user);
    },
    []
  );

  const logout = useCallback(() => {
    clearToken();
    setUser(null);
  }, []);

  const loginWithToken = useCallback(async (token: string) => {
    setToken(token);
    try {
      const u = await authApi.me();
      setUser(u);
    } catch {
      clearToken();
      throw new Error("Invalid token");
    }
  }, []);

  return (
    <AuthContext.Provider
      value={{
        user,
        loading,
        isAuthenticated: !!user,
        login,
        register,
        logout,
        loginWithToken,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error("useAuth must be used within AuthProvider");
  return ctx;
}

export type { ApiError };
