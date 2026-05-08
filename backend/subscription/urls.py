from django.urls import path

from .views import (
    subscribe_view,
    create_setup_intent_view,
    subscription_detail_view,
    cancel_subscription_view,
    update_subscription_view,
    stripe_webhook_view,
)

urlpatterns = [
    path('setup-intent/', create_setup_intent_view, name='setup-intent'),
    path('subscribe/', subscribe_view, name='subscribe'),
    path('detail/', subscription_detail_view, name='subscription-detail'),
    path('cancel/', cancel_subscription_view, name='cancel-subscription'),
    path('update/', update_subscription_view, name='update-subscription'),
    path('webhook/', stripe_webhook_view, name='stripe-webhook'),
]

