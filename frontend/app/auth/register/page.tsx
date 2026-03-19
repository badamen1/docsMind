"use client";

import Link from "next/link";
import { useState } from "react";
import { useAuth } from "@/lib/contexts/AuthContext";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { ApiError } from "@/lib/api";

export default function RegisterPage() {
  const { register, loading, clearError } = useAuth();
  const [formData, setFormData] = useState({
    email: "",
    username: "",
    password: "",
    passwordConfirm: "",
  });
  const [formError, setFormError] = useState<string | null>(null);

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const { name, value } = e.target;
    setFormData((prev) => ({ ...prev, [name]: value }));
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setFormError(null);
    clearError();

    if (
      !formData.email ||
      !formData.username ||
      !formData.password ||
      !formData.passwordConfirm
    ) {
      setFormError("Todos los campos son requeridos");
      return;
    }

    if (formData.password !== formData.passwordConfirm) {
      setFormError("Las contraseñas no coinciden");
      return;
    }

    if (formData.password.length < 8) {
      setFormError("La contraseña debe tener al menos 8 caracteres");
      return;
    }

    try {
      await register(
        formData.email,
        formData.username,
        formData.password,
        formData.passwordConfirm
      );
    } catch (err) {
      if (err instanceof ApiError) {
        setFormError(err.data?.detail || err.message);
      } else {
        setFormError("Error al registrarse");
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
          <h1 className="text-2xl font-bold mb-2">Crear Cuenta</h1>
          <p className="text-slate-400 mb-6">
            Comienza a chatear con tus documentos hoy.
          </p>

          <form onSubmit={handleSubmit} className="space-y-4">
            <Input
              label="Correo electrónico"
              type="email"
              name="email"
              placeholder="nombre@empresa.com"
              value={formData.email}
              onChange={handleChange}
              disabled={loading}
            />

            <Input
              label="Nombre de usuario"
              type="text"
              name="username"
              placeholder="usuario"
              value={formData.username}
              onChange={handleChange}
              disabled={loading}
            />

            <Input
              label="Contraseña"
              type="password"
              name="password"
              placeholder="••••••••"
              value={formData.password}
              onChange={handleChange}
              disabled={loading}
              helperText="Mínimo 8 caracteres"
            />

            <Input
              label="Confirmar Contraseña"
              type="password"
              name="passwordConfirm"
              placeholder="••••••••"
              value={formData.passwordConfirm}
              onChange={handleChange}
              disabled={loading}
            />

            {formError && (
              <div className="bg-red-900/20 border border-red-600 text-red-400 p-3 rounded-lg text-sm">
                {formError}
              </div>
            )}

            <Button
              type="submit"
              disabled={loading}
              className="w-full"
            >
              {loading ? "Creando cuenta..." : "Crear Cuenta"}
            </Button>
          </form>

          {/* Sign in link */}
          <p className="text-center text-slate-400 mt-6">
            ¿Ya tienes una cuenta?{" "}
            <Link href="/auth/login" className="text-blue-400 hover:text-blue-300">
              Iniciar Sesión
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
