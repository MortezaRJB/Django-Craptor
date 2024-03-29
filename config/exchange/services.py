from .models import Order, Limit, OrderBook, Match
from django.http import HttpResponse
from rest_framework import status
from decimal import Decimal, InvalidOperation
import uuid


def fill_order(existing_order: Order, new_order: Order):
  size_filled = Decimal('0')
  if existing_order.is_Bid:
    bid = existing_order
    ask = new_order
  else:
    bid = new_order
    ask = existing_order

  if existing_order.size_remained >= new_order.size_remained:
      existing_order.size_remained -= new_order.size_remained
      size_filled = new_order.size_remained
      new_order.size_remained = Decimal('0')
  else:
    new_order.size_remained -= existing_order.size_remained
    size_filled = existing_order.size_remained
    existing_order.size_remained = Decimal('0')

  mach = Match()
  mach.bid, mach.ask, mach.size_filled, mach.price = bid, ask, size_filled, existing_order.price
  return mach


def fill(limit: Limit, order: Order):
  matches = []
  listof_orders_to_delete = []
  limit_orders = list(Order.objects.filter(is_limit=True, limit=limit, status__in=[Order.OrderStatusChoices.ACTIVE_NOT_FILLED, Order.OrderStatusChoices.ACTIVE_PARTIALLY_FILLED]))
  for i in range(len(limit_orders)):
    o = limit_orders[i]
    matched = fill_order(o, order)
    limit_orders[i] = o
    # postpone order.save()
    matches.append(matched)
    limit.total_volume -= matched.size_filled
    if limit_orders[i].is_filled:
      limit_orders[i].status = Order.OrderStatusChoices.FILLED
      o.save()
    elif limit_orders[i].size_remained != limit_orders[i].size:
      limit_orders[i].status = Order.OrderStatusChoices.ACTIVE_PARTIALLY_FILLED
      o.save()
    else:
      o.save()
    if order.is_filled:
      order.status = Order.OrderStatusChoices.FILLED
      order.save()
      break
    else: 
      order.save()
  
  return matches

def place_order(order: Order, orderbook: OrderBook):
  # TODO: fix mutex
  if order.is_limit:
    limit, created = Limit.objects.get_or_create(orderbook=orderbook, price=order.price, is_bid=order.is_Bid)
    try:
      order.limit = limit
      order.status = Order.OrderStatusChoices.ACTIVE_NOT_FILLED
      limit.total_volume += order.size
      limit.save()
      order.save()
    except InvalidOperation:
      order.status = Order.OrderStatusChoices.REJECTED
      order.save()
      return HttpResponse(status.HTTP_422_UNPROCESSABLE_ENTITY, 'The Order Size Exceeds The Limit!')
    return HttpResponse(status.HTTP_200_OK, 'The Limit Order Was Placed Successfully.')
  else:
    matches = []
    limits_to_delete = []
    total_vol = Decimal('0')
    limits = list(Limit.objects.filter(orderbook=orderbook, is_bid= not order.is_Bid))
    # Reverse list if order.is_Ask
    if order.is_Bid == False: limits.reverse()
    for l in limits: total_vol += l.total_volume
    if order.size > total_vol:
      order.status = Order.OrderStatusChoices.REJECTED
      order.save()
      return HttpResponse(status.HTTP_422_UNPROCESSABLE_ENTITY, 'The Order Size Exceeds The Limit!')
    else:
      for i in range(len(limits)):
        lim = limits[i]
        there_were_matches = fill(lim, order)
        lim.save()
        limits[i] = lim
        matches.extend(there_were_matches)
        if limits[i].total_volume == Decimal('0'): limits_to_delete.append(limits[i])
      # TODO: fix bulk create for matches
      for m in matches:
        m.save()
      # TODO: fix bulk delete
      for l in limits_to_delete:
        l.delete()
      return HttpResponse(status.HTTP_200_OK, 'The Market Order Was Placed Successfully.')


