'use client';

import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { useAuth } from '@/lib/hooks/useAuth';
import {
  PaymentElement,
  useElements,
  useStripe,
  Elements,
} from '@stripe/react-stripe-js';
import { loadStripe } from '@stripe/stripe-js';
import { subscriptionAPI } from '@/lib/api-endpoints';

const stripePromise = loadStripe(process.env.NEXT_PUBLIC_STRIPE_KEY!);
const PRODUCT_ID = process.env.NEXT_PUBLIC_STRIPE_PRODUCT_ID || 'prod_TzyvSWJWZYnzkQ';

const benefits = [
  {
    icon: (
      <svg className="w-5 h-5 text-blue-600 mt-0.5 flex-shrink-0" viewBox="0 0 24 24" fill="currentColor">
        <path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm-2 14.5-4.5-4.5 1.41-1.41L10 13.67l7.09-7.09L18.5 8l-8.5 8.5z" />
      </svg>
    ),
    text: 'Sube hasta 100 documentos con 1 GB de almacenamiento',
  },
  {
    icon: (
      <svg className="w-5 h-5 text-blue-600 mt-0.5 flex-shrink-0" viewBox="0 0 24 24" fill="currentColor">
        <path d="M7 2v11h3v9l7-12h-4l4-8z" />
      </svg>
    ),
    text: 'Acceso a modelos IA más avanzados y respuestas más precisas',
  },
  {
    icon: (
      <svg className="w-5 h-5 text-blue-600 mt-0.5 flex-shrink-0" viewBox="0 0 24 24" fill="currentColor">
        <path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm-1 14H9V8h2v8zm4 0h-2V8h2v8z" />
        <path d="M12 2a10 10 0 100 20A10 10 0 0012 2zm0 18a8 8 0 110-16 8 8 0 010 16zm-1-5h2v2h-2zm0-8h2v6h-2z" />
      </svg>
    ),
    text: 'Acceso a los mejores modelos de OCR para extracción precisa',
  },
];

// ── Formulario interno (requiere Elements context) ──────────────────────────

function PaymentFormContent() {
  const router = useRouter();
  const stripe = useStripe();
  const elements = useElements();

  const [processing, setProcessing] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!stripe || !elements) return;

    setProcessing(true);
    setError(null);

    try {
      const { error: confirmError, setupIntent } = await stripe.confirmSetup({
        elements,
        confirmParams: {
          return_url: `${window.location.origin}/subscribe/success`,
        },
        redirect: 'if_required',
      });

      if (confirmError) {
        throw new Error(confirmError.message || 'Error al confirmar el método de pago');
      }

      if (!setupIntent?.payment_method) {
        throw new Error('No se obtuvo el método de pago de Stripe');
      }

      await subscriptionAPI.subscribe(PRODUCT_ID, setupIntent.payment_method as string);
      router.push('/subscribe/success');
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Error desconocido');
    } finally {
      setProcessing(false);
    }
  };

  return (
    <form onSubmit={handleSubmit} className="flex flex-col gap-6">
      {error && (
        <div className="p-4 bg-red-50 border border-red-200 text-red-700 rounded-xl text-sm">
          {error}
        </div>
      )}

      <div>
        <h3 className="text-xl font-semibold text-gray-900 mb-6">Método de Pago</h3>
        <PaymentElement
          options={{
            layout: {
              type: 'accordion',
              defaultCollapsed: false,
              radios: 'never',
              spacedAccordionItems: true,
            },
          }}
        />
      </div>

      <button
        type="submit"
        disabled={processing || !stripe || !elements}
        className={`w-full py-4 rounded-xl font-bold text-lg text-white transition-all duration-300 flex items-center justify-center gap-2 ${
          processing || !stripe || !elements
            ? 'bg-gray-400 cursor-not-allowed'
            : 'bg-blue-600 hover:bg-blue-700 hover:shadow-lg hover:shadow-blue-500/30'
        }`}
      >
        {processing ? (
          <>
            <span className="animate-spin rounded-full h-5 w-5 border-b-2 border-white" />
            Procesando...
          </>
        ) : (
          <>
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z" />
            </svg>
            Suscribirse — $9.99/mes
          </>
        )}
      </button>

      <p className="text-center text-xs text-gray-400 flex items-center justify-center gap-1.5">
        <svg className="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z" />
        </svg>
        Pagos seguros con Stripe. Tu información está encriptada.
      </p>
    </form>
  );
}

// ── Layout completo de dos columnas ──────────────────────────────────────────

