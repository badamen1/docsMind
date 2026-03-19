"use client";

import { AuthProvider } from "@/lib/contexts/AuthContext";

/**
 * Providers — Envuelve la app con todos los context providers necesarios.
 * Se separa en un archivo "use client" porque el layout es un Server Component.
 */
export function Providers({ children }: { children: React.ReactNode }) {
  return <AuthProvider>{children}</AuthProvider>;
}
