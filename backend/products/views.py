import logging

from rest_framework import generics
from rest_framework.permissions import AllowAny, IsAdminUser

from products.models import Product
from products.serializers import ProductSerializer


logger = logging.getLogger("shop")


class ProductListCreateView(generics.ListCreateAPIView):
    serializer_class = ProductSerializer

    def get_queryset(self):
        return Product.objects.filter(is_active=True)

    def get_permissions(self):
        if self.request.method == "POST":
            return [IsAdminUser()]

        return [AllowAny()]

    def perform_create(self, serializer):
        product = serializer.save()
        logger.info(
            "event=product_created product_id=%s admin_id=%s",
            product.pk,
            self.request.user.pk,
        )


class ProductDetailView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = ProductSerializer

    def get_queryset(self):
        return Product.objects.filter(is_active=True)

    def get_permissions(self):
        if self.request.method in ["DELETE", "PUT", "PATCH"]:
            return [IsAdminUser()]

        return [AllowAny()]

    def perform_update(self, serializer):
        product = serializer.save()
        logger.info(
            "event=product_updated product_id=%s admin_id=%s",
            product.pk,
            self.request.user.pk,
        )

    def perform_destroy(self, instance):
        instance.is_active = False
        instance.save(update_fields=["is_active", "updated_at"])
        logger.info(
            "event=product_deactivated product_id=%s admin_id=%s",
            instance.pk,
            self.request.user.pk,
        )
