from django.urls import path

from orders.views import OrderDetailView, OrderListCreateView, OrderPaymentView

urlpatterns = [
    path("orders/", OrderListCreateView.as_view(), name="order-list-create"),
    path("orders/<int:pk>/", OrderDetailView.as_view(), name="order-detail"),
    path("orders/<int:pk>/pay/", OrderPaymentView.as_view(), name="order-pay"),
]
