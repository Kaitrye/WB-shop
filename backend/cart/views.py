from rest_framework import generics, mixins
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView
from rest_framework.exceptions import ValidationError
from rest_framework import status
from rest_framework.response import Response

from cart.serializers import (
    AddCartItemSerializer, 
    CartItemSerializer, 
    CartSerializer, 
    UpdateCartItemSerializer,
)
from cart.models import CartItem, Cart



class CartItemCreateView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        cart, _ = Cart.objects.get_or_create(user=request.user)

        serializer = AddCartItemSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        product = serializer.validated_data["product"]
        quantity = serializer.validated_data["quantity"]

        if quantity > product.stock:
            raise ValidationError(
                {"quantity": "Запрошенное количество превышает остаток товара."}
            )

        item, created = CartItem.objects.get_or_create(
            cart=cart,
            product=product,
            defaults={"quantity": quantity},
        )

        if not created:
            new_quantity = item.quantity + quantity

            if new_quantity > product.stock:
                raise ValidationError(
                    {"quantity": "Запрошенное количество превышает остаток товара."}
                )

            item.quantity = new_quantity
            item.save(update_fields=["quantity", "updated_at"])

        response_serializer = CartItemSerializer(item)

        return Response(
            response_serializer.data, 
            status=status.HTTP_201_CREATED if created else status.HTTP_200_OK,
        )


class CartView(generics.RetrieveAPIView):
    serializer_class = CartSerializer
    permission_classes = [IsAuthenticated]

    def get_object(self):
        cart, _ = Cart.objects.get_or_create(user=self.request.user)

        return cart


class CartItemDetailView(
    mixins.UpdateModelMixin,
    mixins.DestroyModelMixin,
    generics.GenericAPIView,
):
    serializer_class = UpdateCartItemSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return CartItem.objects.filter(cart__user=self.request.user)


    def patch(self, request, *args, **kwargs):
        return self.partial_update(request, *args, **kwargs)

    def delete(self, request, *args, **kwargs):
        return self.destroy(request, *args, **kwargs)    