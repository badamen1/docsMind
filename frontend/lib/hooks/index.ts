/**
 * Re-exports de hooks públicos.
 * useAuth ahora viene del AuthContext centralizado.
 */

export { useAuth } from "@/lib/contexts/AuthContext";
export { useProtectedRoute, ProtectedRoute } from "./useProtectedRoute";
