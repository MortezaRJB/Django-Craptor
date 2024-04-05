from django.shortcuts import render
from rest_framework.generics import CreateAPIView, ListAPIView, DestroyAPIView, RetrieveAPIView
from rest_framework.views import APIView
from . import models, serializers, services, utils
from rest_framework import permissions, status
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from django.utils.translation import gettext_lazy as _


class OrderCreateAndPlaceApiView(CreateAPIView):
  queryset = models.Order.objects.all()
  serializer_class = serializers.OrderSerializer
  permission_classes = (permissions.IsAuthenticated,)


class OrderCancelApiView(DestroyAPIView):
  queryset = models.Order.objects.all()
  permission_classes = (permissions.IsAuthenticated,)

  def destroy(self, request, *args, **kwargs):
    order = self.get_object()
    if order.status == models.Order.OrderStatusChoices.ACTIVE_NOT_FILLED:
      order.status = models.Order.OrderStatusChoices.CANCELLED_NOT_FILLED
      limit = order.limit
      limit.total_volume -= order.size_remained
      if limit.total_volume == 0:
        limit.delete()
      else:
        limit.save()
      order.save()
      return Response("The Not-Filled Order Cancelled Successfully.", status=status.HTTP_204_NO_CONTENT)
    elif order.status == models.Order.OrderStatusChoices.ACTIVE_PARTIALLY_FILLED:
      order.status = models.Order.OrderStatusChoices.CANCELLED_PARTIALLY_FILLED
      limit = order.limit
      limit.total_volume -= order.size_remained
      if limit.total_volume == 0:
        limit.delete()
      else:
        limit.save()
      order.save()
      return Response("The Partially-Filled Order Cancelled Successfully.", status=status.HTTP_204_NO_CONTENT)
    return Response("The Order Can Not Be Deleted!", status=status.HTTP_400_BAD_REQUEST)


class OrderBookListApiView(ListAPIView):
  queryset = models.OrderBook.objects.filter(is_open=True)
  serializer_class = serializers.OrderBookListSerializer


class OrderBookDetailView(RetrieveAPIView):
  queryset = models.OrderBook.objects.filter(is_open=True)
  serializer_class = serializers.OrderBookDetailSerializer


class GetUserBalanceApiView(APIView):
  permission_classes = (permissions.IsAuthenticated,)

  def get(self, request, currency):
    if currency:
      currency = get_object_or_404(models.CryptoCurrencyType, name__iexact=currency)
      balance = services.user_balance(request.user, currency)
      return Response({"balance": balance}, status=status.HTTP_200_OK)
    return Response({"currency": "This field is required!"}, status=status.HTTP_400_BAD_REQUEST)


class UserRequestsCryptoFundApiView(APIView):
  permission_classes = (permissions.IsAuthenticated,)

  def get(self, request):
    already_exists = models.ETHAccounts.objects.filter(user=request.user, deleted_at=None).first()
    if already_exists:
      return Response("You've already recieved fund!", status=status.HTTP_400_BAD_REQUEST)
    funded = services.user_requests_crypto_fund(request.user)
    if funded:
      return Response("The fund has been added to your account.", status=status.HTTP_201_CREATED)
    return Response("There is not available resource at the moment. Please try again later or Contanct support.", status=status.HTTP_406_NOT_ACCEPTABLE)


class UserDepositsFiatApiView(APIView):
  permission_classes = (permissions.IsAuthenticated,)

  def post(self, request):
    serializer = serializers.UserDepositFiatSerializer(data=request.data)
    if serializer.is_valid():
      deposited = services.user_deposits_fiat(request.user, serializer.validated_data.get('amount'))
      if deposited:
        return Response("Deposit Successful.", status=status.HTTP_201_CREATED)
      return Response("Error processing deposit request!", status=status.HTTP_400_BAD_REQUEST)
    else:
      return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class GatherETHAccounts(APIView):
  permission_classes = (permissions.IsAdminUser,)

  def get(self, request):
    done = utils.gather_eth_accounts_from_ganache()
    if done:
      return Response("Done.", status=status.HTTP_201_CREATED)
    return Response("Error gathering eth accounts!", status=status.HTTP_500_INTERNAL_SERVER_ERROR)


