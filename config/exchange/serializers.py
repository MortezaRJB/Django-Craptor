from rest_framework import serializers
from rest_framework import status
from . import models
from . import services
from django.utils.translation import gettext_lazy as _


class OrderSerializer(serializers.ModelSerializer):
  class Meta:
    model = models.Order
    fields = ['id', 'size', 'is_Bid', 'price', 'is_limit', 'timestamp']
    read_only_fields = ['timestamp']
  
  def validate(self, attrs):
    if attrs.get('is_limit') and not attrs.get('price'):
      raise serializers.ValidationError({"price": _("The Limit Order Requires a 'Price' Value To Be Placed!")})
    elif attrs.get('price') and not attrs.get('is_limit'):
      raise serializers.ValidationError({"price": _("No 'Price' Value Is Accepted For The Market Order!")})
    return super().validate(attrs)
  
  def create(self, validated_data):
    validated_data['size_remained'] = validated_data.get('size')
    validated_data['status'] = models.Order.OrderStatusChoices.PROCESSING
    order = super().create(validated_data)
    orderbook = models.OrderBook.objects.first()
    placing_response = services.place_order(order, orderbook)
    if placing_response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY:
      order.status = models.Order.OrderStatusChoices.REJECTED
      order.save()
      raise serializers.ValidationError(status.HTTP_422_UNPROCESSABLE_ENTITY, 'The Order Size Exceeds The Limit!')
    return order


