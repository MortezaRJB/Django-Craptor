from rest_framework import serializers
from rest_framework import status
from django.db.models import UUIDField
from . import models
from . import services
from django.shortcuts import get_object_or_404
from django.utils.translation import gettext_lazy as _


class OrderSerializer(serializers.ModelSerializer):
  orderbook = serializers.PrimaryKeyRelatedField(
    queryset=models.OrderBook.objects.all()
  )

  class Meta:
    model = models.Order
    fields = ['id', 'orderbook', 'size', 'is_Bid', 'price', 'is_limit', 'status', 'timestamp']
    read_only_fields = ['status', 'timestamp']
  
  def validate(self, attrs):
    if attrs.get('is_limit') and not attrs.get('price'):
      raise serializers.ValidationError({"price": _("The Limit Order Requires a 'Price' Value To Be Placed!")})
    elif attrs.get('price') and not attrs.get('is_limit'):
      raise serializers.ValidationError({"price": _("No 'Price' Value Is Accepted For The Market Order!")})
    return super().validate(attrs)
  
  def create(self, validated_data):
    # order = super().create(validated_data)
    orderbook = validated_data.get('orderbook', None)
    if orderbook is None:
      raise serializers.ValidationError({"orderbook": _("Orderbook is required!")})
    order = models.Order.objects.create(
      orderbook=orderbook,
      size=validated_data.get('size'),
      is_Bid=validated_data.get('is_Bid'),
      price=validated_data.get('price'),
      is_limit=validated_data.get('is_limit'),
      size_remained=validated_data.get('size'),
      status=models.Order.OrderStatusChoices.PROCESSING
    )
    orderbook = order.orderbook
    placing_response = services.place_order(order, orderbook)
    if placing_response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY:
      order.status = models.Order.OrderStatusChoices.REJECTED
      order.save()
      raise serializers.ValidationError(status.HTTP_422_UNPROCESSABLE_ENTITY, 'The Order Size Exceeds The Limit!')
    return order


class OrderBookListSerializer(serializers.ModelSerializer):
  class Meta:
    model = models.OrderBook
    fields = ['id', 'currency_1', 'currency_2']


class LimitSerializer(serializers.ModelSerializer):
  class Meta:
    model = models.Limit
    fields = ['is_bid', 'price', 'total_volume']


class OrderBookDetailSerializer(serializers.ModelSerializer):
  limits = LimitSerializer(many=True, read_only=True)
  
  class Meta:
    model = models.OrderBook
    fields = ['id', 'currency_1', 'currency_2', 'limits']
