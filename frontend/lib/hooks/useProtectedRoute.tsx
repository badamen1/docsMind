"use client";

/**
 * Hook y componente para proteger rutas que requieren autenticación.
 */

import { useRouter } from "next/navigation";
import { ReactNode, useEffect, useState } from "react";
import { useAuth } from "@/lib/contexts/AuthContext";

export function useProtectedRoute() {
  const { user, loading } = useAuth();
  const router = useRouter();
  const [isAuthorized, setIsAuthorized] = useState(false);

  useEffect(() => {
    if (!loading) {
      if (!user) {
        router.push("/auth/login");
      } else {
        setIsAuthorized(true);
      }
    }
  }, [user, loading, router]);

  return { isAuthorized, loading, user };
}

/**
 * Componente wrapper para proteger rutas
 */
export function ProtectedRoute({ children }: { children: ReactNode }) {
  const { isAuthorized, loading } = useProtectedRoute();

  if (loading) {
    return (
      <div className="flex items-center justify-center h-screen">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-500"></div>
      </div>
    );
  }

  if (!isAuthorized) {
    return null;
  }

  return <>{children}</>;
}
