'use client';

import { SubscriptionForm } from '@/components/dashboard/StripePaymentForm';
import { useProtectedRoute } from '@/lib/hooks/useProtectedRoute';

export default function SubscribePage() {
  useProtectedRoute();
  return <SubscriptionForm />;
}
