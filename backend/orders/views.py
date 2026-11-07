from rest_framework import generics
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework import status
from rest_framework.response import Response


from orders.services import create_order_from_cart
from balance.services import pay_for_order
from orders.serializers import CreateOrderSerializer, OrderSerializer
from orders.models import Order

from drf_spectacular.utils import extend_schema


class OrderListCreateView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        request=CreateOrderSerializer,
        responses={201: OrderSerializer},
        operation_id="order_create",
    )
    def post(self, request):
        serializer = CreateOrderSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        order = create_order_from_cart(
            user=request.user,
            cart_item_ids=serializer.validated_data["cart_item_ids"],
        )

        response_serializer = OrderSerializer(order)

        return Response(
            response_serializer.data, 
            status=status.HTTP_201_CREATED,
        )

    @extend_schema(
        responses={200: OrderSerializer(many=True)},
        operation_id="order_list",
    )
    def get(self, request):
        orders = (
            Order.objects.filter(user=request.user)
            .prefetch_related("items__product")
            .order_by("-created_at")
        )

        return Response(OrderSerializer(orders, many=True).data)


class OrderDetailView(generics.RetrieveAPIView):
    serializer_class = OrderSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return (
            Order.objects.filter(user=self.request.user)
            .prefetch_related("items__product")
        )


class OrderPaymentView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        request=None,
        responses={200: OrderSerializer},
        operation_id="order_pay",
    )
    def post(self, request, pk):
        order = pay_for_order(user=request.user, order_id=pk)
        return Response(OrderSerializer(order).data, status=status.HTTP_200_OK)