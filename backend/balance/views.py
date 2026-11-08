from drf_spectacular.utils import extend_schema
from rest_framework import generics, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from balance.models import Balance
from balance.serializers import BalanceSerializer, TopUpBalanceSerializer
from balance.services import top_up_balance


class BalanceView(generics.RetrieveAPIView):
    serializer_class = BalanceSerializer
    permission_classes = [IsAuthenticated]

    def get_object(self):
        balance, _ = Balance.objects.get_or_create(user=self.request.user)
        return balance


class BalanceTopUpView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        request=TopUpBalanceSerializer,
        responses={200: BalanceSerializer},
        operation_id="balance_top_up",
    )
    def post(self, request):
        serializer = TopUpBalanceSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        balance = top_up_balance(
            user=request.user, amount=serializer.validated_data["amount"]
        )

        return Response(
            BalanceSerializer(balance).data,
            status=status.HTTP_200_OK,
        )
