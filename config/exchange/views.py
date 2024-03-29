from django.shortcuts import render
from rest_framework.generics import CreateAPIView, ListAPIView, DestroyAPIView, RetrieveAPIView
from . import models
from . import serializers
from rest_framework import permissions, status
from rest_framework.response import Response
from django.shortcuts import get_object_or_404


class OrderCreateAndPlaceApiView(CreateAPIView):
  queryset = models.Order.objects.all()
  serializer_class = serializers.OrderSerializer
  # permission_classes = (permissions.IsAuthenticated,)


class OrderCancelApiView(DestroyAPIView):
  queryset = models.Order.objects.all()
  # permission_classes = (permissions.IsAuthenticated,)

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


