'use client';

import { SubscriptionForm } from '@/components/dashboard/StripePaymentForm';
import { useProtectedRoute } from '@/lib/hooks/useProtectedRoute';

export default function SubscribePage() {
  useProtectedRoute(); // Requiere autenticación

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100 py-12">
      <div className="container mx-auto">
        <div className="text-center mb-12">
          <h1 className="text-4xl font-bold text-gray-900 mb-4">
            🚀 Suscribirse a Pro
          </h1>
          <p className="text-xl text-gray-600">
            Accede a todas las funciones premium de DocsMind
          </p>
        </div>

        {/* Cards con beneficios */}
        <div className="grid md:grid-cols-3 gap-6 mb-12">
          <div className="bg-white p-6 rounded-lg shadow hover:shadow-lg transition">
            <h3 className="font-bold mb-2 text-lg">📄 Documentos Ilimitados</h3>
            <p className="text-gray-600 text-sm">
              Sube tantos documentos como quieras sin límites de almacenamiento
            </p>
          </div>
          <div className="bg-white p-6 rounded-lg shadow hover:shadow-lg transition">
            <h3 className="font-bold mb-2 text-lg">🤖 IA Premium</h3>
            <p className="text-gray-600 text-sm">
              Acceso a modelos IA más avanzados y respuestas más precisas
            </p>
          </div>
          <div className="bg-white p-6 rounded-lg shadow hover:shadow-lg transition">
            <h3 className="font-bold mb-2 text-lg">⚡ Procesamiento Rápido</h3>
            <p className="text-gray-600 text-sm">
              Procesamiento prioritario y análisis simultáneo de múltiples documentos
            </p>
          </div>
        </div>

        {/* Formulario */}
        <SubscriptionForm />

        {/* Info seguridad */}
        <div className="text-center mt-8">
          <p className="text-gray-600 text-sm">
            🔒 Todos los pagos son procesados de forma segura por Stripe
          </p>
        </div>
      </div>
    </div>
  );
}
