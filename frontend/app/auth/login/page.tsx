"use client";

import Link from "next/link";
import { useState } from "react";
import { useAuth } from "@/lib/contexts/AuthContext";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { ApiError } from "@/lib/api";

export default function LoginPage() {
  const { login, loading, clearError } = useAuth();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [formError, setFormError] = useState<string | null>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setFormError(null);
    clearError();

    if (!email.trim() || !password.trim()) {
      setFormError("Email y contraseña son requeridos");
      return;
    }

    try {
      await login(email, password);
    } catch (err) {
      if (err instanceof ApiError) {
        setFormError(err.data?.detail || err.message);
      } else {
        setFormError("Error al iniciar sesión");
      }
    }
  };

  return (
    <main className="min-h-screen bg-gradient-to-br from-slate-900 via-blue-900 to-slate-900 flex items-center justify-center">
      <div className="w-full max-w-md">
        {/* Logo */}
        <div className="flex items-center gap-2 mb-8">
          <div className="w-10 h-10 bg-blue-500 rounded flex items-center justify-center">
            <span className="text-white font-bold">D</span>
          </div>
          <span className="text-2xl font-bold">DocsMind</span>
        </div>

        {/* Card */}
        <div className="bg-slate-800/50 border border-slate-700 rounded-lg p-8 backdrop-blur">
          <h1 className="text-2xl font-bold mb-2">Bienvenido de vuelta</h1>
          <p className="text-slate-400 mb-6">
            Desbloquea el potencial de tus documentos con IA.
          </p>

          <form onSubmit={handleSubmit} className="space-y-4">
            <Input
              label="Correo electrónico"
              type="email"
              placeholder="nombre@empresa.com"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              disabled={loading}
            />

            <Input
              label="Contraseña"
              type="password"
              placeholder="••••••••"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              disabled={loading}
            />

            {formError && (
              <div className="bg-red-900/20 border border-red-600 text-red-400 p-3 rounded-lg text-sm">
                {formError}
              </div>
            )}

            <div className="flex items-center gap-2">
              <input
                type="checkbox"
                id="remember"
                className="w-4 h-4 rounded border-slate-600 bg-slate-800"
              />
              <label htmlFor="remember" className="text-sm text-slate-300">
                Recordarme por 30 días
              </label>
            </div>

            <Button
              type="submit"
              disabled={loading}
              className="w-full"
            >
              {loading ? "Iniciando sesión..." : "Iniciar Sesión"}
            </Button>
          </form>

          {/* Sign up link */}
          <p className="text-center text-slate-400 mt-6">
            ¿No tienes una cuenta?{" "}
            <Link href="/auth/register" className="text-blue-400 hover:text-blue-300">
              Crear Cuenta
            </Link>
          </p>
        </div>

        <p className="text-center text-slate-500 text-sm mt-6">
          © 2026 DocsMind. Todos los derechos reservados.
        </p>
      </div>
    </main>
  );
}
