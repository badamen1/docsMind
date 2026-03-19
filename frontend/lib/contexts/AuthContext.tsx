"use client";

/**
 * AuthContext — estado de autenticación compartido en toda la app.
 * Resuelve el problema de que useAuth() creaba estados independientes
 * por cada componente que lo usaba.
 */

import {
  createContext,
  useContext,
  useEffect,
  useState,
  ReactNode,
} from "react";
import { useRouter } from "next/navigation";
import { authAPI } from "@/lib/api-endpoints";
import { User } from "@/lib/types";
import { ApiError, clearTokens, setTokens, getAccessToken } from "@/lib/api";

interface AuthContextType {
  user: User | null;
  loading: boolean;
  error: string | null;
  register: (
    email: string,
    username: string,
    password: string,
    passwordConfirm: string
  ) => Promise<void>;
  login: (email: string, password: string) => Promise<void>;
  logout: () => Promise<void>;
  clearError: () => void;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export function AuthProvider({ children }: { children: ReactNode }) {
  const router = useRouter();
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Verificar sesión al montar
  useEffect(() => {
    const checkAuth = async () => {
      const token = getAccessToken();
      if (!token) {
        setLoading(false);
        return;
      }

      try {
        const currentUser = await authAPI.getMe();
        setUser(currentUser);
      } catch {
        clearTokens();
        setUser(null);
      } finally {
        setLoading(false);
      }
    };

    checkAuth();
  }, []);

  const register = async (
    email: string,
    username: string,
    password: string,
    passwordConfirm: string
  ) => {
    setError(null);
    setLoading(true);
    try {
      const response = await authAPI.register({
        email,
        username,
        password,
        password_confirm: passwordConfirm,
      });
      setTokens({ access: response.access, refresh: response.refresh });
      setUser(response.user);
      router.push("/dashboard");
    } catch (err) {
      const message =
        err instanceof ApiError
          ? err.data?.detail || err.message
          : "Error al registrarse";
      setError(message);
      throw err;
    } finally {
      setLoading(false);
    }
  };

  const login = async (email: string, password: string) => {
    setError(null);
    setLoading(true);
    try {
      const response = await authAPI.login(email, password);
      setTokens({ access: response.access, refresh: response.refresh });
      setUser(response.user);
      router.push("/dashboard");
    } catch (err) {
      const message =
        err instanceof ApiError
          ? err.data?.detail || err.message
          : "Error al iniciar sesión";
      setError(message);
      throw err;
    } finally {
      setLoading(false);
    }
  };

  const logout = async () => {
    setError(null);
    try {
      await authAPI.logout();
    } catch {
      // Ignorar error del backend, limpiar tokens de todas formas
    } finally {
      clearTokens();
      setUser(null);
      router.push("/auth/login");
    }
  };

  const clearError = () => setError(null);

  return (
    <AuthContext.Provider
      value={{ user, loading, error, register, login, logout, clearError }}
    >
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth(): AuthContextType {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error("useAuth debe usarse dentro de un AuthProvider");
  }
  return context;
}
