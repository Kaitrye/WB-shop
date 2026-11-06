from django.urls import path

from balance.views import BalanceTopUpView, BalanceView


urlpatterns = [
    path("balance/", BalanceView.as_view(), name="balance"),
    path("balance/top-up/", BalanceTopUpView.as_view(), name="balance-top-up"),
]