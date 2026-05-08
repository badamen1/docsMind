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
    <form onSubmit={handleSubmit} className="space-y-6">
      {error && (
        <div className="p-4 bg-red-50 border border-red-200 text-red-700 rounded-lg text-sm">
          {error}
        </div>
      )}

      <div>
        <label className="block text-sm font-medium text-gray-700 mb-3">
          Información de Pago
        </label>
        <div className="p-4 border border-gray-200 rounded-lg bg-white">
          <PaymentElement options={{ layout: 'tabs' }} />
        </div>
      </div>

      <div className="border-t pt-4 space-y-1">
        <div className="flex justify-between">
          <span className="font-medium text-gray-700">Plan Pro</span>
          <span className="font-bold text-gray-900">$9.99 / mes</span>
        </div>
        <p className="text-xs text-gray-500">
          Cargo mensual recurrente. Cancela en cualquier momento.
        </p>
      </div>

      <button
        type="submit"
        disabled={processing || !stripe || !elements}
        className={`w-full py-3 rounded-lg font-semibold text-white transition ${
          processing || !stripe || !elements
            ? 'bg-gray-400 cursor-not-allowed'
            : 'bg-blue-600 hover:bg-blue-700'
        }`}
      >
        {processing ? (
          <span className="flex items-center justify-center gap-2">
            <span className="animate-spin rounded-full h-4 w-4 border-b-2 border-white" />
            Procesando...
          </span>
        ) : (
          'Suscribirse — $9.99/mes'
        )}
      </button>

      <p className="text-xs text-gray-400 text-center">
        Pagos seguros con Stripe. Tu información está encriptada.
      </p>
    </form>
  );
}

// ── Wrapper que carga el client_secret ────────────────────────────────────

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

  if (loadError) {
    return (
      <div className="space-y-4">
        <div className="p-4 bg-red-50 border border-red-200 text-red-700 rounded-lg text-sm">
          {loadError}
        </div>
        <button
          onClick={fetchSetupIntent}
          disabled={loadingSecret}
          className="w-full py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg font-medium disabled:bg-gray-400 transition"
        >
          {loadingSecret ? 'Reintentando...' : 'Reintentar'}
        </button>
      </div>
    );
  }

  if (!clientSecret) {
    return (
      <div className="flex justify-center items-center h-40">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600" />
      </div>
    );
  }

  return (
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
  );
}
