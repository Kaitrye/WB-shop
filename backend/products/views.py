from rest_framework import generics
from rest_framework.permissions import AllowAny, IsAdminUser

from products.models import Product
from products.serializers import ProductSerializer


class ProductListCreateView(generics.ListCreateAPIView):
    serializer_class = ProductSerializer

    def get_queryset(self):
        return Product.objects.filter(is_active=True)

    def get_permissions(self):
        if self.request.method == "POST":
            return [IsAdminUser()]

        return [AllowAny()]


class ProductDetailView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = ProductSerializer

    def get_queryset(self):
        return Product.objects.filter(is_active=True)

    def get_permissions(self):
        if self.request.method in ["DELETE", "PUT", "PATCH"]:
            return [IsAdminUser()]

        return [AllowAny()]

    def perform_destroy(self, instance):
        instance.is_active = False
        instance.save(update_fields=["is_active", "updated_at"])


