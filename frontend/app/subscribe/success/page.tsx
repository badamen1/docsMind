'use client';

import { useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { useAuth } from '@/lib/hooks/useAuth';
import { useProtectedRoute } from '@/lib/hooks/useProtectedRoute';

const PRO_FEATURES = [
  {
    icon: '📄',
    title: '100 documentos',
    desc: 'Sube hasta 100 documentos',
  },
  {
    icon: '💾',
    title: '1 GB de almacenamiento',
    desc: 'Espacio amplio para tus archivos',
  },
  {
    icon: '🤖',
    title: 'IA Premium',
    desc: 'Acceso a modelos avanzados',
  },
  {
    icon: '⚡',
    title: 'Procesamiento prioritario',
    desc: 'Respuestas más rápidas',
  },
];

export default function SubscribeSuccessPage() {
  useProtectedRoute();
  const router = useRouter();
  const { refreshSubscription } = useAuth();

  useEffect(() => {
    refreshSubscription();
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100 flex items-center justify-center py-12 px-4">
      <div className="max-w-lg w-full bg-white rounded-2xl shadow-xl p-8">
        {/* Header */}
        <div className="text-center mb-8">
          <div className="text-6xl mb-4">🎉</div>
          <h1 className="text-3xl font-bold text-gray-900 mb-2">
            ¡Plan Pro Activado!
          </h1>
          <p className="text-gray-500 mb-4">
            Tu suscripción comenzó con éxito
          </p>
          <span className="inline-block bg-blue-100 text-blue-700 font-semibold px-4 py-1 rounded-full text-sm">
            ⭐ Plan Pro — $9.99/mes
          </span>
        </div>

        {/* Features grid */}
        <div className="grid grid-cols-2 gap-3 mb-8">
          {PRO_FEATURES.map((feature) => (
            <div
              key={feature.title}
              className="flex items-start gap-3 p-3 rounded-lg bg-gray-50"
            >
              <span className="text-2xl">{feature.icon}</span>
              <div>
                <p className="font-semibold text-sm text-gray-800">
                  {feature.title}
                </p>
                <p className="text-xs text-gray-500">{feature.desc}</p>
              </div>
            </div>
          ))}
        </div>

        {/* CTA */}
        <button
          onClick={() => router.push('/dashboard')}
          className="w-full py-3 bg-blue-600 hover:bg-blue-700 text-white font-semibold rounded-lg transition"
        >
          Ir al Dashboard
        </button>

        <p className="text-xs text-gray-400 text-center mt-4">
          Puedes gestionar tu suscripción desde el dashboard en cualquier momento.
        </p>
      </div>
    </div>
  );
}