export function SubscriptionForm() {
  const router = useRouter();
  const { subscription } = useAuth();

  const [clientSecret, setClientSecret] = useState<string | null>(null);
  const [loadError, setLoadError] = useState<string | null>(null);
  const [loadingSecret, setLoadingSecret] = useState(false);

  const fetchSetupIntent = async () => {
    setLoadError(null);
    setLoadingSecret(true);
    try {
      const data = await subscriptionAPI.setupIntent();
      setClientSecret(data.client_secret);
    } catch (err) {
      setLoadError(
        err instanceof Error ? err.message : 'Error al inicializar el pago'
      );
    } finally {
      setLoadingSecret(false);
    }
  };

  useEffect(() => {
    if (subscription?.plan_type === 'pro') {
      router.replace('/dashboard');
      return;
    }
    fetchSetupIntent();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  return (
    <div className="min-h-screen bg-gray-50 flex items-center justify-center px-6 py-12 relative overflow-x-hidden">
      {/* Ambient glow */}
      <div className="fixed top-[-10%] left-[-10%] w-[40vw] h-[40vw] rounded-full bg-blue-400/10 blur-[150px] pointer-events-none" />
      <div className="fixed bottom-[-20%] right-[-10%] w-[50vw] h-[50vw] rounded-full bg-indigo-400/5 blur-[150px] pointer-events-none" />

      <div className="w-full max-w-6xl grid grid-cols-1 lg:grid-cols-12 gap-12 lg:gap-24 items-start relative z-10">

        {/* ── Columna izquierda: resumen ─────────────────────────────────── */}
        <div className="lg:col-span-5 flex flex-col gap-10">
          <div>
            <button
              onClick={() => router.back()}
              className="flex items-center gap-2 text-blue-600 hover:text-blue-800 transition-colors mb-6 group"
            >
              <svg
                className="w-4 h-4 group-hover:-translate-x-1 transition-transform"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 19l-7-7m0 0l7-7m-7 7h18" />
              </svg>
              <span className="text-sm font-semibold uppercase tracking-widest">Volver</span>
            </button>

            <h1 className="text-5xl md:text-6xl font-extrabold text-gray-900 tracking-tight">
              Checkout
            </h1>
          </div>

          <div className="flex flex-col gap-8">
            {/* Plan identity */}
            <div className="flex items-start justify-between">
              <div>
                <h2 className="text-3xl font-bold text-blue-600">Plan Pro</h2>
                <p className="text-gray-500 mt-1 text-sm">
                  Accede a todas las funciones premium de DocsMind
                </p>
              </div>
              <div className="text-right">
                <span className="text-4xl font-bold text-gray-900">$9.99</span>
                <span className="text-gray-500 text-sm block">/ mes</span>
              </div>
            </div>

            {/* Benefits */}
            <ul className="flex flex-col gap-3">
              {benefits.map((b, i) => (
                <li
                  key={i}
                  className="flex items-start gap-4 p-4 rounded-xl bg-white shadow-sm hover:shadow-md transition-shadow"
                >
                  {b.icon}
                  <span className="text-gray-700 text-sm leading-relaxed">{b.text}</span>
                </li>
              ))}
            </ul>
          </div>

          {/* Total */}
          <div className="pt-8 flex items-center justify-between border-t border-gray-200">
            <span className="text-gray-500 text-lg">Total hoy</span>
            <span className="text-2xl font-bold text-blue-600">$9.99</span>
          </div>

          <p className="text-xs text-gray-400">
            Cargo mensual recurrente. Cancela en cualquier momento desde tu dashboard.
          </p>
        </div>

        {/* ── Columna derecha: pago ──────────────────────────────────────── */}
        <div className="lg:col-span-7">
          <div className="bg-white rounded-2xl p-6 md:p-10 shadow-xl relative overflow-hidden">
            {/* Top glass highlight */}
            <div className="absolute top-0 left-0 w-full h-px bg-gradient-to-r from-transparent via-blue-200/60 to-transparent" />

            {loadError ? (
              <div className="flex flex-col gap-4">
                <div className="p-4 bg-red-50 border border-red-200 text-red-700 rounded-xl text-sm">
                  {loadError}
                </div>
                <button
                  onClick={fetchSetupIntent}
                  disabled={loadingSecret}
                  className="w-full py-3 bg-blue-600 hover:bg-blue-700 text-white rounded-xl font-semibold disabled:bg-gray-400 transition"
                >
                  {loadingSecret ? 'Reintentando...' : 'Reintentar'}
                </button>
              </div>
            ) : !clientSecret ? (
              <div className="flex flex-col items-center justify-center h-48 gap-4">
                <div className="animate-spin rounded-full h-10 w-10 border-b-2 border-blue-600" />
                <p className="text-sm text-gray-400">Preparando formulario de pago...</p>
              </div>
            ) : (
              <Elements
                stripe={stripePromise}
                options={{
                  clientSecret,
                  appearance: {
                    theme: 'stripe',
                    variables: {
                      colorPrimary: '#2563eb',
                      borderRadius: '8px',
                    },
                  },
                }}
              >
                <PaymentFormContent />
              </Elements>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
