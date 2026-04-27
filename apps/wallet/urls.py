from django.urls import path
from . import views

app_name = "wallet"

urlpatterns = [
    path("packages/", views.CoinPackageListView.as_view(), name="packages"),
    path("checkout/<int:package_id>/", views.CreateCheckoutSessionView.as_view(), name="checkout"),
    path("webhook/", views.stripe_webhook, name="webhook"),
    path("history/", views.CoinLedgerHistoryView.as_view(), name="history"),
]
